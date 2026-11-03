"""Bug 23: explicit config failure must not fall back or create storage."""
import errno
from pathlib import Path
import re

import pytest
from looking_glass import config


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    for key in ("LG_CONFIG", "LG_HOST", "LG_ADMIN_PORT", "LG_VIEWER_PORT", "LG_DATA_DIR"):
        monkeypatch.delenv(key, raising=False)
    return tmp_path


def load_from(mode, path, monkeypatch):
    if mode == "environment":
        monkeypatch.setenv("LG_CONFIG", str(path))
        return config.load_settings()
    return config.load_settings(path)


@pytest.mark.parametrize("mode", ["argument", "environment"])
def test_missing_explicit_config_does_not_fall_back_or_write(isolated, monkeypatch, mode):
    default = isolated / "config.yaml"
    default.write_text("server:\n  admin_port: 5999\n")
    monkeypatch.setenv("LG_DATA_DIR", str(isolated / "state"))
    missing = isolated / "not-mounted/config.yaml"
    before = sorted(str(p) for p in isolated.rglob("*"))
    with pytest.raises(FileNotFoundError, match=re.escape(str(missing))):
        load_from(mode, missing, monkeypatch)
    assert sorted(str(p) for p in isolated.rglob("*")) == before
    assert not (isolated / "state").exists()


@pytest.mark.parametrize("mode", ["argument", "environment"])
def test_unreadable_explicit_config_propagates_path_error(isolated, monkeypatch, mode):
    path = isolated / "private.yaml"
    path.write_text("server: {}\n")
    original = Path.open
    def denied(self, *args, **kwargs):
        if self == path:
            raise PermissionError(errno.EACCES, "Permission denied", str(self))
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(PermissionError, match=re.escape(str(path))):
        load_from(mode, path, monkeypatch)
    assert not (isolated / "data").exists()


@pytest.mark.parametrize("mode", ["argument", "environment"])
def test_directory_is_not_treated_as_optional_config(isolated, monkeypatch, mode):
    with pytest.raises(IsADirectoryError):
        load_from(mode, isolated, monkeypatch)
    assert not (isolated / "data").exists()


@pytest.mark.parametrize("mode", ["argument", "environment"])
def test_broken_explicit_symlink_is_failure(isolated, monkeypatch, mode):
    path = isolated / "broken.yaml"
    path.symlink_to(isolated / "missing.yaml")
    with pytest.raises(FileNotFoundError):
        load_from(mode, path, monkeypatch)


@pytest.mark.parametrize("mode", ["argument", "environment"])
def test_empty_explicit_path_is_rejected(isolated, monkeypatch, mode):
    with pytest.raises(ValueError, match="must not be empty"):
        load_from(mode, "", monkeypatch)


def test_no_explicit_or_default_file_uses_defaults_without_writes(isolated):
    settings = config.load_settings()
    assert settings.config_path is None
    assert settings.raw == config.DEFAULTS
    assert list(isolated.iterdir()) == []


def test_optional_default_is_loaded_and_empty_file_still_supported(isolated):
    path = isolated / "config.yaml"
    path.write_text("server:\n  admin_port: 5999\n")
    settings = config.load_settings()
    assert settings.config_path == path and settings.admin_port == 5999
    path.write_text("")
    assert config.load_settings().raw == config.DEFAULTS


def test_argument_precedes_lg_config_and_environment_overrides_file(isolated, monkeypatch):
    good = isolated / "chosen.yaml"
    good.write_text("server:\n  host: 127.0.0.2\n  admin_port: 5999\nstorage:\n  data_dir: selected-data\n")
    monkeypatch.setenv("LG_CONFIG", str(isolated / "missing.yaml"))
    monkeypatch.setenv("LG_HOST", "127.0.0.3")
    monkeypatch.setenv("LG_VIEWER_PORT", "6111")
    settings = config.load_settings(good, overrides={"server": {"admin_port": 6122}})
    assert settings.config_path == good
    assert (settings.host, settings.admin_port, settings.viewer_port) == ("127.0.0.3", 6122, 6111)
    assert settings.data_dir == isolated / "selected-data"
    assert not settings.data_dir.exists()


def test_missing_argument_never_uses_valid_lg_config(isolated, monkeypatch):
    good = isolated / "good.yaml"
    good.write_text("server: {}\n")
    monkeypatch.setenv("LG_CONFIG", str(good))
    with pytest.raises(FileNotFoundError):
        config.load_settings(isolated / "missing.yaml")
