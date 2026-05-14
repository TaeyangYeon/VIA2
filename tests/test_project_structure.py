import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_python_version_is_311():
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 11


def test_required_directories_exist():
    dirs = [
        ROOT / "backend",
        ROOT / "backend" / "routers",
        ROOT / "backend" / "services",
        ROOT / "backend" / "models",
        ROOT / "agents",
        ROOT / "agents" / "prompts",
        ROOT / "light_test",
        ROOT / "frontend",
        ROOT / "tests",
        ROOT / "scripts",
        ROOT / "docs",
    ]
    for d in dirs:
        assert d.is_dir(), f"Missing directory: {d}"


def test_required_init_files_exist():
    init_files = [
        ROOT / "backend" / "__init__.py",
        ROOT / "backend" / "routers" / "__init__.py",
        ROOT / "backend" / "services" / "__init__.py",
        ROOT / "backend" / "models" / "__init__.py",
        ROOT / "agents" / "__init__.py",
        ROOT / "agents" / "prompts" / "__init__.py",
        ROOT / "light_test" / "__init__.py",
        ROOT / "tests" / "__init__.py",
    ]
    for f in init_files:
        assert f.is_file(), f"Missing __init__.py: {f}"


def test_backend_placeholder_files_exist():
    assert (ROOT / "backend" / "main.py").is_file()
    assert (ROOT / "backend" / "config.py").is_file()


def test_pyproject_toml_exists_and_contains_via2():
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.is_file(), "pyproject.toml missing"
    assert "via2" in pyproject.read_text()


def test_requirements_txt_exists():
    assert (ROOT / "requirements.txt").is_file()


def test_gitignore_exists():
    assert (ROOT / ".gitignore").is_file()


def test_readme_exists():
    assert (ROOT / "README.md").is_file()


def test_python_version_file_exists():
    pv = ROOT / ".python-version"
    assert pv.is_file(), ".python-version missing"
    assert "3.11" in pv.read_text()
