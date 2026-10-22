from pathlib import Path
from types import SimpleNamespace
import re
from jinja2 import Environment,ChoiceLoader,FileSystemLoader
ROOT=Path(__file__).parents[2]

def test_editor_transition_template():
    env=Environment(loader=ChoiceLoader([FileSystemLoader(ROOT/"web_html"),FileSystemLoader(ROOT/"templates")]))
    env.globals.update(app_title="Looking Glass",Role=SimpleNamespace(SUPERADMIN="superadmin"))
    m=dict(id=1,name="M",campaign_id=2,wall_count=0,walls_source="")
    html=env.get_template("admin/map_editor.html").render(map=m,campaign=dict(id=2,name="C"),siblings=[m],fog_opacity=.5,op_count=0,user=None)
    ids=re.findall(r'\bid="([^"{}]+)"',html);assert len(ids)==len(set(ids))
    for name in ("transition-form","transition-markers","transition-travel-form","transition-add"):assert f'id="{name}"' in html
    assert html.index("map_transitions.js")<html.index("admin_map_editor.js")


def test_passage_footer_is_outside_scroll_body():
    from test_sidebar_appearance import Structure
    page=Structure((ROOT/"templates/partials/_map_transitions.html").read_text())
    for ident in ("tr-delete","tr-save-runtime","tr-open","tr-travel","tr-close"):
        ancestry=page.nodes[ident][2]
        assert any(tag=="footer" for tag,_ in ancestry)
        assert not any(tag=="fieldset" for tag,_ in ancestry)
    text=(ROOT/"static/css/admin.css").read_text()
    assert "#transition-editor .transition-body" in text and "#transition-editor .transition-actions" in text
