"""Keep new-window inspection isolated from test-host DNS and real application writes."""
import ast
from pathlib import Path


def test_destination_navigation_is_mocked_on_the_context_and_cleaned_up():
    source = Path(__file__).with_name("browser").joinpath("test_passage_modal_layout.py").read_text()
    tree = ast.parse(source)
    test = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "test_inspection_does_not_activate_viewer")
    calls = [ast.unparse(node.func) for node in ast.walk(test) if isinstance(node, ast.Call)]
    assert "page.context.route" in calls
    assert "page.context.unroute" in calls
    assert "target.close" in calls
    assert any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(test))
    assert "assert not posts" in ast.get_source_segment(source, test)
