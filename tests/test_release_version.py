from __future__ import annotations

import importlib.util
import shutil
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prepare_release", ROOT / "tools/prepare_release.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FILES = ("pyproject.toml", "uv.lock", "src/billharbor_vendors/__init__.py")


def checkout(tmp_path: Path) -> Path:
    for name in FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


@pytest.mark.parametrize("tag", ["v1.2.3", "v1.2.3.dev4", "v1.2.3rc2", "v1.2.3a1", "v1.2.3b1", "v1.2.3.post1"])
def test_release_stamps_only_aggregate(tmp_path: Path, tag: str) -> None:
    root = checkout(tmp_path)
    before = tomllib.loads((root / "uv.lock").read_text())
    version = MODULE.prepare(root, tag)
    after = tomllib.loads((root / "uv.lock").read_text())
    original = [p for p in before["package"] if p["name"] == "billharbor-vendors"][0]
    original["version"] = version
    assert before == after
    assert tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"] == tag[1:]
    namespace = {}
    exec((root / FILES[2]).read_text(), namespace)
    assert namespace["__version__"] == tag[1:]
    assert MODULE.prepare(root, tag) == version  # Repeatable within disposable checkout.


@pytest.mark.parametrize("tag", ["1.2.3", "v01.2.3", "v1.2", "v1.2.3RC1", "v1.2.3+local", "v1.2.3\n", "v1.2.3;echo bad", "v1.2.3.dev01"])
def test_invalid_tag_changes_nothing(tmp_path: Path, tag: str) -> None:
    root = checkout(tmp_path)
    before = {name: (root / name).read_bytes() for name in FILES}
    with pytest.raises(ValueError):
        MODULE.prepare(root, tag)
    assert before == {name: (root / name).read_bytes() for name in FILES}


def test_inconsistent_export_changes_nothing(tmp_path: Path) -> None:
    root = checkout(tmp_path)
    (root / FILES[2]).write_text('__version__ = "broken"\n')
    before = {name: (root / name).read_bytes() for name in FILES}
    with pytest.raises(ValueError):
        MODULE.prepare(root, "v1.2.3")
    assert before == {name: (root / name).read_bytes() for name in FILES}
