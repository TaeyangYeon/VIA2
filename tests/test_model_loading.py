import pytest
from pathlib import Path
import nbformat


def test_generate_colab_notebook_script_exists():
    """scripts/generate_colab_notebook.py 파일 존재 확인"""
    script_path = Path(__file__).parent.parent / "scripts" / "generate_colab_notebook.py"
    assert script_path.exists(), f"Script not found at {script_path}"


def test_verify_vision_models_notebook_exists():
    """scripts/verify_vision_models.ipynb 파일 존재 확인"""
    notebook_path = Path(__file__).parent.parent / "scripts" / "verify_vision_models.ipynb"
    assert notebook_path.exists(), f"Notebook not found at {notebook_path}"


def test_model_setup_doc_exists():
    """docs/MODEL_SETUP.md 파일 존재 확인"""
    doc_path = Path(__file__).parent.parent / "docs" / "MODEL_SETUP.md"
    assert doc_path.exists(), f"Documentation not found at {doc_path}"


def test_generate_script_valid_python_syntax():
    """generate_colab_notebook.py가 유효한 Python 문법인지 compile() 검증"""
    script_path = Path(__file__).parent.parent / "scripts" / "generate_colab_notebook.py"
    content = script_path.read_text()

    try:
        compile(content, str(script_path), 'exec')
    except SyntaxError as e:
        pytest.fail(f"SyntaxError in generate_colab_notebook.py: {e}")


def test_model_setup_doc_contains_all_model_sections():
    """MODEL_SETUP.md에 5개 모델 섹션 존재 확인"""
    doc_path = Path(__file__).parent.parent / "docs" / "MODEL_SETUP.md"
    content = doc_path.read_text()

    model_names = ["Florence-2", "Grounding DINO", "SAM 2", "DINOv2", "Depth-Anything-V2"]

    for model_name in model_names:
        assert model_name in content, f"Model section '{model_name}' not found in MODEL_SETUP.md"


def test_notebook_is_valid_nbformat():
    """verify_vision_models.ipynb를 nbformat으로 읽어서 유효한 노트북인지 검증"""
    notebook_path = Path(__file__).parent.parent / "scripts" / "verify_vision_models.ipynb"

    with open(notebook_path, 'r', encoding='utf-8') as f:
        try:
            nb = nbformat.read(f, as_version=4)
        except Exception as e:
            pytest.fail(f"Failed to read notebook as valid nbformat: {e}")

    assert nb is not None, "Notebook could not be loaded"


def test_notebook_has_minimum_15_cells():
    """노트북 셀 수가 최소 15개 이상인지 확인"""
    notebook_path = Path(__file__).parent.parent / "scripts" / "verify_vision_models.ipynb"

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    assert len(nb.cells) >= 15, f"Notebook has {len(nb.cells)} cells, expected at least 15"


def test_notebook_code_cells_contain_all_model_names():
    """노트북 코드 셀에 5개 모델 이름 문자열 포함 확인"""
    notebook_path = Path(__file__).parent.parent / "scripts" / "verify_vision_models.ipynb"

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    # Join all code cell sources
    code_content = "\n".join(
        cell.source for cell in nb.cells if cell.cell_type == "code"
    )

    model_names = ["Florence-2", "Grounding DINO", "SAM 2", "DINOv2", "Depth-Anything-V2"]

    for model_name in model_names:
        assert model_name in code_content, f"Model name '{model_name}' not found in notebook code cells"
