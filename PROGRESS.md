# VIA2 Progress

## 현재 진행 단계: Step 3 (완료)

## Phase 1: 환경 설정
- [x] Step 1: Python 환경 + 프로젝트 디렉토리 초기화
- [x] Step 2: OpenCV + NumPy + PyTorch 설치
- [x] Step 3: Ollama 설치 + Qwen2.5-Coder 검증
- [ ] Step 4: SOTA Vision 모델 사전 검증

## Phase 2: 백엔드 기반 + AI Adapter
- [ ] Step 5: FastAPI 초기화 + Health 엔드포인트
- [ ] Step 6: AI Engine Adapter + 로컬 Ollama 어댑터
- [ ] Step 7: Remote AI Adapter
- [ ] Step 8: Engine 설정 API
- [ ] Step 9: 이미지 업로드 + 저장소 API
- [ ] Step 10: ROI 설정 API + Config + Directive API
- [ ] Step 11: 로깅 시스템

## Phase 3: 시각 분석 에이전트
- [ ] Step 12: Agent 기본 인터페이스 + 전체 모델 정의
- [ ] Step 13: Spec Agent (Qwen2.5-Coder)
- [ ] Step 14: Image Analysis Agent (OpenCV)
- [ ] Step 15: Depth Agent (Depth-Anything-V2)
- [ ] Step 16: Material Agent (Florence-2 + DINOv2)
- [ ] Step 17: ROI Agent (Grounding DINO + SAM 2)
- [ ] Step 18: 분석 결과 통합 모듈
- [ ] Step 19: Vision Judge Agent (Qwen2.5-VL)

## Phase 4: 파이프라인 설계
- [ ] Step 20: Pipeline Block Library
- [ ] Step 21: Pipeline Composer
- [ ] Step 22: Parameter Searcher + ProcessingQualityEvaluator
- [ ] Step 23: Algorithm Selector (결정 트리)
- [ ] Step 24: Inspection Plan Agent
- [ ] Step 25: Vision Judge 기반 파이프라인 선정 루프
- [ ] Step 26: Test Agent (Inspection, 항목별)
- [ ] Step 27: Test Agent (Align)

## Phase 5: Blueprint + 평가 루프
- [ ] Step 28: Blueprint Agent (SVG 다이어그램)
- [ ] Step 29: 파라미터 시트 생성기
- [ ] Step 30: Evaluation Agent
- [ ] Step 31: Feedback Controller
- [ ] Step 32: Decision Agent (InternVL + DINOv2 통계)
- [ ] Step 33: Orchestrator (기본 + Retry + Decision 연결)
- [ ] Step 34: 파이프라인 실행 API + 조명 권장사항

## Phase 6: 메인 프론트엔드
- [ ] Step 35: Electron + React + TypeScript + TailwindCSS 초기화
- [ ] Step 36: Redux Store + API 클라이언트
- [ ] Step 37: 전체 레이아웃 + Input Panel
- [ ] Step 38: ROI 드로잉 UI
- [ ] Step 39: Engine 설정 + Directive Panel
- [ ] Step 40: Config Panel + Execution Panel
- [ ] Step 41: Result Panel (Blueprint Viewer)

## Phase 7: Light Test 윈도우
- [ ] Step 42: Light Test 윈도우 + 듀얼 뷰 레이아웃
- [ ] Step 43: Depth + Material 분석 백엔드 연동
- [ ] Step 44: 조명 배치 UI (정면도/평면도 동기화)
- [ ] Step 45: PBR 렌더링 엔진
- [ ] Step 46: 컬러 조명 + 편광 시뮬레이션

## Phase 8: 통합 / 패키징 / 배포
- [ ] Step 47: 전체 E2E 테스트
- [ ] Step 48: Light Test E2E + 결과 내보내기
- [ ] Step 49: FastAPI 자동 시작 + macOS DMG 패키징
- [ ] Step 50: 문서화 + 최종 통합 테스트

---

## Step 3 완료 내역

**Ollama 버전**: 0.21.0

**qwen2.5-coder:7b 모델 정보**:
- 모델명: qwen2.5-coder:7b
- ID: dae161e27b0e
- 크기: 4.7 GB

**생성/수정된 파일**:
- `scripts/start_ollama.sh` (신규 생성 — ollama serve 백그라운드 실행 + health check)
- `tests/test_ollama.py` (신규 생성 — 4개 테스트)
- `requirements.txt` (requests>=2.31.0 추가)

**pytest 결과** (전체 20개):
```
20 passed in 45.10s
tests/test_ollama.py::test_ollama_is_running PASSED
tests/test_ollama.py::test_qwen_coder_model_exists PASSED
tests/test_ollama.py::test_text_generation PASSED
tests/test_ollama.py::test_json_output_parsing PASSED
tests/test_libraries.py::test_opencv_import PASSED
tests/test_libraries.py::test_numpy_import PASSED
tests/test_libraries.py::test_torch_import PASSED
tests/test_libraries.py::test_opencv_image_operations PASSED
tests/test_libraries.py::test_torch_tensor_operations PASSED
tests/test_libraries.py::test_opencv_basic_processing PASSED
tests/test_libraries.py::test_numpy_opencv_interop PASSED
tests/test_project_structure.py::test_python_version_is_311 PASSED
tests/test_project_structure.py::test_required_directories_exist PASSED
tests/test_project_structure.py::test_required_init_files_exist PASSED
tests/test_project_structure.py::test_backend_placeholder_files_exist PASSED
tests/test_project_structure.py::test_pyproject_toml_exists_and_contains_via2 PASSED
tests/test_project_structure.py::test_requirements_txt_exists PASSED
tests/test_project_structure.py::test_gitignore_exists PASSED
tests/test_project_structure.py::test_readme_exists PASSED
tests/test_project_structure.py::test_python_version_file_exists PASSED
```

