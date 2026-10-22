"""Deployment example paths stay consistent with configuration resolution."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]

def test_production_config_paths():
    cfg = yaml.safe_load((ROOT / "docs/examples/config.production.yaml").read_text())
    assert cfg["storage"]["data_dir"] == "/var/lib/looking-glass"
    assert cfg["storage"]["database"] == "looking_glass.db"
    assert cfg["server"]["viewer_port"] == 5100

def test_native_unit_paths():
    unit = (ROOT / "docs/examples/looking-glass.service").read_text()
    assert "--config /etc/looking-glass/config.yaml serve" in unit
    assert "ReadWritePaths=/var/lib/looking-glass" in unit
    assert "WorkingDirectory=/opt/looking-glass" in unit
    assert "ProtectSystem=strict" in unit
    assert "/opt/looking-glass/data" not in unit

def test_container_paths_are_explicit():
    doc = (ROOT / "docs/deployment.md").read_text()
    podman = doc.split("## 4. Podman deployment")[1].split("## 5.")[0]
    assert "-e LG_CONFIG=/etc/looking-glass/config.yaml" in podman
    assert "-e LG_DATA_DIR=/app/data" in podman
    assert "/etc/looking-glass/config.yaml:/etc/looking-glass/config.yaml:ro,Z" in podman
    assert "/var/lib/looking-glass:/app/data:Z" in podman
    assert "--userns=keep-id" in podman

def test_first_install_uses_production_example():
    doc = (ROOT / "docs/deployment.md").read_text()
    assert doc.count("docs/examples/config.production.yaml /etc/looking-glass/config.yaml") == 2
    assert "### Move an existing native installation" in doc
    assert "--config /etc/looking-glass/config.yaml list-users" in doc
