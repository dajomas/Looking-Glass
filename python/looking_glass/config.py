"""Configuration loading.

Configuration comes from (in increasing priority):
  1. Built-in defaults (DEFAULTS below)
  2. A YAML file (config.yaml, path passed with --config or LG_CONFIG)
  3. Environment variables (LG_ADMIN_PORT, LG_VIEWER_PORT, LG_HOST, LG_DATA_DIR)
"""

import copy
from collections.abc import Mapping
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULTS: dict[str, Any] = {
    "server": {
        "host": "0.0.0.0",
        "admin_port": 5000,
        "viewer_port": 5100,
        "log_level": "info",
        "access_log_success": False,
    },
    "storage": {
        "data_dir": "data",
        "database": "looking_glass.db",  # relative to data_dir
        "max_upload_mb": 150,
        "max_image_pixels": 400_000_000,
    },
    "security": {
        "session_hours": 12,
        "secure_cookies": False,
        "initial_superadmin": "superadmin",
        "admins_can_create_viewers": True,
        "min_password_length": 8,
        "login_max_failures": 5,
        "login_lockout_seconds": 300,
    },
    "fog": {
        "work_max_dim": 2048,      # resolution used for wall rasterising / area detection
        "wall_thickness": 3,       # px at work resolution; closes small gaps between wall ends
        "leak_warn_fraction": 0.6, # warn admin when a single click reveals more than this share of the map
        "doors_block": True,       # default for new maps: doors split areas
        "fog_color": "#000000",
        "feather_px": 2,           # soft fog edge on the viewer image
        "admin_fog_opacity": 0.55,
    },
    "scrying_glass": {
        "enabled": False,
        "base_url": "",
        "username": "",
        "password": "",
        "password_env": "LG_SCRYING_GLASS_PASSWORD",
        "timeout_seconds": 5,
    },
    "viewer": {
        "max_image_dim": 4096,     # viewer composite is downscaled to fit this
        "image_format": "webp",    # webp | jpeg | png
        "image_quality": 85,
        "title": "Looking Glass",
    },
}


def _validate_shape(value: object, source: str) -> None:
    """Validate supplied structure without restricting extension keys or leaf values."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{source}: configuration must be a mapping.")
    for name, default in DEFAULTS.items():
        if isinstance(default, dict) and name in value and not isinstance(value[name], Mapping):
            raise ValueError(f"{source}: section '{name}' must be a mapping.")


def _deep_merge(base: dict, override: Mapping) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), Mapping):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


@dataclass(slots=True)
class Settings:
    raw: dict[str, Any] = field(default_factory=lambda: copy.deepcopy(DEFAULTS))
    config_path: Path | None = None

    def section(self, name: str) -> dict[str, Any]:
        return self.raw[name]

    # Convenience accessors -------------------------------------------------
    @property
    def host(self) -> str:
        return self.raw["server"]["host"]

    @property
    def admin_port(self) -> int:
        return int(self.raw["server"]["admin_port"])

    @property
    def viewer_port(self) -> int:
        return int(self.raw["server"]["viewer_port"])

    @property
    def data_dir(self) -> Path:
        p = Path(self.raw["storage"]["data_dir"])
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def database_path(self) -> Path:
        p = Path(self.raw["storage"]["database"])
        return p if p.is_absolute() else (self.data_dir / p)

    @property
    def maps_dir(self) -> Path:
        return self.data_dir / "maps"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def static_dir(self) -> Path:
        return REPO_ROOT / "static"

    @property
    def templates_dir(self) -> Path:
        return REPO_ROOT / "templates"

    @property
    def web_html_dir(self) -> Path:
        return REPO_ROOT / "web_html"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.maps_dir, self.cache_dir, self.database_path.parent):
            d.mkdir(parents=True, exist_ok=True)


def load_settings(path: str | os.PathLike | None = None, overrides: Mapping | None = None) -> Settings:
    raw = copy.deepcopy(DEFAULTS)
    cfg_path: Path | None = None
    candidate = path if path is not None else os.environ.get("LG_CONFIG")
    if candidate is not None:
        if not os.fspath(candidate):
            raise ValueError("Explicit configuration path must not be empty.")
        cfg_path = Path(candidate)
    elif (REPO_ROOT / "config.yaml").exists():
        cfg_path = REPO_ROOT / "config.yaml"
    # Only discovery is optional; explicit paths must open successfully.
    if cfg_path is not None:
        with cfg_path.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
        # Preserve empty/null YAML documents, but do not discard other false-like values.
        loaded = {} if loaded is None else loaded
        _validate_shape(loaded, f"Configuration file {cfg_path}")
        raw = _deep_merge(raw, loaded)
    if overrides is not None:
        _validate_shape(overrides, "Configuration overrides")

    env_map = {
        "LG_HOST": ("server", "host", str),
        "LG_ADMIN_PORT": ("server", "admin_port", int),
        "LG_VIEWER_PORT": ("server", "viewer_port", int),
        "LG_DATA_DIR": ("storage", "data_dir", str),
    }
    for env, (sec, key, cast) in env_map.items():
        if env in os.environ:
            raw[sec][key] = cast(os.environ[env])
    if overrides is not None:
        raw = _deep_merge(raw, overrides)
    from .services.scrying_glass import options
    options(raw["scrying_glass"])
    return Settings(raw=raw, config_path=cfg_path)
