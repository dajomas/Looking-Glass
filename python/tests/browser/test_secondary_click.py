from browser_support import template_environment, fulfill_auxiliary
"""Real Chromium pointer events against actual editor and PanZoom scripts."""
import io
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
pw=pytest.importorskip('playwright.sync_api')
ROOT=Path(__file__).resolve().parents[3]




@pytest.fixture
def page(browser):
    p=browser.new_page(viewport={'width':1000,'height':700});yield p;p.close()


def picture(rgba=False):
    b=io.BytesIO();Image.new('RGBA' if rgba else 'RGB',(400,200),(0,0,0,0) if rgba else (180,40,40)).save(b,'PNG');return b.getvalue()


def boot(page,fail_first=False):
    data={'ok':True,'id':1,'name':'Map','campaign_id':4,'cache_token':'t','image_version':'one',
          'width':400,'height':200,'work_width':400,'work_height':200,'walls_version':1,'fog_version':1,
          'walls_source':'source','calibration':{'offset_x':0,'offset_y':0,'scale_x':1,'scale_y':1,'doors_block':True},
          'walls':[[0,0,400,0,'wall',True]],'op_count':0,'is_active':True,'live_viewers':1,'disabled_wall_types':[]}
    base = '<!doctype html><meta charset="utf-8"><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>'
    html=template_environment({"base.html":base}).get_template("admin/map_editor.html").render(
        map=dict(data,wall_count=1),campaign=dict(id=4,name="C"),siblings=[dict(id=1,name="Map")],fog_opacity=.55,op_count=0)
    state={'gets':0,'posts':[],'errors':[]}
    page.on('pageerror',lambda e:state['errors'].append(str(e)))
    def route(r):
        if fulfill_auxiliary(r, data): return
        req=r.request;path=urlparse(req.url).path
        if path=='/maps/1':r.fulfill(content_type='text/html',body=html);return
        if path.startswith('/static/'):
            r.fulfill(content_type='application/javascript' if path.endswith('.js') else 'text/css',body=(ROOT/path.lstrip('/')).read_text());return
        if path=='/api/campaigns/4/wall-sources':r.fulfill(json={'sources':[]});return
        if path=='/api/maps/1/image':r.fulfill(content_type='image/png',body=picture());return
        if path=='/api/maps/1/fog.png':r.fulfill(content_type='image/png',body=picture(True));return
        if path=='/api/maps/1':
            state['gets']+=1
            if fail_first and state['gets']==1:r.fulfill(status=500,json={'ok':False,'error':'Initial state failed'})
            else:r.fulfill(json=data)
            return
        if req.method=='POST':
            state['posts'].append(path);r.fulfill(json=dict(data,area_fraction=.1,leak_warning=False));return
        raise AssertionError(path)
    page.route('**/*',route);page.goto('http://looking-glass.test/maps/1')
    page.wait_for_function("document.getElementById('map-img').naturalWidth===400")
    pw.expect(page.locator('#walls-svg path')).to_have_count(1)
    page.wait_for_timeout(150)
    pw.expect(page.locator('#busy')).to_be_hidden()
    assert state['errors'] == []
    return state


@pytest.mark.parametrize('mode,button,expected',[
    ('reveal','left','reveal'),('reveal','right','hide'),
    ('hide','left','hide'),('hide','right','reveal')])
def test_stationary_click_uses_mode_or_its_inverse(page,mode,button,expected):
    state=boot(page);page.locator('#fog-panel > summary').click();page.check(f'input[name="mode"][value="{mode}"]')
    page.locator('#viewport').click(button=button,position={'x':400,'y':200})
    page.wait_for_timeout(450)
    assert state['posts']==[f'/api/maps/1/{expected}']
    assert page.is_checked(f'input[name="mode"][value="{mode}"]')
    assert state['errors']==[]


def test_right_drag_pans_without_editing_fog(page):
    state=boot(page);vp=page.locator('#viewport').bounding_box()
    before=page.locator('#stage').evaluate('el=>el.style.transform')
    page.mouse.move(vp['x']+300,vp['y']+200);page.mouse.down(button='right')
    page.mouse.move(vp['x']+380,vp['y']+240,steps=8);page.mouse.up(button='right')
    assert page.locator('#stage').evaluate('el=>el.style.transform')!=before
    assert state['posts']==[]


def test_space_right_drag_does_not_edit_fog(page):
    state=boot(page);vp=page.locator('#viewport').bounding_box()
    page.keyboard.down('Space');page.mouse.move(vp['x']+300,vp['y']+200)
    page.mouse.down(button='right');page.mouse.move(vp['x']+350,vp['y']+200,steps=5)
    page.mouse.up(button='right');page.keyboard.up('Space')
    assert state['posts']==[]


def test_middle_click_does_not_edit_fog(page):
    state=boot(page);page.locator('#viewport').click(button='middle',position={'x':400,'y':200})
    assert state['posts']==[]


def test_startup_refresh_recovers_without_blanking_players(page):
    state=boot(page,fail_first=True)
    assert state['gets']>=2
    assert state['posts']==[]
    pw.expect(page.locator('#map-load-error')).to_be_hidden()


def test_pointer_cancel_never_edits_fog(page):
    state=boot(page)
    page.evaluate("""()=>{const vp=document.getElementById('viewport');vp.setPointerCapture=()=>{};
      vp.dispatchEvent(new PointerEvent('pointerdown',{pointerId:99,button:2,buttons:2,clientX:400,clientY:400,bubbles:true}));
      vp.dispatchEvent(new PointerEvent('pointercancel',{pointerId:99,button:2,bubbles:true}));}""")
    assert state['posts']==[]


def test_default_panzoom_does_not_emit_secondary_taps(page):
    page.set_content('<div id="vp" style="width:400px;height:200px"><div id="stage"></div></div>')
    page.add_script_tag(path=str(ROOT/'static/js/pan_zoom.js'))
    page.evaluate("window.taps=[];window.pz=new PanZoom(document.getElementById('vp'),document.getElementById('stage'),{onTap:(x,y,e)=>taps.push(e.button)})")
    page.locator('#vp').click(button='right',position={'x':100,'y':100})
    assert page.evaluate('window.taps')==[]
