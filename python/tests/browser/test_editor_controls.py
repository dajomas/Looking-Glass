from browser_support import template_environment, fulfill_auxiliary
"""Chromium tests of actual editor/viewer scripts and rendered editor markup."""
import base64
import io
import json
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
from jinja2 import Environment,DictLoader
pw=pytest.importorskip('playwright.sync_api')
ROOT=Path(__file__).resolve().parents[3]


def png(mode='RGB',color=(200,30,30),size=(400,200)):
    b=io.BytesIO();Image.new(mode,size,color).save(b,'PNG');return b.getvalue()




@pytest.fixture
def page(browser):
    p=browser.new_page(viewport={'width':1200,'height':800});yield p;p.close()


def editor(page,fail=False):
    data={'ok':True,'id':1,'name':'M','campaign_id':4,'cache_token':'token','image_version':'map1',
          'width':400,'height':200,'work_width':400,'work_height':200,'walls_version':1,'fog_version':1,
          'walls_source':'src','calibration':{'offset_x':0,'offset_y':0,'scale_x':1,'scale_y':1,'doors_block':True},
          'walls':[[0,0,0,200,'wall',True],[200,0,200,200,'door',True]],'op_count':0,
          'is_active':False,'live_viewers':0,'disabled_wall_types':[]}
    state={'fail':fail,'data':data,'posts':[],'errors':[]}
    templates={'base.html':"""<!doctype html><meta name="csrf-token" content="token"><style>html,body{margin:0}main.editor{display:grid;grid-template-columns:320px 1fr;height:800px}.sidebar{overflow:auto}.viewport{position:relative;overflow:hidden}.stage{position:absolute;transform-origin:0 0}.stage>img,.stage>canvas,.stage>svg{position:absolute;width:100%;height:100%}.stage img{z-index:0}#fog-canvas{z-index:1}#walls-svg{z-index:2}</style>{% block styles %}{% endblock %}<main class="editor">{% block content %}{% endblock %}</main>{% block scripts %}{% endblock %}""",
     'admin/map_editor.html':(ROOT/'web_html/admin/map_editor.html').read_text(),
     'partials/_csrf.html':'<input name="csrf_token" value="token" type="hidden">',
     'partials/_map_display_dialog.html':'<dialog id="map-display-dialog"><p id="map-display-question"></p></dialog>'}
    templates["partials/_double_reveal.html"]=(ROOT/"templates/partials/_double_reveal.html").read_text()
    html=template_environment(templates).get_template('admin/map_editor.html').render(
        map=dict(data,wall_count=2),campaign={'id':4,'name':'C'},siblings=[{'id':1,'name':'M'}],op_count=0,fog_opacity=.55)
    page.on('pageerror',lambda e:state['errors'].append(str(e)))
    page.on('dialog',lambda d:d.dismiss())
    def route(r):
        if fulfill_auxiliary(r, data): return
        req=r.request;path=urlparse(req.url).path
        if path=='/maps/1':r.fulfill(content_type='text/html',body=html);return
        if path.startswith('/static/'):
            p=ROOT/path.lstrip('/')
            if p.exists():r.fulfill(content_type='application/javascript' if p.suffix=='.js' else 'text/css',body=p.read_text())
            else:r.fulfill(content_type='application/javascript',body='')
            return
        if path=='/api/maps/1/image':r.fulfill(content_type='image/png',body=png());return
        if path=='/api/maps/1/fog.png':r.fulfill(content_type='image/png',body=png('RGBA',(255,255,255,0)));return
        if path=='/api/campaigns/4/wall-sources':r.fulfill(json={'sources':[]});return
        if path=='/api/maps/1':
            r.fulfill(status=500,json={'ok':False,'error':'Temporary state failure'}) if state['fail'] else r.fulfill(json=data)
            return
        if req.method=='POST':
            state['posts'].append((path,req.post_data_json))
            if path.endswith('wall-types'):data['disabled_wall_types']=req.post_data_json['disabled_wall_types'];data['walls_version']+=1
            r.fulfill(json=dict(data,area_fraction=.2,leak_warning=False));return
        raise AssertionError(path)
    page.route('**/*',route);page.goto('http://looking-glass.test/maps/1')
    page.wait_for_function("document.getElementById('map-img').naturalWidth===400")
    return state


def test_editor_displays_map_and_walls_on_open(page):
    state=editor(page)
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    assert page.locator('#stage').bounding_box()['width']>0
    assert not state['errors']


def test_image_loads_even_if_metadata_fails_and_retry_recovers(page):
    state=editor(page,True)
    pw.expect(page.locator('#map-load-error')).to_contain_text('Temporary state failure')
    assert page.locator('#map-img').evaluate('el=>el.naturalWidth')==400
    state['fail']=False;page.click('#retry-map-load')
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    pw.expect(page.locator('#map-load-error')).to_be_hidden()


