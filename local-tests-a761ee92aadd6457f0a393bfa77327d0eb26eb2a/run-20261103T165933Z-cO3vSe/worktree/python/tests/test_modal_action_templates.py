from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).parents[2]

class Buttons(HTMLParser):
    def __init__(self,text):
        super().__init__();self.buttons=[];self.current=None;self.feed(text)
    def handle_starttag(self,tag,attrs):
        if tag=="button":self.current=[dict(attrs),""]
    def handle_data(self,data):
        if self.current is not None:self.current[1]+=data
    def handle_endtag(self,tag):
        if tag=="button" and self.current is not None:self.buttons.append(self.current);self.current=None


def test_single_portal_close_and_clear_pair_reset():
    text=(ROOT/"web_html/admin/wall_editor.html").read_text()
    buttons={a.get("id"):label for a,label in Buttons(text).buttons}
    assert "portal-cancel" not in buttons
    assert buttons["portal-close"]=="Close"
    assert buttons["portal-remove"]=="Reset pairing…"
    assert buttons["portal-apply"]=="Apply configuration to draft"


def test_display_labels_preserve_action_values_and_explain_reset_scope():
    text=(ROOT/"templates/partials/_map_display_dialog.html").read_text()
    values={a.get("value"):label for a,label in Buttons(text).buttons}
    assert values==dict(restore="Restore saved reveals",reset="Reset fog and show map",cancel="Cancel")
    assert "cannot be undone" in text and "Cross-map endpoint session overrides" in text
    assert "wall-door locks" in text and "wall-passage discovery" in text


def test_travel_labels_are_distinct_from_inspection_and_return():
    text=(ROOT/"templates/partials/_map_transitions.html").read_text()
    buttons={a.get("id"):label for a,label in Buttons(text).buttons}
    assert buttons["tr-travel"]=="Travel…" and buttons["tr-open"]=="Inspect destination"
    assert buttons["tr-cancel-travel"]=="Back to passage"
