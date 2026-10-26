from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from looking_glass.rbac import Role


def test_search_escaping_and_context():
    root=Path(__file__).resolve().parents[2]
    env=Environment(loader=FileSystemLoader([root/'web_html',root/'templates']),autoescape=select_autoescape(['html']))
    env.globals.update(Role=Role,app_title='Looking Glass')
    context=dict(campaign={'id':1,'name':'Campaign'},user={'role':'admin','username':'dm','display_name':'DM'},entry='admin',csrf_token='token')
    search=dict(query='<script>',kind='all',limit=50,truncated=True,results=[dict(kind='room',title='<script>',map_name='Map',snippet='<img onerror=x>',url='/campaigns/1/inspect/maps/1')])
    html=env.get_template('admin/campaign_search.html').render(**context,search=search)
    assert '&lt;script&gt;' in html and '&lt;img onerror=x&gt;' in html
    assert 'campaign_quick_nav.js' in html and 'refine' in html.lower()
    context['entry']='viewer'
    html=env.get_template('admin/campaign_search.html').render(**context,search=search)
    assert 'campaign_quick_nav.js' not in html


def test_selected_content_is_plain_text():
    root=Path(__file__).resolve().parents[2]
    env=Environment(loader=FileSystemLoader([root/'web_html',root/'templates']),autoescape=select_autoescape(['html']))
    env.globals.update(Role=Role,app_title='Looking Glass')
    html=env.get_template('admin/readiness_inspect.html').render(campaign={'id':1,'name':'C'},map={'id':1,'name':'Map','width':400,'height':200},entry='admin',user=None,csrf_token='',marker=None,endpoints=[],notes=[],selected={'name':'A','kind':'room','markdown':'<script>alert(1)</script>'})
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert 'admin_map_editor.js' not in html
