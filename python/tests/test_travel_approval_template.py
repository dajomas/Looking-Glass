from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).parents[2]

class Tags(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids={};self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if "id" in attrs:self.ids[attrs["id"]]=(tag,attrs)


def test_approval_help_is_accessible_and_initially_hidden():
    text=(ROOT/"templates/partials/_map_transitions.html").read_text()
    tags=Tags(text).ids
    assert "hidden" in tags["tr-approval-control"][1]
    assert tags["tr-approve"][1]["aria-describedby"]=="tr-approval-help"
    assert "tr-approval-label" in tags and "tr-approval-help" in tags
    assert "overrides any secret/blocked/approval requirement" not in text
