"""Real Chromium, mocked API. No production server is modified."""
import json
from pathlib import Path

import pytest
pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def browser():
    with pw.sync_playwright() as p:
        b=p.chromium.launch(headless=True,args=["--no-sandbox"])
        yield b
        b.close()


@pytest.fixture
def page(browser):
    p=browser.new_page();yield p;p.close()


def prompt(page, available):
    page.set_content('<dialog id="map-display-dialog"><p id="map-display-question"></p><button id="restore">Restore</button></dialog>')
    page.evaluate("""available=>{
      window.calls=[]; window.available=available; window.LG_MAP={id:1};
      window.fetch=async(url,options)=>{calls.push({url,options});return {ok:true,json:async()=>({ok:true,can_restore:window.available})};};
      document.getElementById('restore').onclick=()=>{const d=document.getElementById('map-display-dialog');d.returnValue='restore';d.close();};
    }""",available)
    page.add_script_tag(path=str(ROOT/'static/js/map_display_prompt.js'))


def test_no_reveals_resets_without_prompt_and_rechecks_next_selection(page):
    prompt(page,False)
    assert page.evaluate("window.LGChooseFog('One',1)")=='reset'
    assert not page.locator('dialog').evaluate('d=>d.open')
    assert page.evaluate("window.LGChooseFog('Two',2)")=='reset'
    assert page.evaluate('window.calls.map(c=>c.url)')==['/api/maps/1/display-options','/api/maps/2/display-options']
    assert page.evaluate("window.calls.every(c=>c.options.cache==='no-store')")


def test_reveals_prompt_and_then_reset_after_new_empty_check(page):
    prompt(page,True)
    page.evaluate("window.answer=null; void window.LGChooseFog('One',1).then(v=>window.answer=v)")
    pw.expect(page.locator('dialog')).to_be_visible()
    page.click('#restore')
    page.wait_for_function("window.answer==='restore'")
    page.evaluate('window.available=false')
    assert page.evaluate("window.LGChooseFog('One',1)")=='reset'
    assert page.evaluate('window.calls.length')==2


def test_checkpoint_error_does_not_reset_or_display(page):
    prompt(page,False)
    page.evaluate("window.fetch=async()=>({ok:false})")
    error=page.evaluate("window.LGChooseFog('One',1).catch(e=>e.message)")
    assert 'No map was displayed' in error


def test_source_apply_has_no_confirmation_and_preserves_index(page):
    page.set_content('<details id="saved-wall-library" open><form id="source-save"><input id="source-file" type="file"></form>\n<select id="saved-source"></select><select id="saved-scene"></select><p id="saved-scene-info"></p><p id="source-status"></p>\n<button id="source-apply">Apply</button><button id="source-delete">Delete</button><button id="source-refresh">Refresh</button>\n<input id="saved-auto-align" type="checkbox" checked></details>')
    page.evaluate("""()=>{window.LG_MAP={id:1,campaign_id:4};window.submitted=null;
      window.confirm=()=>{throw new Error('Unexpected Apply confirmation');};
      window.LGApi={get:async url=>url.endsWith('/wall-sources')?{sources:[{id:7,filename:'maps.db',scene_count:1}]}:
       {scenes:[{index:8,name:'Tower',walls:10,doors:1,calibration:{offset_x:0,offset_y:0,scale_x:1,scale_y:1}}]},
       post:async(url,body)=>{window.submitted=body;return new Promise(()=>{});}};
    }""")
    page.add_script_tag(path=str(ROOT/'static/js/wall_source_library.js'))
    pw.expect(page.locator('#saved-source')).to_be_enabled();page.select_option('#saved-source','7')
    pw.expect(page.locator('#saved-scene')).to_be_enabled();page.select_option('#saved-scene','8')
    page.click('#source-apply'); assert page.evaluate('window.submitted.scene_index')==8


def batch(page):
    page.set_content('<meta name="csrf-token" content="token"><section id="campaign-batch-import" data-campaign-id="4">\n<form id="batch-upload"><input id="batch-map-files" type="file" multiple><input id="batch-wall-files" type="file" multiple><button>Import</button></form>\n<ul id="batch-import-results"></ul><p id="batch-status"></p><table><tbody id="batch-assignment-rows"></tbody></table>\n<button id="batch-apply-walls">Apply</button><button id="batch-refresh-sources">Refresh</button>\n<script id="batch-existing-maps" type="application/json">[{"id":1,"name":"Map"}]</script></section>')
    page.clock.install()
    page.evaluate("""()=>{
      window.confirms=0;window.applied=null;window.pendingUploads=[];
      window.confirm=()=>{window.confirms++;return false;};
      window.LGApi={get:async url=>url.endsWith('/wall-sources')?{sources:[{id:7,filename:'db',scene_count:1}]}:
        {scenes:[{index:2,name:'Room',walls:5}]},post:async(url,body)=>{
         if(url.endsWith('from-source')){window.applied=body;return {imported:5,scene:'Room'};}
         return await new Promise(resolve=>window.pendingUploads.push(resolve));
       }};
    }""")
    page.add_script_tag(path=str(ROOT/'static/js/campaign_batch_import.js'))
    pw.expect(page.locator('#batch-assignment-rows select').nth(0)).to_be_enabled()


def test_batch_one_progress_line_total_and_exact_four_second_clear(page):
    batch(page)
    page.set_input_files('#batch-wall-files',[{'name':'first.uvtt','mimeType':'text/plain','buffer':b'x'},
                                             {'name':'second.db','mimeType':'text/plain','buffer':b'y'}])
    page.click('#batch-upload button')
    pw.expect(page.locator('#batch-status')).to_contain_text('1/2: first.uvtt')
    assert page.locator('#batch-import-results').count()==0
    page.evaluate('window.pendingUploads.shift()({source:{id:8}})')
    pw.expect(page.locator('#batch-status')).to_contain_text('2/2: second.db')
    assert 'first.uvtt' not in page.locator('#batch-status').inner_text()
    page.evaluate('window.pendingUploads.shift()({source:{id:9}})')
    pw.expect(page.locator('#batch-status')).to_contain_text('0 maps, 2 wall sources imported; 0 failed')
    page.clock.fast_forward(3999)
    assert page.locator('#batch-status').inner_text()
    page.clock.fast_forward(1)
    assert page.locator('#batch-status').inner_text()==''


def test_batch_apply_does_not_confirm(page):
    batch(page)
    source=page.locator('#batch-assignment-rows select').nth(0)
    scene=page.locator('#batch-assignment-rows select').nth(1)
    source.select_option('7');pw.expect(scene).to_be_enabled();scene.select_option('2')
    page.click('#batch-apply-walls')
    pw.expect(page.locator('#batch-status')).to_contain_text('1 applied, 0 failed')
    assert page.evaluate('window.confirms')==0
    assert page.evaluate('window.applied.scene_index')==2


def test_removed_one_off_section_has_no_dangling_editor_handlers():
    template=(ROOT/'web_html/admin/map_editor.html').read_text()
    script=(ROOT/'static/js/admin_map_editor.js').read_text()
    assert 'id="wall-legend"' in template
    for name in ['Normal wall','Secret door','Window / terrain','Invisible wall','Ethereal / passive']:
        assert name in template
    for ident in ['wall-import','wall-file','btn-clear-walls','scene-select']:
        assert f'id="{ident}"' not in template
        assert f'$("{ident}")' not in script
    assert 'setActive(target)' in script
