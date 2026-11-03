from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_library_header_and_scroll_region_are_separate():
    source=(ROOT/'web_html/admin/map_editor.html').read_text()
    start=source.index('<dialog id="room-library-dialog"')
    dialog=source[start:source.index('</dialog>',start)]
    header=dialog[dialog.index('<header'):dialog.index('</header>')]
    for identity in ['room-library-title','room-library-close','room-library-refresh','room-library-status']:
        assert 'id="'+identity+'"' in header
    assert dialog.index('id="room-library-list"')>dialog.index('</header>')
    assert 'tabindex="0"' in dialog
    css=(ROOT/'static/css/admin.css').read_text()
    assert '#room-library-dialog[open] { display: flex;' in css
    assert 'min-height: 0; overflow-y: auto;' in css
    assert 'max-height: 85dvh' in css
