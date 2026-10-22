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
