from pathlib import Path
from types import SimpleNamespace
import pytest
jinja2=pytest.importorskip("jinja2")
ROOT=Path(__file__).resolve().parents[2]


def test_preview_template_escaping_and_fields():
    env=jinja2.Environment(loader=jinja2.ChoiceLoader([jinja2.FileSystemLoader(ROOT/"web_html"),jinja2.FileSystemLoader(ROOT/"templates")]),autoescape=True)
    env.globals.update(app_title="Looking Glass")
    report={"name":"<script>bad</script>","description":"<script>secret</script>","schema":16,"current_schema":16,
            "maps":[{"name":"<script>map</script>","width":20,"height":30}],"counts":{"maps":1},"compressed_bytes":100,"expanded_bytes":200}
    html=env.get_template("admin/backup_inspect.html").render(campaign={"id":1,"name":"Target"},report=report,preview='a"b',csrf_token="csrf",user=None)
    assert '<script>bad</script>' not in html and '&lt;script&gt;bad&lt;/script&gt;' in html
    assert 'name="preview" value="a&#34;b"' in html
    assert 'action="/campaigns/1/restore"' in html and 'name="csrf_token"' in html
    assert 'Same backup ZIP' in html and '15 minutes' in html


def test_campaign_uses_inspect_not_direct_restore():
    html=(ROOT/"web_html/admin/campaign.html").read_text()
    assert 'action="/campaigns/{{ campaign.id }}/restore/inspect"' in html
    assert 'action="/campaigns/{{ campaign.id }}/restore"' not in html
    assert 'recovery_files' in html
