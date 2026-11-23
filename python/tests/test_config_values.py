"""Bug 31: colour leaves are validated by the loader, not inside server startup."""
import pytest

from looking_glass.config import ConfigError, load_settings


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch):
    for name in ("LG_CONFIG", "LG_HOST", "LG_ADMIN_PORT", "LG_VIEWER_PORT", "LG_DATA_DIR"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("text,shown", [
    ("fog:\n  fog_color: #808080\n", "None"),          # unquoted: YAML comment -> null
    ("fog:\n  fog_color: null\n", "None"),
    ("fog:\n  fog_color: grey\n", "'grey'"),
    ("fog:\n  fog_color: '#80808'\n", "'#80808'"),
    ("fog:\n  fog_color: '#12345g'\n", "'#12345g'"),
    ("fog:\n  fog_color: 808080\n", "808080"),         # YAML integer, not a string
    ("fog:\n  fog_color: ''\n", "''"),
])
def test_invalid_fog_colour_is_rejected_with_location(tmp_path, text, shown):
    path = tmp_path / "bad.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError) as info:
        load_settings(path)
    message = str(info.value)
    assert str(path) in message
    assert "'fog.fog_color'" in message
    assert f"not {shown}." in message


def test_null_colour_message_suggests_quoting(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("fog:\n  fog_color: #808080\n", encoding="utf-8")
    with pytest.raises(ConfigError, match='quote colours') as info:
        load_settings(path)
    assert 'fog_color: "#808080"' in str(info.value)


def test_config_error_remains_a_value_error():
    assert issubclass(ConfigError, ValueError)


@pytest.mark.parametrize("colour", ["#808080", "#abc", "#ABCDEF", "808080", "fff"])
def test_valid_colours_load(tmp_path, colour):
    path = tmp_path / "ok.yaml"
    path.write_text(f'fog:\n  fog_color: "{colour}"\n', encoding="utf-8")
    assert load_settings(path).section("fog")["fog_color"] == colour


def test_defaults_and_overrides_are_validated(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    assert load_settings(path).section("fog")["fog_color"] == "#000000"
    with pytest.raises(ConfigError, match="'fog.fog_color'"):
        load_settings(path, overrides={"fog": {"fog_color": None}})
