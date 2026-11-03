from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from looking_glass.rbac import Role

def test_readiness_templates_escape_and_no_editor_boot():
    root=Path(__file__).resolve().parents[2]
    env=Environment(loader=FileSystemLoader([root/'web_html',root/'templates']),autoescape=select_autoescape(['html']))
    env.globals.update(Role=Role,app_title='Looking Glass')
    common=dict(campaign={'id':1,'name':'Campaign'},user={'role':'admin','username':'dm','display_name':'DM'},entry='admin',csrf_token='test')
    report={'map_count':1,'counts':{'error':1,'warning':0,'info':0},'generated_at':'now','findings':[{'severity':'error','map_name':'<script>','message':'<secret>','map_id':1,'url':'/campaigns/1/readiness/maps/1','code':'image_unreadable'}],'expanded_bytes':50,'size_complete':True,'upload_limit':100}
    html=env.get_template('admin/campaign_readiness.html').render(**common,report=report)
    assert '&lt;secret&gt;' in html
    assert 'admin_map_editor.js' not in html
    html=env.get_template('admin/readiness_inspect.html').render(**common,map={'id':1,'name':'<script>','width':400,'height':200},marker={'x':10,'y':20,'original_x':10,'original_y':20},endpoints=[],notes=[])
    assert 'cx="10"' in html
    assert 'admin_map_editor.js' not in html
    assert '/api/maps/1/image' in html
