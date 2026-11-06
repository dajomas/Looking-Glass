"""Bug 24: supplied configuration structure is validated before merging."""
from collections import UserDict
import copy

import pytest
import yaml

from looking_glass import config

INVALID_ROOTS = [[], ["server"], False, True, 0, 1, "text", ""]
INVALID_SECTIONS = [None, False, 0, "", [], ["value"]]
SECTIONS = ("server", "storage", "security", "fog", "viewer", "scrying_glass")


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    for name in ("LG_CONFIG", "LG_HOST", "LG_ADMIN_PORT", "LG_VIEWER_PORT", "LG_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def load_file(root, monkeypatch, selection, value):
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(value), encoding="utf-8")
    if selection == "environment":
        monkeypatch.setenv("LG_CONFIG", str(path))
    return config.load_settings(path if selection == "argument" else None)


@pytest.mark.parametrize("selection", ["argument", "environment", "discovery"])
@pytest.mark.parametrize("value", INVALID_ROOTS)
def test_yaml_root_must_be_mapping(isolated, monkeypatch, selection, value):
    with pytest.raises(ValueError, match="configuration must be a mapping") as error:
        load_file(isolated, monkeypatch, selection, value)
    assert str(isolated / "config.yaml") in str(error.value)
    assert sorted(p.name for p in isolated.iterdir()) == ["config.yaml"]


@pytest.mark.parametrize("selection", ["argument", "environment", "discovery"])
@pytest.mark.parametrize("section", SECTIONS)
@pytest.mark.parametrize("value", INVALID_SECTIONS)
def test_yaml_section_must_be_mapping(isolated, monkeypatch, selection, section, value):
    # A later valid environment override must not conceal an invalid file section.
    monkeypatch.setenv("LG_HOST", "127.0.0.1")
    monkeypatch.setenv("LG_DATA_DIR", str(isolated / "must-not-exist"))
    with pytest.raises(ValueError, match=f"section '{section}' must be a mapping") as error:
        load_file(isolated, monkeypatch, selection, {section: value})
    assert str(isolated / "config.yaml") in str(error.value)
    assert sorted(p.name for p in isolated.iterdir()) == ["config.yaml"]


@pytest.mark.parametrize("value", INVALID_ROOTS)
def test_override_root_must_be_mapping(isolated, value):
    with pytest.raises(ValueError, match="Configuration overrides: configuration must be a mapping"):
        config.load_settings(overrides=value)
    assert list(isolated.iterdir()) == []


@pytest.mark.parametrize("section", SECTIONS)
@pytest.mark.parametrize("value", INVALID_SECTIONS)
def test_override_section_must_be_mapping(isolated, section, value):
    with pytest.raises(ValueError, match=f"Configuration overrides: section '{section}' must be a mapping"):
        config.load_settings(overrides={section: value})
    assert list(isolated.iterdir()) == []


@pytest.mark.parametrize("text", ["", "# comment only\n", "null\n"])
def test_empty_and_null_documents_keep_defaults(isolated, text):
    path = isolated / "config.yaml"
    path.write_text(text, encoding="utf-8")
    assert config.load_settings(path).raw == config.DEFAULTS


def test_partial_merge_precedence_and_extensions(isolated, monkeypatch):
    path = isolated / "config.yaml"
    path.write_text("server:\n  admin_port: 5999\n  extension: []\nplugin: false\n", encoding="utf-8")
    monkeypatch.setenv("LG_ADMIN_PORT", "6000")
    overrides = UserDict({"server": UserDict({"admin_port": 6001}), "plugin": None})
    before = copy.deepcopy(overrides)
    defaults = copy.deepcopy(config.DEFAULTS)
    settings = config.load_settings(path, overrides=overrides)
    assert settings.admin_port == 6001
    assert settings.viewer_port == config.DEFAULTS["server"]["viewer_port"]
    assert settings.raw["server"]["extension"] == []
    assert settings.raw["plugin"] is None
    assert overrides == before and config.DEFAULTS == defaults
    assert sorted(p.name for p in isolated.iterdir()) == ["config.yaml"]


def test_empty_section_mappings_keep_defaults(isolated):
    assert config.load_settings(overrides={name: {} for name in SECTIONS}).raw == config.DEFAULTS


def test_missing_explicit_file_still_precedes_override_validation(isolated):
    with pytest.raises(FileNotFoundError):
        config.load_settings(isolated / "missing.yaml", overrides=False)
