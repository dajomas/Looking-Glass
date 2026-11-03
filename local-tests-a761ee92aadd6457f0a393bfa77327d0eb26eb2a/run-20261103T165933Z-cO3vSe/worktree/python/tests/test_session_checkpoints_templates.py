from pathlib import Path
from jinja2 import Environment,FileSystemLoader,select_autoescape
from looking_glass.rbac import Role


def test_checkpoint_templates_escape_and_block_restore():
    root=Path(__file__).resolve().parents[2]
    env=Environment(loader=FileSystemLoader([root/'web_html',root/'templates']),autoescape=select_autoescape(['html']))
    env.globals.update(Role=Role,app_title='Looking Glass')
    common=dict(campaign={'id':1,'name':'Adventure'},entry='admin',user={'role':'admin','username':'dm','display_name':'DM'},csrf_token='csrf')
    checkpoint=dict(id=1,name='<script>',notes='<secret>',created_at='now',automatic=False)
    html=env.get_template('admin/session_checkpoints.html').render(**common,checkpoints=[checkpoint],page=1,has_more=False)
    assert '&lt;script&gt;' in html and '&lt;secret&gt;' in html
    assert 'Session checkpoints' in html
    view=dict(conflicts=[],token='a'*64,current=dict(active_map_id=None,maps=[]),target=dict(active_map_id=None,maps=[]))
    html=env.get_template('admin/session_checkpoint_preview.html').render(**common,checkpoint=checkpoint,view=view,problem=None)
    assert 'name="token"' in html and 'name="csrf_token"' in html
    assert 'Save safety checkpoint and restore' in html
    view['conflicts']=['Map <changed>']
    html=env.get_template('admin/session_checkpoint_preview.html').render(**common,checkpoint=checkpoint,view=view,problem=None)
    assert 'Map &lt;changed&gt;' in html and 'name="token"' not in html
    assert 'Delete checkpoint' in html