**이슈 및 해결 사항**: 특이사항 없음

---

## Step 1 완료 내역

**Python 버전**: Python 3.11.15 (pyenv 3.11.15)

**생성된 디렉토리**:
- `backend/`
- `backend/routers/`
- `backend/services/`
- `backend/models/`
- `agents/`
- `agents/prompts/`
- `light_test/`
- `frontend/` (빈 디렉토리)
- `tests/`
- `scripts/` (빈 디렉토리)
- `docs/` (빈 디렉토리)

**생성된 파일**:
- `backend/__init__.py`
- `backend/main.py` (placeholder)
- `backend/config.py` (placeholder)
- `backend/routers/__init__.py`
- `backend/services/__init__.py`
- `backend/models/__init__.py`
- `agents/__init__.py`
- `agents/prompts/__init__.py`
- `light_test/__init__.py`
- `tests/__init__.py`
- `tests/test_project_structure.py`
- `pyproject.toml`
- `requirements.txt`
- `.python-version` (3.11.15, set via `pyenv local`)
- `.gitignore`
- `README.md`

**이슈 및 해결**:
- pytest가 다른 프로젝트의 venv에 설치되어 있었으나, Python 3.11.15가 시스템에서 직접 pytest를 사용 가능 (pytest-9.0.3). 별도 설치 불필요.
- `.gitignore`에서 `.python-version` 제외 → 프로젝트 설정 파일로 추적 대상에 포함.

**pytest 결과**:
```
9 passed in 0.02s
tests/test_project_structure.py::test_python_version_is_311 PASSED
tests/test_project_structure.py::test_required_directories_exist PASSED
tests/test_project_structure.py::test_required_init_files_exist PASSED
tests/test_project_structure.py::test_backend_placeholder_files_exist PASSED
tests/test_project_structure.py::test_pyproject_toml_exists_and_contains_via2 PASSED
tests/test_project_structure.py::test_requirements_txt_exists PASSED
tests/test_project_structure.py::test_gitignore_exists PASSED
tests/test_project_structure.py::test_readme_exists PASSED
tests/test_project_structure.py::test_python_version_file_exists PASSED
```

---

## Step 2 완료 내역

**설치된 패키지 버전** (pyenv Python 3.11.15):
- `opencv-python` 4.8.1.78 (x86_64 호환, GUI 포함 variant — pyenv에 기존 설치됨)
- `numpy` 1.24.4
- `torch` 2.2.2 (CPU 전용)

**이슈 및 해결**:
- pyenv Python 3.11.15에 이미 OpenCV, NumPy, PyTorch가 설치되어 있었음 → 별도 `pip install` 불필요.
- 쉘의 `python3` 명령이 K-ETF_Trend 프로젝트의 `.venv`를 가리키고 있음 → 이 프로젝트에서는 `/Users/geseuteu/.pyenv/versions/3.11.15/bin/python`을 명시적으로 사용해야 함. 추후 VIA2 전용 `.venv` 생성 권장.
- `requirements.txt`에는 `opencv-python-headless`로 명시 (백엔드에 GUI 불필요). 현재 환경에서는 `opencv-python`이 설치되어 있으나 headless 기능 동작 확인됨.

**생성/수정된 파일**:
- `tests/test_libraries.py` (신규 생성)
- `requirements.txt` (opencv-python-headless, numpy, torch 추가)

**pytest 결과** (전체 16개):
```
16 passed in 1.81s
tests/test_libraries.py::test_opencv_import PASSED
tests/test_libraries.py::test_numpy_import PASSED
tests/test_libraries.py::test_torch_import PASSED
tests/test_libraries.py::test_opencv_image_operations PASSED
tests/test_libraries.py::test_torch_tensor_operations PASSED
tests/test_libraries.py::test_opencv_basic_processing PASSED
tests/test_libraries.py::test_numpy_opencv_interop PASSED
tests/test_project_structure.py::test_python_version_is_311 PASSED
tests/test_project_structure.py::test_required_directories_exist PASSED
tests/test_project_structure.py::test_required_init_files_exist PASSED
tests/test_project_structure.py::test_backend_placeholder_files_exist PASSED
tests/test_project_structure.py::test_pyproject_toml_exists_and_contains_via2 PASSED
tests/test_project_structure.py::test_requirements_txt_exists PASSED
tests/test_project_structure.py::test_gitignore_exists PASSED
tests/test_project_structure.py::test_readme_exists PASSED
tests/test_project_structure.py::test_python_version_file_exists PASSED
```
