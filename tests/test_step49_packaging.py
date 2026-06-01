import os
import pytest


def test_electron_builder_yml_exists():
    assert os.path.exists("frontend/electron-builder.yml")


def test_build_icons_dir_exists():
    assert os.path.isdir("build/icons")


def test_icon_png_exists():
    assert os.path.exists("build/icons/icon.png")


def test_preload_js_exists():
    assert os.path.exists("frontend/preload.js")


def test_engine_setup_guide_component_exists():
    assert os.path.exists("frontend/src/components/EngineSetupGuide.tsx")
