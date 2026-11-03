"""Unit checks for the bounded diagnostic wrapper, without browser dependencies."""
import importlib.util
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("browser_check", Path(__file__).with_name("check_browser_environment.py"))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_missing_playwright_is_failure(monkeypatch):
    def missing(name):
        raise check.PackageNotFoundError(name)
    monkeypatch.setattr(check, "version", missing)
    assert check.main([]) == 1


@pytest.mark.parametrize("returncode, expected", [(0, 0), (1, 1), (-11, 1)])
def test_child_status_and_debug(monkeypatch, returncode, expected):
    monkeypatch.setattr(check, "version", lambda name: "test")
    monkeypatch.setattr(check, "font_diagnostics", lambda: None)
    def run(cmd, **kwargs):
        assert cmd[-1] == "--probe"
        assert "pw:browser" in kwargs["env"]["DEBUG"]
        assert kwargs["timeout"] == 45
        return SimpleNamespace(returncode=returncode)
    monkeypatch.setattr(check.subprocess, "run", run)
    assert check.main([]) == expected


def test_child_timeout_is_failure(monkeypatch):
    monkeypatch.setattr(check, "version", lambda name: "test")
    monkeypatch.setattr(check, "font_diagnostics", lambda: None)
    def timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
    monkeypatch.setattr(check.subprocess, "run", timeout)
    assert check.main(["--timeout", "1"]) == 1


def test_invalid_timeout():
    with pytest.raises(SystemExit) as exc:
        check.main(["--timeout", "0"])
    assert exc.value.code == 2


class FakePage:
    def __init__(self, source="Ready", rendered="Ready"):
        self.source, self.rendered = source, rendered

    def locator(self, selector):
        assert selector == "#check"
        return self

    def text_content(self):
        return self.source

    def inner_text(self):
        return self.rendered


def test_dom_content_and_rendered_text_pass():
    check.check_dom(FakePage())


@pytest.mark.parametrize("source", [None, "", "wrong"])
def test_dom_content_failure_is_not_hidden(source):
    with pytest.raises(RuntimeError, match="DOM content mismatch"):
        check.check_dom(FakePage(source=source))


@pytest.mark.parametrize("rendered", ["", "wrong"])
def test_rendered_failure_has_actionable_diagnostics(rendered):
    with pytest.raises(RuntimeError, match="fontconfig dejavu-sans-fonts"):
        check.check_dom(FakePage(rendered=rendered))


def test_missing_font_tool_is_warning(monkeypatch, capsys):
    monkeypatch.setattr(check.shutil, "which", lambda name: None)
    check.font_diagnostics()
    assert "fc-match not found" in capsys.readouterr().out


def test_font_tool_timeout_is_warning(monkeypatch, capsys):
    monkeypatch.setattr(check.shutil, "which", lambda name: "/usr/bin/fc-match")
    def timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
    monkeypatch.setattr(check.subprocess, "run", timeout)
    check.font_diagnostics()
    assert "font diagnostics unavailable" in capsys.readouterr().out
