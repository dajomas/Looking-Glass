from html.parser import HTMLParser
from pathlib import Path


def test_import_picker_belongs_to_edit_form_only():
    path=Path(__file__).resolve().parents[2]/"web_html/admin/map_editor.html"
    class Inspector(HTMLParser):
        def __init__(self):
            super().__init__();self.stack=[];self.parents={}
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if attrs.get("id") in ("room-import-choice","room-import-select"):
                self.parents[attrs["id"]]=list(self.stack)
            if tag not in ("input","img","link","meta","br","hr"):
                self.stack.append((tag,attrs.get("id")))
        def handle_endtag(self,tag):
            for i in range(len(self.stack)-1,-1,-1):
                if self.stack[i][0]==tag:
                    del self.stack[i:];break
    parser=Inspector();parser.feed(path.read_text())
    assert set(parser.parents)=={"room-import-choice","room-import-select"}
    for parents in parser.parents.values():
        assert ("form","room-form") in parents
        assert ("div","room-read") not in parents
