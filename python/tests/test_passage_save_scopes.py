"""Validate additive save identity and independent service scopes without FastAPI."""
import ast
import asyncio
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_map_transitions import scene,draft
from test_fog import engine
from looking_glass.services import map_transitions as service

@pytest.mark.parametrize("updating",[False,True])
def test_save_response_identifies_endpoint_and_notifies_after_commit(updating):
    path=Path(__file__).parents[1]/"looking_glass/web/admin/map_transitions.py"
    fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=="save_endpoint")
    fn.decorator_list=[]
    entered=[];calls=[]
    @contextmanager
    def connect():
        entered.append(True)
        try:yield SimpleNamespace(execute=lambda *a:None)
        finally:entered.pop()
    async def changed(*args):assert not entered;calls.append(args)
    ns=dict(campaign_for_manage=lambda *a:None,service=SimpleNamespace(save=lambda *a:{"id":"saved-id"}),
        listing=lambda *a:{"endpoints":[{"id":"saved-id"}]},notify=SimpleNamespace(campaign_changed=changed),BadRequest=ValueError)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),"exec"),ns)
    body=SimpleNamespace(map_id=1,revision=2 if updating else None,return_link=False,model_dump=lambda:{})
    result=asyncio.run(ns["save_endpoint"](SimpleNamespace(db=SimpleNamespace(connect=connect)),{},1,body,"saved-id" if updating else None))
    assert result["saved_endpoint_id"]=="saved-id" and len(calls)==1


def test_configuration_and_session_mutations_keep_other_scope(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        saved=service.runtime(c,1,a["id"],a["revision"],"discovered","blocked")
        saved=service.save(c,1,1,draft(name="New name",destination_id=b["id"]),a["id"],saved["revision"])
        assert saved["runtime_visibility"]=="discovered" and saved["runtime_availability"]=="blocked"
        saved=service.runtime(c,1,a["id"],saved["revision"],"secret",None)
        assert saved["name"]=="New name" and saved["destination_id"]==b["id"]