def test_show_hide_and_enable_disable_are_independent(page):
    state=editor(page)
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    page.uncheck('[data-wall-show="wall"]')
    assert page.locator('#walls-svg .w-wall').count()==0
    assert state['posts']==[]
    page.uncheck('[data-wall-enabled="door"]');page.click('#apply-wall-types')
    page.wait_for_function("document.getElementById('wall-count').textContent==='2'")
    pw.expect(page.locator('#walls-svg .w-passive')).to_have_count(1)
    assert state['posts'][-1][1]=={'disabled_wall_types':['door']}


def test_reveal_offline_displays_warning_without_publishing(page):
    state=editor(page)
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    page.locator('#viewport').click(position={'x':200,'y':300})
    pw.expect(page.locator('#toast')).to_contain_text('NOT shown to players')
    assert not any('active' in path for path,body in state['posts'])


def test_selection_restored_after_option_reload_and_page_reload(page):
    html="""<!doctype html><select id="saved-source"><option value="">Choose</option><option value="7">Database</option></select><select id="saved-scene"><option value="">Choose</option><option value="3">Tower</option></select><script src="/static/js/keep_select_values.js"></script>"""
    def route(r):
        if urlparse(r.request.url).path.startswith('/static/'):
            r.fulfill(content_type='application/javascript',body=(ROOT/'static/js/keep_select_values.js').read_text())
        else:r.fulfill(content_type='text/html',body=html)
    page.route('**/*',route);page.goto('http://looking-glass.test/maps/1')
    page.select_option('#saved-source','7');page.select_option('#saved-scene','3')
    page.evaluate("const s=document.getElementById('saved-scene');s.value='';s.disabled=true;s.disabled=false")
    pw.expect(page.locator('#saved-scene')).to_have_value('3')
    page.reload();pw.expect(page.locator('#saved-source')).to_have_value('7');pw.expect(page.locator('#saved-scene')).to_have_value('3')


def test_viewer_centers_revealed_bounds(page):
    image='data:image/png;base64,'+base64.b64encode(png()).decode()
    page.set_content('<div id="viewport" style="width:800px;height:500px;position:relative"><div id="stage" style="transform-origin:0 0"><img id="map"></div></div><div id="waiting"><span id="waiting-text"></span></div><i id="conn-dot"></i><span id="map-name"></span><button id="btn-fit"></button><button id="btn-full"></button><div id="hud"></div>')
    page.evaluate("""image=>{window.LG_CAMPAIGN=4;window.fetch=async()=>({ok:true,json:async()=>({map:{name:'M',width:400,height:200,version:'1-1',image_url:image,revealed_bounds:{x:280,y:80,width:100,height:100}}})});window.WebSocket=class{};}""",image)
    page.add_script_tag(path=str(ROOT/'static/js/pan_zoom.js'));page.add_script_tag(path=str(ROOT/'static/js/viewer_area_zoom.js'));page.add_script_tag(path=str(ROOT/'static/js/viewer_display.js'))
    page.wait_for_function("document.getElementById('map').naturalWidth===400")
    center=page.locator('#stage').evaluate("el=>{const m=new DOMMatrix(getComputedStyle(el).transform);return {x:m.a*330+m.e,y:m.d*130+m.f};}")
    assert center['x']==pytest.approx(400,abs=1)
    assert center['y']==pytest.approx(250,abs=1)


def test_collapsible_battle_sidebar_panels(page):
    state = editor(page)
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    for panel, control in (("players-panel", "btn-show"), ("fog-panel", "fog-opacity"), ("wall-legend", "apply-wall-types"), ("walls-panel", "wall-width")):
        details = page.locator(f"#{panel}")
        summary = page.locator(f"#{panel} > summary")
        if not details.evaluate("el => el.open"):
            summary.click()
        pw.expect(page.locator(f"#{control}")).to_be_visible()
        summary.click()
        pw.expect(page.locator(f"#{control}")).to_be_hidden()
        summary.click()
        pw.expect(page.locator(f"#{control}")).to_be_visible()
    assert not state['posts'] and not state['errors']


def test_wall_width_is_screen_constant_and_survives_reload(page):
    state = editor(page)
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    page.locator('#wall-width').evaluate("el => { el.value = '4'; el.dispatchEvent(new Event('input', {bubbles:true})); }")
    def screen_width():
        return page.locator('#walls-svg .w-wall').evaluate("el => parseFloat(getComputedStyle(el).strokeWidth) * el.getScreenCTM().a")
    assert screen_width() == pytest.approx(4, abs=.01)
    page.click('#zoom-in')
    assert screen_width() == pytest.approx(4, abs=.01)
    assert not state['posts'] and not state['errors']
    page.reload()
    pw.expect(page.locator('#walls-svg path')).to_have_count(2)
    assert page.locator('#wall-width').input_value() == '4'
    assert screen_width() == pytest.approx(4, abs=.01)
