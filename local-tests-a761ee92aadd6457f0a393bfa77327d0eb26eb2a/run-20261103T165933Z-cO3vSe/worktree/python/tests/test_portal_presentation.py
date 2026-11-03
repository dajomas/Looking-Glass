"""Admin presentation associations; no HTTP dependency or viewer mutation."""
from dataclasses import replace
import pytest
from test_passages import passage_scene,inputs,scene_walls
from test_fog import engine
from looking_glass.repositories import walls as walls_repo,maps as maps_repo,fog_ops
from looking_glass.services.door_arrows import arrows
from looking_glass.services.portal_presentation import visible_routes


def test_route_counterpart_is_the_actual_displayed_exit(engine,passage_scene):
    db,tmp=passage_scene
    with db.connect() as c:
        spec,segs,ops=inputs(c,tmp);geometry=arrows(engine,spec,segs,ops)
        routes=visible_routes(spec,segs,geometry)
        assert len(routes)==1
        route=routes[0]
        assert route["entry"]["side"]==1 and route["entry"]["compass"]=="W"
        assert route["exit"]["side"]==0 and route["exit"]["compass"]=="E"
        assert route["entry"]["wall_id"]!=route["exit"]["wall_id"]
        actual=next(a for a in geometry if a.exit_only)
        assert route["exit"]["polygon"]==actual.polygon
        assert route["state"]=="door"
        assert "target" not in route and not c.execute("SELECT * FROM passage_runtime_states").fetchall()


@pytest.mark.parametrize("kind",["door","locked_door","unlocked_door","secret"])
def test_visible_admin_entries_include_all_runtime_kinds(engine,passage_scene,kind):
    db,tmp=passage_scene
    with db.connect() as c:
        walls_repo.replace(c,1,scene_walls(kind));c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        spec,segs,ops=inputs(c,tmp)
        result=visible_routes(spec,segs,arrows(engine,spec,segs,ops))
        assert len(result)==1 and result[0]["state"]==kind
        assert visible_routes(replace(spec,arrow_audience="viewer"),segs,arrows(engine,spec,segs,ops))==[]


def test_shared_exit_has_one_rotation_item_per_entry(engine,passage_scene):
    db,tmp=passage_scene;segs=scene_walls()
    segs[-2].passage["sides"][0]={"role":"entry","kind":"locked_door","after":"door","exit":0}
    with db.connect() as c:
        walls_repo.replace(c,1,segs);c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        fog_ops.add(c,1,"reveal",300,100,1);maps_repo.bump_fog(c,1)
        spec,segs,ops=inputs(c,tmp);geometry=arrows(engine,spec,segs,ops)
        routes=visible_routes(spec,segs,geometry)
        assert len(routes)==2 and routes[0]["id"]!=routes[1]["id"]
        assert routes[0]["exit"]==routes[1]["exit"]
        assert visible_routes(spec,segs,[a for a in geometry if not a.exit_only])==[]
        assert visible_routes(replace(spec,door_arrows_enabled=False),segs,geometry)==[]


def test_hidden_sources_have_no_routes_and_viewer_is_unchanged(engine,passage_scene):
    db,tmp=passage_scene
    with db.connect() as c:
        spec,segs,ops=inputs(c,tmp);before=engine.viewer_image(spec,segs,ops).read_bytes()
        visible_routes(spec,segs,arrows(engine,spec,segs,ops))
        assert engine.viewer_image(spec,segs,ops).read_bytes()==before
        assert visible_routes(spec,segs,arrows(engine,spec,segs,[]))==[]


def test_both_exit_reuses_visible_double_headed_arrow(engine,passage_scene):
    db,tmp=passage_scene;segs=scene_walls()
    segs[-2].passage["sides"][1]["role"]="both"
    segs[-1].passage["sides"][0]={"role":"both","kind":"door","after":"door","exit":1}
    with db.connect() as c:
        walls_repo.replace(c,1,segs);c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        fog_ops.add(c,1,"reveal",500,100,1);maps_repo.bump_fog(c,1)
        spec,segs,ops=inputs(c,tmp);geometry=arrows(engine,spec,segs,ops)
        routes=visible_routes(spec,segs,geometry)
        assert len(routes)==2
        assert routes[0]["entry"]["polygon"]==routes[1]["exit"]["polygon"]
        assert routes[1]["entry"]["polygon"]==routes[0]["exit"]["polygon"]
