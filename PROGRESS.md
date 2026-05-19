# VIA2 Progress

## 현재 진행 단계: Step 23 (완료)

## Phase 1: 환경 설정
- [x] Step 1: Python 환경 + 프로젝트 디렉토리 초기화
- [x] Step 2: OpenCV + NumPy + PyTorch 설치
- [x] Step 3: Ollama 설치 + Qwen2.5-Coder 검증
- [x] Step 4: SOTA Vision 모델 사전 검증

## Phase 2: 백엔드 기반 + AI Adapter
- [x] Step 5: FastAPI 초기화 + Health 엔드포인트
- [x] Step 6: AI Engine Adapter + 로컬 Ollama 어댑터
- [x] Step 7: Remote AI Adapter
- [x] Step 8: Engine 설정 API
- [x] Step 9: 이미지 업로드 + 저장소 API
- [x] Step 10: ROI 설정 API + Config + Directive API
- [x] Step 11: 로깅 시스템

## Phase 3: 시각 분석 에이전트
- [x] Step 12: Agent 기본 인터페이스 + 전체 모델 정의
- [x] Step 13: Spec Agent (Qwen2.5-Coder)
- [x] Step 14: Image Analysis Agent (OpenCV)
- [x] Step 15: Depth Agent (Depth-Anything-V2)
- [x] Step 16: Material Agent (Florence-2 + DINOv2)
- [x] Step 17: ROI Agent (Grounding DINO + SAM 2)
- [x] Step 18: 분석 결과 통합 모듈
- [x] Step 19: Vision Judge Agent (Qwen2.5-VL)

## Phase 4: 파이프라인 설계
- [x] Step 20: Pipeline Block Library
- [x] Step 21: Pipeline Composer
- [x] Step 22: Parameter Searcher + ProcessingQualityEvaluator
- [x] Step 23: Algorithm Selector (결정 트리)
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

## Step 23 완료 내역

### 생성된 파일
- `agents/algorithm_selector.py` (신규)
- `tests/test_algorithm_selector.py` (신규)
- `PROGRESS.md` (업데이트)

### AlgorithmSelector 인터페이스

```python
class AlgorithmSelector(BaseAgent):
    def __init__(self, directive: str = "") -> None
    async def run(self, scene_context: SceneContext, **kwargs) -> AgentResult
```

- name: `"algorithm_selector"`
- 순수 결정론적 규칙 기반 분류기 (LLM 호출 없음)
- directive는 로그에만 기록되며 결정 결과에 영향 없음

### 결정 트리 로직
| 우선순위 | 조건 | 결과 |
|----------|------|------|
| 1 | `contrast > 0.4` AND `blob_feasibility > 0.6` | BLOB |
| 2 | `color_discriminability > 0.5` | COLOR_FILTER |
| 3 | `edge_density > 0.3` AND `structural_regularity > 0.5` | EDGE_DETECTION |
| 4 | `pattern_repetition > 0.7` | TEMPLATE_MATCHING |
| 5 | (기본 폴백) | BLOB |

- 임계값 비교: 엄격한 `>` (같은 경우 미충족)
- 첫 번째 매칭 조건에서 즉시 반환 (short-circuit)

### AgentResult data 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | `str` | AlgorithmCategory 열거형의 `.value` 문자열 |
| `reason` | `str` | 선택 이유 (어떤 조건이 충족됐는지 설명) |
| `scores` | `dict` | 결정에 관여한 6개 진단 지표 값 |
| `decision_path` | `list[str]` | 각 조건 체크 결과 (`[MATCH]`/`[SKIP]`/`[DEFAULT]`) |

### 에러 처리
| 조건 | status | error_message |
|------|--------|---------------|
| `scene_context is None` | `"error"` | `"SceneContext is required"` |
| `scene_context.image_diagnosis is None` | `"error"` | `"ImageDiagnosis is required in SceneContext"` |

### Directive 처리
- directive가 있으면 `info` 레벨 로그로 기록
- 결정 트리 로직은 directive와 무관하게 동일하게 동작

### 테스트 커버리지
| 카테고리 | 테스트 수 |
|----------|----------|
| Instantiation | 2 |
| AgentResultStructure | 10 |
| DecisionTreePaths | 5 |
| DecisionPriority | 5 |
| BoundaryValues | 7 |
| ErrorHandling | 4 |
| DirectiveHandling | 2 |
| **합계** | **35** |

### pytest 결과
- 신규 테스트: 35개 (모두 통과)
- 전체 테스트: 887개 (regressions 없음)
- 실행 시간: ~55초

### 특이사항 없음
`AlgorithmCategory.GEOMETRIC`은 결정 트리에 포함되지 않음 (PLAN.md 명세에 따라 5개 enum 중 4개만 사용; default는 BLOB).

---

## Step 22 완료 내역

### 생성된 파일
- `agents/processing_quality_evaluator.py` (신규)
- `agents/parameter_searcher.py` (신규)
- `tests/test_parameter_searcher.py` (신규)
- `PROGRESS.md` (업데이트)

### ProcessingQualityEvaluator 인터페이스

```python
class ProcessingQualityEvaluator:
    def evaluate(self, original: np.ndarray, processed: np.ndarray, purpose: str = "") -> QualityScore

@dataclass
class QualityScore:
    contrast_score: float      # 0.0–1.0
    noise_score: float         # 0.0–1.0
    edge_score: float          # 0.0–1.0
    overall_score: float       # 0.0–1.0
    details: dict              # raw metrics
```

### 스코어링 로직
| 항목 | 방법 | 가중치 |
|------|------|--------|
| contrast_score | `min(1, proc_std / max(orig_std, 1))` | 0.3 |
| noise_score | `min(1, orig_lap_var / max(proc_lap_var, 1))` | 0.3 |
| edge_score | `min(1, proc_canny_count / max(orig_canny_count, 1))` | 0.4 |
| overall_score | 가중 합계, [0,1] 클램프 | — |

- 퇴화 이미지(std < 1.0): overall_score = 0.0
- BGR(3D) / 그레이스케일(2D) 입력 모두 지원

### ParameterSearcher 인터페이스

```python
class ParameterSearcher(BaseAgent):
    def __init__(self, directive: str = "") -> None
    async def run(self, pipeline: ProcessingPipeline, image: np.ndarray,
                  roi: Optional[dict] = None, **kwargs) -> AgentResult
```

### AgentResult data 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| `optimized_pipeline` | `ProcessingPipeline` | 최적 파라미터 적용된 파이프라인 |
| `quality_score` | `dict` | QualityScore asdict |
| `search_summary` | `dict` | `{total_combinations, evaluated, best_score}` |

### Block 실행 매핑 요약
| 카테고리 | block_id | OpenCV 함수 |
|----------|----------|-------------|
| color_space | grayscale / hsv_s / hsv_v / lab_l / ycrcb_cr | cvtColor + split |
| denoise | gaussian_fine/mid | GaussianBlur |
| denoise | bilateral | bilateralFilter |
| denoise | median | medianBlur |
| denoise | nlmeans | fastNlMeansDenoising |
| denoise | clahe | createCLAHE().apply() |
| threshold | otsu | threshold OTSU |
| threshold | adaptive_mean/gauss | adaptiveThreshold |
| threshold | dynamic_threshold | mean+offset → threshold |
| morphology | erosion/dilation | erode/dilate |
| morphology | opening/closing/tophat/blackhat/morph_gradient | morphologyEx |
| edge | canny | Canny |
| edge | sobel/laplacian/scharr | Sobel/Laplacian/Scharr → uint8 |

### 에러 처리
| 조건 | status | error_message |
|------|--------|---------------|
| blocks 없음 | error | "Pipeline has no blocks" |
| 이미지 < 3×3 | error | "Image too small for parameter search" |
| OpenCV 예외 | 해당 조합 스킵, 로그 | — |
| 모든 조합 실패 | error | "All parameter combinations failed" |
| block_id 미등록 | block.params 폴백 + 실행 패스스루 | — |

### Directive 처리
| directive 포함 문자열 | max_evals |
|----------------------|-----------|
| "fast" (대소문자 무관) | 30 |
| "thorough" | 300 |
| 기본 | 100 |

- 조합 수 > max_evals: random.sample(seed=42)으로 무작위 샘플링

### 테스트 커버리지
| 카테고리 | 테스트 수 |
|----------|----------|
| EvaluatorInstantiation | 2 |
| QualityScoreStructure | 7 |
| QualityScoreRange | 5 |
| DegenerateDetection | 3 |
| ScoringLogic | 5 |
| SearcherInstantiation | 4 |
| AgentResultStructure | 8 |
| SearchSummary | 5 |
| PipelineOptimization | 5 |
| ROIHandling | 2 |
| ErrorHandling | 4 |
| DirectiveHandling | 3 |
| RegistryFallback | 1 |
| **합계** | **54** |

### pytest 결과
- 신규 테스트: 54개 (모두 통과)
- 전체 테스트: 852개 (regressions 없음)
- 실행 시간: ~62초

### 특이사항 없음
모든 OpenCV 연산이 gray(2D)/BGR(3D) 입력을 정상 처리.
파라미터 리스트를 itertools.product로 조합 후 최고 overall_score 조합 선택.

---

## Step 21 완료 내역

### 생성된 파일
- `agents/pipeline_composer.py` (신규)
- `tests/test_pipeline_composer.py` (신규)
- `PROGRESS.md` (업데이트)

### PipelineComposer 인터페이스
```python
class PipelineComposer(BaseAgent):
    def __init__(self, directive: str = "") -> None: ...
    async def run(self, scene_context: SceneContext, **kwargs) -> AgentResult: ...
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `pipelines` | `list[ProcessingPipeline]` | 3~5개 후보 파이프라인 |
| `num_candidates` | `int` | 생성된 파이프라인 수 |
| `matching_blocks_summary` | `dict[str, int]` | 카테고리별 매칭 블록 수 |

### Pipeline Composition Rules
- 모든 파이프라인: color_space → (denoise) → threshold → (morphology) → (edge) 순서 유지
- color_space 블록 정확히 1개 필수 (폴백: grayscale)
- threshold 블록 정확히 1개 필수 (폴백: dynamic_threshold)
- denoise 선택 (noise_level > 10 시 권장)
- morphology / edge 선택
- `lighting_uniformity > 0.25`이면 최소 1개 파이프라인에 CLAHE 포함 필수

### Directive 처리
| 키워드 | 동작 |
|--------|------|
| `clahe` (대소문자 무관) | 모든 파이프라인의 denoise 위치에 CLAHE 강제 삽입 |

### 다양성 전략
1. **Basic** – 첫 번째 CS + 기본 denoise + 첫 번째 threshold
2. **Alt** – 두 번째 CS + 두 번째 denoise + 두 번째 threshold
3. **Morph** – 첫 번째 CS + 형태학 블록 추가
4. **Edge** – 첫 번째 CS + 엣지 블록 추가
5. **Full** – 첫 번째 CS + morph + edge 조합
- 매칭 블록이 부족할 경우 레지스트리에서 `opening`, `closing`, `sobel`, `canny`를 탐색 블록으로 보충하여 중복 없는 파이프라인 최소 3개 보장

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|----------|-----------|
| 클래스 인스턴스화 | 5 |
| AgentResult 구조 | 8 |
| 파이프라인 수 (3~5) | 4 |
| 파이프라인 구조 | 5 |
| 블록 구조 | 5 |
| 블록 순서 | 6 |
| CLAHE 조명 처리 | 2 |
| Directive 처리 | 4 |
| 파이프라인 다양성 | 3 |
| 에러 처리 | 4 |
| matching_blocks_summary | 3 |
| 고노이즈 진단 | 2 |
| 불균일 조명 진단 | 2 |
| **합계** | **53** |

### pytest 결과
- 신규 테스트: 54개 통과
- 전체 테스트: 798개 통과 / 0 실패

### 이슈 및 해결 사항
- **실제 모델 필드명 불일치**: 스펙 문서의 `PipelineBlock(name, category, params)` 는 실제로 `PipelineBlock(block_id, block_type, params)`, `ProcessingPipeline(name, ...)` 은 `ProcessingPipeline(pipeline_id, ...)` 임 — 소스 파일 직접 확인 후 실제 필드명 사용
- **최소 진단 다양성**: matching 블록이 grayscale + dynamic_threshold 뿐일 때도 3개 이상의 고유 파이프라인 보장 — opening/closing/sobel/canny를 탐색 블록으로 보충

---

## Step 20 완료 내역

**생성된 파일**:
- `agents/pipeline_blocks.py` (신규 생성 — `BlockDefinition` 데이터클래스, `BLOCK_REGISTRY`, 조회/필터 함수 4종)
- `tests/test_pipeline_blocks.py` (신규 생성 — 102개 테스트, 전부 통과)

**BlockDefinition 인터페이스**:
```python
@dataclass
class BlockDefinition:
    name: str                                    # 블록 ID
    category: str                                # "color_space" | "denoise" | "threshold" | "morphology" | "edge"
    when: Callable[[ImageDiagnosis], bool]        # 조건 함수
    params: dict                                 # 파라미터 탐색 범위
    description: str                             # 한국어 설명
```

> `BlockDefinition`은 라이브러리 정의용 — `models.py`의 `PipelineBlock`(파이프라인 구성용)과 별개

**BLOCK_REGISTRY 블록 목록 (26개)**:

| 카테고리 | 블록 이름 |
|---|---|
| color_space (5) | grayscale, hsv_s, hsv_v, lab_l, ycrcb_cr |
| denoise (6) | gaussian_fine, gaussian_mid, bilateral, median, nlmeans, clahe |
| threshold (4) | otsu, adaptive_mean, adaptive_gauss, dynamic_threshold |
| morphology (7) | erosion, dilation, opening, closing, tophat, blackhat, morph_gradient |
| edge (4) | canny, sobel, laplacian, scharr |

> 태스크 명세의 "28 total"은 오기 — 실제 나열된 블록 합산 결과 26개

**get_matching_blocks 동작**:
- `diagnosis: ImageDiagnosis`와 선택적 `category: str | None` 인자 수신
- `BLOCK_REGISTRY` 전체 순회하며 `block.when(diagnosis)` 평가
- `True`인 블록만 반환; `category` 지정 시 해당 카테고리로 추가 필터링

**조건 매칭 로직 요약**:

| 시나리오 | 매칭 블록 (예시) |
|---|---|
| noise_level > 5 | gaussian_fine |
| noise_level > 15 | gaussian_mid |
| noise_level > 10 + edge_sharpness > 0.1 | bilateral |
| noise_level > 20 | median |
| noise_level > 30 | nlmeans |
| lighting_uniformity > 0.25 | clahe |
| lighting_uniformity > 0.2 | adaptive_mean |
| lighting_uniformity > 0.2 + noise_level > 10 | adaptive_gauss |
| lighting_uniformity > 0.3 | lab_l, tophat, blackhat |
| contrast > 0.15 | otsu |
| contrast < 0.15 | dynamic_threshold |
| color_discriminability > 0.3 | hsv_s |
| color_discriminability > 0.2 | hsv_v |
| color_discriminability > 0.4 + dominant_channel_ratio < 0.5 | ycrcb_cr |
| edge_sharpness > 0.05 | canny, laplacian |
| edge_sharpness > 0.03 | sobel, scharr |
| noise_level < 15 + edge_sharpness > 0.05 | laplacian |
| edge_density > 0.1 | erosion, morph_gradient |
| edge_density > 0.05 | dilation, closing |
| noise_level > 10 | opening |
| 항상 | grayscale |

**테스트 커버리지**:

| 카테고리 | 테스트 수 |
|---|---|
| BlockDefinition 구조 | 10 |
| 레지스트리 블록 수 | 7 |
| get_block 조회 | 30 |
| 고노이즈 매칭 | 10 |
| 조명 불균일 매칭 | 9 |
| 대비 매칭 | 4 |
| 색상 구분성 매칭 | 7 |
| 엣지 선명도 매칭 | 7 |
| 모폴로지 조건 | 6 |
| 카테고리 필터 | 6 |
| 기본 진단 최소 매칭 | 5 |
| **합계** | **102** |

**pytest 결과**:
- 신규 테스트: 102개 추가
- 전체: 744 passed (642 → 744), 0 failed
- 회귀 없음

**이슈 및 해결**:
1. **태스크 명세 블록 수 불일치**: 명세에 "28 total"이라 명시됐으나 카테고리별 블록 나열 합계는 5+6+4+7+4=26. 실제 나열된 블록을 기준으로 구현하고 테스트도 26으로 수정.
2. **lighting_uniformity 해석**: `image_analysis_agent.py` 확인 결과 이 값은 coefficient of variation(CV)으로, 값이 클수록 조명이 불균일함. 조건식 `> 0.2~0.3`은 "불균일 조명일 때 해당 블록 적용"을 의미 — PLAN.md 명칭과 실제 코드 필드 간 혼동 없이 정확히 적용.
3. **BlockDefinition 데이터클래스 callable 필드**: `when: Callable[[ImageDiagnosis], bool]` 필드를 가진 dataclass는 `__eq__` 비교 시 함수 동일성(identity)으로 비교되므로 문제 없음. 람다 늦은 바인딩 위험도 리스트 컴프리헨션이 아닌 명시적 구성으로 회피.

---

## Step 19 완료 내역

**생성된 파일**:
- `agents/vision_judge_agent.py` (신규 생성 — `VisionJudgeAgent(BaseAgent)`: Qwen2.5-VL 원격 클라이언트)
- `agents/prompts/vision_judge_prompt.py` (신규 생성 — `build_vision_judge_prompt()`: VLM 평가 프롬프트 빌더)
- `tests/test_vision_judge.py` (신규 생성 — 47개 테스트, 전부 통과)

**VisionJudgeAgent 인터페이스**:
```python
VisionJudgeAgent(remote_url: str, directive: str = "")
async def run(
    self,
    original_image: np.ndarray,
    processed_image: np.ndarray,
    purpose: str,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

**AgentResult data 필드**:

| 키 | 타입 | 설명 |
|---|---|---|
| `judgement` | dict | JudgementResult (asdict) |
| `raw_response` | str | 서버 원시 응답 텍스트 |

**원격 추론 프로토콜**:
- 엔드포인트: `POST {remote_url}/vision_judge/evaluate`
- 요청: `{"original_image": "<base64 JPEG>", "processed_image": "<base64 JPEG>", "purpose": str, "directive": str}`
- 응답: `{"visibility_score": float, "separability_score": float, "measurability_score": float, "problems": [str], "next_suggestion": str}`
- timeout: 60.0초
- 그레이스케일 이미지는 자동으로 BGR 변환 후 JPEG 인코딩

**build_vision_judge_prompt 설명**:
- 입력: `purpose: str`, `directive: str = ""`
- 출력: 단일 문자열 프롬프트 — VLM이 원본/처리 이미지를 비교하여 가시성/분리성/측정성 점수를 strict JSON으로 출력하도록 지시
- directive 제공 시 프롬프트 끝에 "Additional evaluation guidance: {directive}" 추가

**에러 처리 테이블**:

| 조건 | 동작 |
|---|---|
| original_image < 3×3 | status="error", "Original image too small for vision judge" |
| processed_image < 3×3 | status="error", "Processed image too small for vision judge" |
| httpx.ConnectError | status="error", "Vision Judge server unreachable: {url}" |
| 응답 키 누락 / JSON 파싱 실패 | status="error", "Invalid Vision Judge response format" |
| HTTP 비-2xx | status="error", "Vision Judge server error: {status_code}" |
| 점수 범위 초과 | [0.0, 1.0]으로 클램핑 |

**테스트 커버리지**:

| 카테고리 | 테스트 수 |
|---|---|
| Class instantiation | 5 |
| AgentResult structure | 6 |
| JudgementResult fields | 6 |
| Score computation | 4 |
| Good vs bad processing | 2 |
| Prompt building | 6 |
| Remote HTTP call | 5 |
| Error handling | 7 |
| Grayscale input | 1 |
| Directive handling | 3 |
| Edge cases | 2 |
| **합계** | **47** |

**pytest 결과**:
- `tests/test_vision_judge.py`: 47 passed
- 전체 테스트: 642 passed (이전 595 + 신규 47), 리그레션 없음

**이슈 및 해결**:
- 없음

---

## Step 18 완료 내역

**생성된 파일**:
- `agents/scene_context.py` (신규 생성 — `build_scene_context()`: 4개 에이전트 결과 통합 모듈)
- `tests/test_scene_context.py` (신규 생성 — 38개 테스트, 전부 통과)

**build_scene_context 인터페이스**:
```python
def build_scene_context(
    image_analysis_result: AgentResult,
    depth_result: AgentResult,
    material_result: AgentResult,
    roi_result: AgentResult,
) -> SceneContext
```

**SceneContext 필드 매핑**:

| SceneContext 필드 | 소스 에이전트 | 비고 |
|---|---|---|
| `image_diagnosis` | ImageAnalysisAgent | 실패 시 기본값 ImageDiagnosis 생성 |
| `image_diagnosis.depth_complexity` | DepthAgent (`depth_stats`) | 실패 시 0.0 유지 |
| `image_diagnosis.has_shadow_region` | DepthAgent (`depth_stats`) | 실패 시 False 유지 |
| `image_diagnosis.surface_type` | MaterialAgent (`surface_type`) | 실패 시 "" 유지 |
| `depth_map` | DepthAgent (`depth_map`) | 실패 시 None |
| `material_map` | MaterialAgent (`material_map`) | 실패 시 None |
| `roi` | ROIAgent (정규화) | 실패 시 None |
| `spec` | — | 기본값 `{}` |

**Depth/Material 병합 로직**:
- DepthAgent 성공 시 `depth_stats.depth_complexity`, `depth_stats.has_shadow_region`을 `ImageDiagnosis` 플레이스홀더 필드에 덮어씀
- MaterialAgent 성공 시 `surface_type`을 `ImageDiagnosis.surface_type`에 덮어씀
- 데이터 키 누락 시 기본값 유지 (`.get()` + 기본값 패턴)

**ROI 정규화 로직**:
- `mode == "manual"` → `data["roi"]` 사용
- `mode == "auto"` → `data["recommended_roi"]` 사용 (None 가능)
- `mode` 키 없음 / 에러 → `None`

**부분 실패 처리**:
- 각 에이전트 `status != "success"` 또는 `data` 키 누락 → 해당 필드에 기본값 적용, 나머지 에이전트 결과는 정상 처리
- ImageAnalysisAgent 실패 → `_default_diagnosis()` 생성 후 Depth/Material 결과 병합 계속 진행

**에러 처리 테이블**:

| 실패 에이전트 | depth_map | material_map | roi | depth_complexity | surface_type |
|---|---|---|---|---|---|
| ImageAnalysis | 정상 | 정상 | 정상 | Depth에서 병합 | Material에서 병합 |
| Depth | None | 정상 | 정상 | 0.0 | Material에서 병합 |
| Material | 정상 | None | 정상 | Depth에서 병합 | "" |
| ROI | 정상 | 정상 | None | Depth에서 병합 | Material에서 병합 |
| 전부 | None | None | None | 0.0 | "" |

**테스트 커버리지**:

| 카테고리 | 테스트 수 |
|---|---|
| Basic | 5 |
| Depth merging | 4 |
| Material merging | 2 |
| ROI normalization | 4 |
| Partial failure | 8 |
| All agents failed | 6 |
| Validation | 3 |
| Edge cases | 6 |
| **합계** | **38** |

**pytest 결과**:
- `tests/test_scene_context.py`: 38 passed
- 전체 테스트: 595 passed (이전 557 + 신규 38), 리그레션 없음

**이슈 및 해결**:
- 없음

---

## Step 17 완료 내역

**생성된 파일**:
- `agents/roi_agent.py` (신규 생성 — `ROIAgent(BaseAgent)`: Grounding DINO + SAM 2 원격 클라이언트)
- `tests/test_roi_agent.py` (신규 생성 — 57개 테스트, 전부 통과)

**ROIAgent 인터페이스**:
```python
ROIAgent(remote_url: str, directive: str = "")
async def run(
    self,
    image: np.ndarray,              # BGR or 2D grayscale
    roi: Optional[dict] = None,     # {x1, y1, x2, y2} — manual ROI
    text_query: Optional[str] = None,  # text for auto detection
    **kwargs,
) -> AgentResult
```

**AgentResult data 필드 (manual mode)**:
| 필드 | 타입 | 설명 |
|------|------|------|
| `mode` | `str` | `"manual"` |
| `roi` | `dict` | 클램핑된 ROI 좌표 `{x1, y1, x2, y2}` |
| `roi_stats` | `dict` | `{"area_ratio": float, "aspect_ratio": float}` |

**AgentResult data 필드 (auto mode)**:
| 필드 | 타입 | 설명 |
|------|------|------|
| `mode` | `str` | `"auto"` |
| `query` | `str` | 사용된 텍스트 쿼리 |
| `detections` | `list` | DINO 감지 결과 `[{"box", "score", "label"}, ...]` |
| `recommended_roi` | `dict\|None` | 추천 ROI `{x1, y1, x2, y2}` (감지 없으면 None) |
| `masks` | `list` | SAM 2 마스크 `[{"bbox", "area", "segmentation_rle"}, ...]` |
| `confidence` | `float` | 최종 신뢰도 점수 |
| `message` | `str` | 감지 없을 때 안내 메시지 (optional) |

**원격 추론 프로토콜**:
| 모델 | 엔드포인트 | 요청 payload | 응답 |
|------|-----------|-------------|------|
| Grounding DINO | `POST {remote_url}/grounding_dino/detect` | `{"image": "<base64 JPEG>", "text_query": str, "threshold": 0.3}` | `{"boxes": [[x1,y1,x2,y2],...], "scores": [...], "labels": [...]}` |
| SAM 2 | `POST {remote_url}/sam2/segment` | `{"image": "<base64 JPEG>", "boxes": [[x1,y1,x2,y2],...]}` | `{"masks": [{"bbox","area","segmentation_rle"}], "scores": [...]}` |

- `httpx.AsyncClient` 단일 컨텍스트 내에서 DINO → SAM 2 순차 호출 (timeout=60s)
- DINO 감지 결과가 없으면 SAM 2 호출 생략
- 모델 로컬 로드 없음 — 모든 추론은 Colab GPU에서만 실행

**에러 처리**:
| 조건 | 동작 | error_message |
|------|------|---------------|
| 이미지 < 3×3 | `status="error"` | `"Image too small for ROI analysis"` |
| roi도 text_query도 없음 | `status="error"` | `"No ROI or text query provided"` |
| ROI 클램핑 후 너비/높이 0 | `status="error"` | `"ROI has zero width or height after clamping to image bounds"` |
| DINO ConnectError | `status="error"` | `"Grounding DINO server unreachable: {url}"` |
| DINO 응답 형식 오류 | `status="error"` | `"Invalid Grounding DINO response format"` |
| DINO 감지 없음 | `status="success"` | — (data에 message 포함) |
| SAM 2 실패 (연결/형식) | `status="success"` (부분) | DINO box를 recommended_roi로 사용 |
| roi + text_query 동시 제공 | auto mode 우선 | — |

**테스트 커버리지**:
| 카테고리 | 테스트 수 |
|---------|---------|
| 클래스 인스턴스화 | 5 |
| neither roi nor text_query 에러 | 2 |
| 이미지 너무 작음 에러 | 2 |
| manual ROI 정상 동작 | 11 |
| manual ROI 클램핑 | 2 |
| manual ROI 클램핑 후 무효 | 2 |
| auto mode 성공 (DINO + SAM 2) | 11 |
| 원격 호출 검증 | 6 |
| auto mode 감지 없음 | 5 |
| roi + text_query 동시 제공 | 1 |
| DINO 서버 연결 불가 | 3 |
| SAM 2 서버 연결 불가 (부분 성공) | 3 |
| DINO 응답 형식 오류 | 1 |
| SAM 2 응답 형식 오류 (부분 성공) | 1 |
| 그레이스케일 입력 | 2 |
| **합계** | **57** |

**pytest 결과**: 557 passed (기존 500 + 신규 57), 리그레션 없음

**이슈 및 해결**:
- 없음 (TDD Red→Green 한 사이클로 완료)
- SAM 2 실패 시 부분 성공 처리: `except httpx.ConnectError` + `except Exception` 두 케이스 모두 `sam2_data = None` 처리 → DINO 박스를 fallback `recommended_roi`로 반환
- DINO 감지 없음 → SAM 2 호출 생략 (mock call_count=1 검증)
- ROI 수동 모드는 HTTP 호출 없음 (완전 로컬 계산, no mock 필요)

---

## Step 16 완료 내역

**생성된 파일**:
- `agents/material_lut.py` (신규 생성 — Material LUT: 8가지 재질 × 4개 속성)
- `agents/material_agent.py` (신규 생성 — `MaterialAgent(BaseAgent)`: Florence-2 + DINOv2 원격 클라이언트)
- `tests/test_material_agent.py` (신규 생성 — 41개 테스트, 전부 통과)

**MaterialAgent 인터페이스**:
```python
MaterialAgent(remote_url: str, directive: str = "")
async def run(
    self,
    image: np.ndarray,          # BGR or 2D grayscale
    roi: Optional[dict] = None, # {x1, y1, x2, y2}
    **kwargs,
) -> AgentResult
# status="success", data={"surface_type", "material_map", "confidence", "regions", "feature_stats"}
```

**AgentResult data 필드**:
| 필드 | 타입 | 설명 |
|------|------|------|
| `surface_type` | `str` | 주요 재질 ("metal", "plastic", "glass" 등) |
| `material_map` | `dict` | 영역별 재질 분류 `{"label": {"type", "confidence", "bbox"}}` |
| `confidence` | `float` | 전체 분류 신뢰도 (0.0–1.0) |
| `regions` | `list` | Florence-2 원본 영역 감지 결과 |
| `feature_stats` | `dict` | DINOv2 특징 통계: `{"feature_dim": int, "feature_norm": float, "top_similarities": dict}` |

**Material LUT 재질 목록 및 광학 속성**:
| 재질 | specular | diffuse | roughness |
|------|----------|---------|-----------|
| metal | 0.90 | 0.30 | 0.10 |
| plastic | 0.50 | 0.60 | 0.30 |
| glass | 0.95 | 0.10 | 0.02 |
| rubber | 0.10 | 0.70 | 0.80 |
| ceramic | 0.60 | 0.50 | 0.20 |
| wood | 0.15 | 0.80 | 0.60 |
| fabric | 0.05 | 0.90 | 0.90 |
| paper | 0.10 | 0.85 | 0.70 |

`reference_features`: 384차원 영벡터 (placeholder) — Step 45 Colab 실측값으로 대체 예정

**원격 추론 프로토콜**:
| 모델 | 엔드포인트 | 요청 payload | 응답 |
|------|-----------|-------------|------|
| Florence-2 | `POST {remote_url}/florence2/caption` | `{"image": "<base64 JPEG>"}` | `{"caption": str, "regions": [...]}` |
| DINOv2 | `POST {remote_url}/dinov2/features` | `{"image": "<base64 JPEG>"}` | `{"features": [[float,...]], "shape": [N, D]}` |

- `httpx.AsyncClient` 단일 컨텍스트 내에서 두 모델 순차 호출 (timeout=60s)
- ROI 제공 시 전송 전에 이미지를 ROI 영역으로 크롭
- 모델 로컬 로드 없음 — 모든 추론은 Colab GPU에서만 실행

**에러 처리**:
| 조건 | error_message |
|------|---------------|
| 이미지 < 3×3 | `"Image too small for material analysis"` |
| Florence-2 ConnectError | `"Florence-2 server unreachable: {url}"` |
| DINOv2 ConnectError | `"DINOv2 server unreachable: {url}"` |
| Florence-2 응답 형식 오류 | `"Invalid Florence-2 response format"` |
| DINOv2 응답 형식 오류 | `"Invalid DINOv2 response format"` |
| 양쪽 모두 실패 | Florence-2 에러 메시지 우선 반환 |
| 한쪽만 실패 | `status="success"` (부분 데이터, confidence 0.5 기준) |

**테스트 커버리지**:
| 카테고리 | 테스트 수 |
|---------|---------|
| 클래스 인스턴스화 | 5 |
| AgentResult 구조 검증 | 8 |
| Material LUT 검증 | 4 |
| 코사인 유사도 | 3 |
| Florence-2 원격 호출 | 3 |
| DINOv2 원격 호출 | 3 |
| 결합 분류 동작 | 3 |
| ROI 크롭 | 2 |
| 에러 처리 | 6 |
| 부분 실패 처리 | 2 |
| 그레이스케일 입력 | 1 |
| directive 전달 | 1 |
| **합계** | **41** |

**pytest 결과**: 500 passed (기존 459 + 신규 41), 리그레션 없음

**이슈 및 해결**:
- 없음 (TDD Red→Green 한 사이클로 완료)
- 코사인 유사도에서 영벡터(LUT placeholder) 처리: `norm == 0.0` 가드로 NaN 방지, 유사도 0.0 반환
- Florence-2/DINOv2 두 호출을 단일 `async with httpx.AsyncClient()` 블록 내 순차 처리 → 테스트에서 `side_effect` URL 기반 라우팅으로 두 엔드포인트 독립 모킹

---

## Step 15 완료 내역

**생성된 파일**:
- `agents/depth_agent.py` (신규 생성 — `DepthAgent(BaseAgent)`: 원격 Depth-Anything-V2 클라이언트)
- `tests/test_depth_agent.py` (신규 생성 — 35개 테스트, 전부 통과)

**DepthAgent 인터페이스**:
```python
DepthAgent(remote_url: str, directive: str = "")
async def run(
    self,
    image: np.ndarray,       # BGR or 2D grayscale
    roi: Optional[dict] = None,  # {x1, y1, x2, y2}
    **kwargs,
) -> AgentResult
# data={"depth_map": np.ndarray, "depth_stats": dict}, status="success"
```

**depth_stats 필드 및 계산 방식**:
| 필드 | 계산 방식 |
|------|----------|
| `depth_complexity` | `min(std(depth) × 2, 1.0)` — ROI 내 깊이값 표준편차 정규화 |
| `has_shadow_region` | `depth_gradient_max > 0.3` — Sobel 최대 기울기 임계값 판별 |
| `depth_range` | `max(depth) − min(depth)` — ROI 내 깊이 범위 |
| `depth_mean` | `mean(depth)` — ROI 내 평균 깊이 |
| `depth_gradient_max` | `max(√(Sobel_x² + Sobel_y²))` — 최대 기울기 크기 |

**원격 추론 프로토콜**:
- 요청: `POST {remote_url}/depth` with `{"image": "<base64 JPEG>"}`
- 응답: `{"depth_map": "<base64 float32 bytes>", "shape": [H, W]}`
- 로컬 로드 없음 — 모델은 Colab GPU에서만 실행

**에러 처리**:
- 이미지 크기 < 3×3 → `"Image too small for depth estimation"`
- 서버 연결 실패 → `"Depth server unreachable: {url}"`
- 응답 형식 오류 → `"Invalid depth response format"`

**테스트 커버리지**:
| 카테고리 | 테스트 수 |
|---------|---------|
| 클래스 인스턴스화 | 5 |
| AgentResult 구조 검증 | 6 |
| depth_stats 필드 존재 확인 | 1 |
| depth_complexity 범위/동작 | 3 |
| has_shadow_region 감지 | 2 |
| depth_range 계산 | 2 |
| depth_mean 계산 | 2 |
| depth_gradient_max 계산 | 2 |
| ROI 크롭 적용 | 2 |
| 원격 호출 URL/페이로드 검증 | 2 |
| 에러 처리 (small/unreachable/invalid) | 5 |
| 그레이스케일 입력 처리 | 1 |
| **합계** | **35** |

**pytest 결과**: 459 passed (기존 424 + 신규 35), 리그레션 없음

---

## Step 14 완료 내역

**생성된 파일**:
- `agents/image_analysis_agent.py` (신규 생성 — `ImageAnalysisAgent(BaseAgent)`: 순수 OpenCV 이미지 분석)
- `tests/test_image_analysis.py` (신규 생성 — 49개 테스트, 전부 통과)

**ImageAnalysisAgent 인터페이스**:
```python
ImageAnalysisAgent(directive: str = "")
async def run(
    self,
    image: np.ndarray,      # BGR or 2D grayscale
    roi: Optional[dict] = None,  # {x1, y1, x2, y2}
    **kwargs,
) -> AgentResult
# data={"diagnosis": ImageDiagnosis}, status="success"
```

**계산 메트릭 목록**:
| 필드 | 계산 방식 |
|------|----------|
| `contrast` | 그레이스케일 std / 255 (RMS contrast) |
| `noise_level` | Laplacian variance |
| `edge_density` | Canny 엣지 픽셀 비율 |
| `lighting_uniformity` | 4×4 블록 휘도 평균의 변동계수 (CV) |
| `illumination_type` | CV 임계값 + 중심/외곽 비교 + 위치 상관관계 |
| `noise_frequency` | FFT 에너지 중 고주파 비율 |
| `reflection_level` | 픽셀값 > 230 비율 |
| `blob_feasibility` | clip(contrast × 2, 0, 1) |
| `blob_count_estimate` | Otsu 이진화 + connectedComponents |
| `color_discriminability` | 채널 간 최대 평균 차이 / 128 |
| `dominant_channel_ratio` | max(채널 평균) / sum(채널 평균) |
| `structural_regularity` | 정규화 자기상관 (소규모 이동) |
| `pattern_repetition` | FFT 기반 자기상관 함수 오프센터 피크 |
| `optimal_color_space` | gray / hsv_s / lab_l / bgr 판별 |
| `threshold_candidate` | Otsu 임계값 |
| `edge_sharpness` | 평균 Sobel 기울기 크기 |
| `surface_type` | `""` (Depth/Material Agent 예약) |
| `depth_complexity` | `0.0` (Depth Agent 예약) |
| `has_shadow_region` | `False` (Material Agent 예약) |

**테스트 커버리지**:
| 카테고리 | 테스트 수 |
|---------|---------|
| 클래스 인스턴스화 | 3 |
| AgentResult 구조 검증 | 4 |
| 메트릭 범위 유효성 | 14 |
| illumination_type 분류 | 4 |
| noise_frequency 분류 | 3 |
| 비교 동작 (노이즈/대비) | 3 |
| 그레이스케일 입력 처리 | 3 |
| ROI 크롭 분석 | 2 |
| 엣지 케이스 (1×1, 3×3, 흑/백) | 8 |
| depth/material 기본값 | 3 |
| directive 전달 | 1 |
| optimal_color_space | 2 |
| **합계** | **49** |

**pytest 결과** (전체 424개: 424 passed):
- 신규: 49 passed (test_image_analysis.py)
- 기존 회귀 없음: 375 passed

**이슈 및 해결**:
- 초소형 이미지(1×1, 3×3): Laplacian, Canny, Sobel 등 커널 연산 최소 크기 가드 적용 (`h < 3 or w < 3` 체크)
- 단색 이미지 분모 0: 모든 나눗셈에 `+ 1e-6` 엡실론 추가
- Otsu 실패 케이스: `try/except cv2.error` 처리

---

## Step 13 완료 내역

**생성/수정된 파일**:
- `agents/prompts/spec_prompt.py` (신규 생성 — `build_spec_prompt()` 함수: system/user 프롬프트 쌍 반환)
- `agents/spec_agent.py` (신규 생성 — `SpecAgent(BaseAgent)`: LLM 호출 + JSON 파싱 + `AgentResult` 반환)
- `tests/test_spec_agent.py` (신규 생성 — 38개 테스트, 전부 통과)

**Spec Agent 출력 데이터 구조**:
```python
{
    "mode": "inspection" | "align",
    "goal": str,           # 영문 목표 설명
    "success_criteria": {
        "accuracy":    float | None,
        "fp_rate":     float | None,
        "fn_rate":     float | None,
        "coord_error": float | None,
    },
    "raw_input": str       # 원본 사용자 텍스트
}
```

**프롬프트 템플릿 구조** (`agents/prompts/spec_prompt.py`):
- `build_spec_prompt(user_text, roi=None, directive=None) -> (system_prompt, user_prompt)`
- **system_prompt**: JSON-only 출력 강제, mode/goal/success_criteria/raw_input 스키마 정의, inspection/align 판단 규칙
- **user_prompt**: `"User request: {user_text}"` + ROI 좌표 라인(roi 있을 때만) + `"Additional directive: {directive}"` 라인(directive 있을 때만)

**SpecAgent 인터페이스**:
```python
SpecAgent(
    adapter: BaseAIAdapter,
    model: str = "qwen2.5-coder:7b",
    directive: str = "",
)
async def run(
    self,
    user_text: str,
    roi: dict | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```
- `directive` 우선순위: `run(directive=...)` > 생성자 `directive`
- 에러 시 `AgentResult(status="error", data={}, error_message=..., execution_time_ms=...)`

**JSON 파싱 로직** (`_strip_fences` + `_parse_response`):
- ` ```json ... ``` ` 마크다운 펜스 제거 (정규식)
- ` ``` ... ``` ` 언어 태그 없는 펜스도 제거
- 앞뒤 공백 strip 후 `json.loads()`
- 빈 문자열 → `ValueError("Empty response from adapter")`

**테스트 커버리지**:
| 카테고리 | 테스트 수 |
|---------|---------|
| 클래스 인스턴스화 | 4 |
| 한국어 inspection 요청 | 2 |
| 영어 align 요청 | 2 |
| AgentResult 필드 검증 | 4 |
| JSON 파싱 견고성 | 6 |
| 어댑터 에러 처리 | 2 |
| Directive 주입 | 4 |
| ROI 좌표 포함 | 3 |
| build_spec_prompt 유틸 | 9 |
| 어댑터 호출 검증 | 2 |
| **합계** | **38** |

**pytest 결과** (전체 375개: 375 passed):
```
375 passed in 54.39s
```

**신규 테스트 수**: 38개 (기존 337개 → 375개)

**이슈 및 해결 사항**:
- 없음 (TDD Red→Green 한 사이클로 완료)
- `directive` 우선순위 처리: `run()` 호출 시 `directive=None`은 "명시적으로 비우기"가 아니라 "생성자 값 사용"으로 해석하여 `if directive is not None` 조건으로 구분
- `generate_text()` 첫 번째 위치 인수 = user_prompt (system_prompt는 kwargs): `adapter.generate_text(user_prompt, self.model, system_prompt=system_prompt)` 순서가 `BaseAIAdapter` 시그니처와 일치
- 테스트에서 mock call_args 검증: `call_args.args[0]`(prompt) 또는 `call_args.kwargs["prompt"]` 모두 처리하는 방어적 코드 사용

---

## Step 12 완료 내역

**생성/수정된 파일**:
- `agents/models.py` (신규 생성 — 17개 데이터 모델: 13개 dataclass + 3개 Enum + AgentDirectives)
- `agents/base_agent.py` (신규 생성 — BaseAgent 추상 클래스: run() abstract, logger property, _log() helper)
- `tests/test_models.py` (신규 생성 — 87개 테스트, 전부 통과)

**데이터 모델 목록**:
| 모델 | 종류 | 필드 수 |
|------|------|---------|
| `AgentResult` | dataclass | 4 |
| `ImageDiagnosis` | dataclass | 19 |
| `InspectionItem` | dataclass | 6 |
| `InspectionPlan` | dataclass | 3 (+ `__post_init__`) |
| `JudgementResult` | dataclass | 6 |
| `AgentDirectives` | dataclass | 9 |
| `PipelineBlock` | dataclass | 3 |
| `ProcessingPipeline` | dataclass | 5 |
| `BlueprintNode` | dataclass | 4 |
| `BlueprintEdge` | dataclass | 3 |
| `Blueprint` | dataclass | 5 |
| `SceneContext` | dataclass | 5 |
| `EvaluationResult` | dataclass | 4 |
| `DecisionResult` | dataclass | 5 |
| `AlgorithmCategory` | Enum | 5 members |
| `FailureReason` | Enum | 6 members |
| `DecisionVerdict` | Enum | 4 members |

**BaseAgent 인터페이스**:
- `__init__(name: str, directive: str = "")` — 이름과 선택적 지시문
- `logger` property — `get_agent_logger(name)` BoundLogger 반환
- `_log(level, message, **extra)` — logger에 위임
- `run(**kwargs) -> AgentResult` — 추상 메서드 (서브클래스 구현 필수)

**pytest 결과** (전체 337개: 337 passed):
```
337 passed in 52.23s
```

**신규 테스트 수**: 87개 (전체 250개 → 337개)

**이슈 및 해결 사항**:
- `SceneContext.depth_map`, `material_map`은 numpy array 대응을 위해 `Optional[Any]` 타입 사용 (numpy/cv2/torch import 없음)
- `InspectionPlan.__post_init__`으로 `total_items = len(items)` 자동 계산
- `dataclass` mutable default 문제: list/dict 필드 전부 `field(default_factory=...)` 사용하여 인스턴스 간 공유 방지
- `BaseAgent._logger`를 인스턴스 변수로 저장 후 `logger` property로 노출 (structlog BoundLogger 타입)

---

## Step 11 완료 내역

**생성/수정된 파일**:
- `backend/services/logger.py` (신규 생성 — structlog 기반 에이전트별 로깅 서비스)
- `backend/routers/logs.py` (신규 생성 — GET/GET-agents/DELETE /api/logs 라우터)
- `backend/main.py` (수정 — logs_router를 /api prefix로 등록)
- `requirements.txt` (수정 — structlog>=24.0.0 추가)
- `tests/test_logger.py` (신규 생성 — 40개 테스트, 전부 통과)

**structlog 버전**: 25.5.0

**로그 엔트리 JSON 스키마**:
```json
{
  "timestamp": "2025-05-18T12:00:00.000000Z",
  "agent_name": "spec_agent",
  "level": "info",
  "message": "Processing started",
  "extra": {"input_length": 150}
}
```

**인메모리 버퍼 크기**: 1000 (`collections.deque(maxlen=1000)`, `threading.Lock`으로 thread-safe)

**로그 파일 경로**: `logs/via2.log` (JSON Lines 포맷, 디렉토리 자동 생성)

**API 엔드포인트 목록**:

| 메서드 | 경로 | 상태 코드 | 설명 |
|--------|------|-----------|------|
| `GET` | `/api/logs` | 200 | 로그 조회 (쿼리: agent_name, level, limit) |
| `GET` | `/api/logs/agents` | 200 | 로그가 있는 에이전트 이름 목록 |
| `DELETE` | `/api/logs` | 200 | 로그 초기화 (인메모리 버퍼 + 파일) |

**pytest 결과** (전체 250개: 250 passed):
```
250 passed in 56.79s
```

**신규 테스트 목록 (40개)**:
- `test_get_agent_logger_returns_callable`
- `test_get_agent_logger_different_names_are_independent`
- `test_log_entry_has_required_fields`
- `test_log_entry_agent_name_matches`
- `test_log_entry_level_is_lowercase`
- `test_log_entry_message_matches`
- `test_log_entry_extra_dict_stored`
- `test_log_entry_extra_is_empty_dict_when_no_kwargs`
- `test_log_entry_timestamp_is_iso_string`
- `test_debug_log_is_recorded`
- `test_info_log_is_recorded`
- `test_warning_log_is_recorded`
- `test_error_log_is_recorded`
- `test_get_logs_filter_by_level_returns_only_matching`
- `test_get_logs_filter_by_level_error_excludes_info`
- `test_get_logs_filter_by_agent_name`
- `test_get_logs_compound_filter_agent_and_level`
- `test_get_logs_limit_returns_most_recent`
- `test_get_logs_limit_default_returns_all_up_to_100`
- `test_get_logs_limit_larger_than_buffer_returns_all`
- `test_buffer_max_1000_drops_oldest`
- `test_concurrent_logging_does_not_corrupt_buffer`
- `test_clear_logs_empties_buffer`
- `test_log_file_is_created_on_first_log`
- `test_log_file_contains_json_lines`
- `test_clear_logs_truncates_log_file`
- `test_get_agent_names_returns_unique_names`
- `test_get_agent_names_empty_when_no_logs`
- `test_api_get_logs_returns_200`
- `test_api_get_logs_empty_initially`
- `test_api_get_logs_returns_logged_entries`
- `test_api_get_logs_filter_by_agent_name`
- `test_api_get_logs_filter_by_level`
- `test_api_get_logs_limit_param`
- `test_api_get_logs_agents_returns_200`
- `test_api_get_logs_agents_empty_initially`
- `test_api_get_logs_agents_lists_agent_names`
- `test_api_delete_logs_returns_200`
- `test_api_delete_logs_clears_buffer`
- `test_api_delete_logs_response_has_cleared_field`

**이슈 및 해결 사항**:
- structlog의 `DropEvent`를 마지막 프로세서에서 raise하여 stdout 출력을 차단하고 인메모리 버퍼와 파일 쓰기만 수행
- `cache_logger_on_first_use=False`로 설정하여 테스트 간 프로세서 체인 재사용 문제 방지
- `GET /api/logs/agents`를 `GET /api/logs` 보다 먼저 등록하여 FastAPI 라우트 매칭 순서 보장
- `configure_log_file()` 함수를 테스트 전용 유틸로 추가하여 각 테스트가 독립적인 tmp_path에 로그 파일을 기록하도록 격리

---

## Step 10 완료 내역

**생성/수정된 파일**:
- `backend/models/roi.py` (신규 생성 — ROICoordinates Pydantic 모델, 좌표 유효성 검사)
- `backend/models/config.py` (신규 생성 — SuccessCriteria + InspectionConfig Pydantic 모델)
- `backend/models/directives.py` (신규 생성 — AgentDirectives Pydantic 모델)
- `backend/services/roi_store.py` (신규 생성 — thread-safe 인메모리 ROI 저장소)
- `backend/services/config_store.py` (신규 생성 — thread-safe 인메모리 Config 저장소)
- `backend/services/directives_store.py` (신규 생성 — thread-safe 인메모리 Directives 저장소)
- `backend/routers/roi.py` (신규 생성 — GET/POST/DELETE /api/roi 라우터)
- `backend/routers/config.py` (신규 생성 — GET/POST /api/config 라우터, 경고 로직 포함)
- `backend/routers/directives.py` (신규 생성 — GET/POST /api/directives 라우터)
- `backend/main.py` (수정 — roi_router, config_router, directives_router를 /api prefix로 등록)
- `tests/test_settings_api.py` (신규 생성 — 64개 테스트, 전부 통과)

**pytest 결과** (전체 210개: 205 passed, 5 skipped):
```
205 passed, 5 skipped in 3.92s
tests/test_settings_api.py::test_roi_model_valid_coordinates_accepted PASSED
tests/test_settings_api.py::test_roi_model_x1_equal_x2_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_x1_greater_than_x2_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_y1_equal_y2_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_y1_greater_than_y2_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_negative_x1_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_negative_y1_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_negative_x2_raises_validation_error PASSED
tests/test_settings_api.py::test_roi_model_all_zero_except_positive_x2_y2_is_valid PASSED
tests/test_settings_api.py::test_roi_store_initially_returns_none PASSED
tests/test_settings_api.py::test_roi_store_set_and_get_returns_roi PASSED
tests/test_settings_api.py::test_roi_store_clear_resets_to_none PASSED
tests/test_settings_api.py::test_get_roi_when_not_set_returns_null PASSED
tests/test_settings_api.py::test_post_roi_valid_coordinates_returns_200 PASSED
tests/test_settings_api.py::test_post_roi_persists_and_get_returns_it PASSED
tests/test_settings_api.py::test_post_roi_x1_equal_x2_returns_422 PASSED
tests/test_settings_api.py::test_post_roi_x1_greater_than_x2_returns_422 PASSED
tests/test_settings_api.py::test_post_roi_y1_greater_than_y2_returns_422 PASSED
tests/test_settings_api.py::test_post_roi_negative_x1_returns_422 PASSED
tests/test_settings_api.py::test_delete_roi_clears_and_get_returns_null PASSED
tests/test_settings_api.py::test_delete_roi_returns_200 PASSED
tests/test_settings_api.py::test_config_model_default_mode_is_inspection PASSED
tests/test_settings_api.py::test_config_model_default_max_iteration_is_3 PASSED
tests/test_settings_api.py::test_config_model_default_success_criteria_fields_are_none PASSED
tests/test_settings_api.py::test_config_model_mode_align_is_valid PASSED
tests/test_settings_api.py::test_config_model_invalid_mode_raises_validation_error PASSED
tests/test_settings_api.py::test_config_model_max_iteration_1_is_valid PASSED
tests/test_settings_api.py::test_config_model_max_iteration_10_is_valid PASSED
tests/test_settings_api.py::test_config_model_max_iteration_0_raises_validation_error PASSED
tests/test_settings_api.py::test_config_model_max_iteration_11_raises_validation_error PASSED
tests/test_settings_api.py::test_config_model_accuracy_1_0_is_valid PASSED
tests/test_settings_api.py::test_config_model_accuracy_above_1_raises_validation_error PASSED
tests/test_settings_api.py::test_config_model_accuracy_below_0_raises_validation_error PASSED
tests/test_settings_api.py::test_config_model_fp_rate_0_0_is_valid PASSED
tests/test_settings_api.py::test_config_model_coord_error_0_is_valid PASSED
tests/test_settings_api.py::test_config_model_coord_error_negative_raises_validation_error PASSED
tests/test_settings_api.py::test_config_store_returns_default_config PASSED
tests/test_settings_api.py::test_config_store_update_and_get_returns_updated PASSED
tests/test_settings_api.py::test_config_store_reset_returns_defaults PASSED
tests/test_settings_api.py::test_get_config_returns_200_with_defaults PASSED
tests/test_settings_api.py::test_post_config_valid_payload_returns_200 PASSED
tests/test_settings_api.py::test_post_config_persists_to_get PASSED
tests/test_settings_api.py::test_post_config_invalid_mode_returns_422 PASSED
tests/test_settings_api.py::test_post_config_max_iteration_0_returns_422 PASSED
tests/test_settings_api.py::test_post_config_max_iteration_11_returns_422 PASSED
tests/test_settings_api.py::test_post_config_accuracy_above_099_triggers_warning PASSED
tests/test_settings_api.py::test_post_config_accuracy_exactly_099_no_warning PASSED
tests/test_settings_api.py::test_post_config_fp_rate_below_0005_triggers_warning PASSED
tests/test_settings_api.py::test_post_config_fp_rate_exactly_0005_no_warning PASSED
tests/test_settings_api.py::test_post_config_fn_rate_below_0005_triggers_warning PASSED
tests/test_settings_api.py::test_post_config_coord_error_below_05_triggers_warning PASSED
tests/test_settings_api.py::test_post_config_coord_error_exactly_05_no_warning PASSED
tests/test_settings_api.py::test_post_config_all_extreme_goals_triggers_all_warnings PASSED
tests/test_settings_api.py::test_post_config_no_extreme_goals_no_warnings_field PASSED
tests/test_settings_api.py::test_get_config_has_no_warnings_field PASSED
tests/test_settings_api.py::test_directives_model_default_all_fields_empty_string PASSED
tests/test_settings_api.py::test_directives_model_accepts_custom_values PASSED
tests/test_settings_api.py::test_directives_store_returns_default_empty_strings PASSED
tests/test_settings_api.py::test_directives_store_update_and_get_returns_updated PASSED
tests/test_settings_api.py::test_directives_store_reset_returns_defaults PASSED
tests/test_settings_api.py::test_get_directives_returns_200_with_empty_defaults PASSED
tests/test_settings_api.py::test_post_directives_saves_and_get_returns_updated PASSED
tests/test_settings_api.py::test_post_directives_partial_update_preserves_other_defaults PASSED
tests/test_settings_api.py::test_post_directives_all_fields_saved PASSED
(기존 141 passed, 5 skipped — 회귀 없음)
```

**ROICoordinates 모델 필드 상세**:
| 필드 | 타입 | 검증 규칙 |
|------|------|----------|
| `x1` | `int` | `>= 0`, `x1 < x2` |
| `y1` | `int` | `>= 0`, `y1 < y2` |
| `x2` | `int` | `>= 0` |
| `y2` | `int` | `>= 0` |

**InspectionConfig 모델 필드 상세**:
| 필드 | 타입 | 기본값 | 검증 규칙 |
|------|------|--------|----------|
| `mode` | `Literal["inspection","align"]` | `"inspection"` | 두 값 중 하나 |
| `max_iteration` | `int` | `3` | 1 ≤ x ≤ 10 |
| `success_criteria` | `SuccessCriteria` | 모든 필드 None | 서브 모델 |
| `success_criteria.accuracy` | `Optional[float]` | `None` | 0.0 ≤ x ≤ 1.0 |
| `success_criteria.fp_rate` | `Optional[float]` | `None` | 0.0 ≤ x ≤ 1.0 |
| `success_criteria.fn_rate` | `Optional[float]` | `None` | 0.0 ≤ x ≤ 1.0 |
| `success_criteria.coord_error` | `Optional[float]` | `None` | x ≥ 0.0 |

**Config 경고 로직 (POST /api/config 전용)**:
| 조건 | 경고 메시지 |
|------|------------|
| `accuracy > 0.99` | "Accuracy above 99% is extremely difficult to achieve with rule-based methods" |
| `fp_rate < 0.005` | "FP rate below 0.5% may require deep learning approaches" |
| `fn_rate < 0.005` | "FN rate below 0.5% may require deep learning approaches" |
| `coord_error < 0.5` | "Coordinate error below 0.5px may require sub-pixel algorithms or hardware upgrade" |

- GET /api/config는 `warnings` 필드 없이 `InspectionConfig`만 반환
- POST /api/config는 항상 `warnings` 필드 포함 (해당 없으면 빈 리스트)

**AgentDirectives 모델 필드 상세**:
| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `orchestrator` | `str` | `""` | 오케스트레이터 에이전트 지시 |
| `spec` | `str` | `""` | Spec 에이전트 지시 |
| `image_analysis` | `str` | `""` | 이미지 분석 에이전트 지시 |
| `depth` | `str` | `""` | Depth 에이전트 지시 |
| `material` | `str` | `""` | Material 에이전트 지시 |
| `pipeline_composer` | `str` | `""` | Pipeline Composer 에이전트 지시 |
| `vision_judge` | `str` | `""` | Vision Judge 에이전트 지시 |
| `inspection_plan` | `str` | `""` | Inspection Plan 에이전트 지시 |
| `test` | `str` | `""` | Test 에이전트 지시 |

**API 엔드포인트 목록**:

| 메서드 | 경로 | 상태 코드 | 설명 |
|--------|------|-----------|------|
| `POST` | `/api/roi` | 200 / 422 | ROI 좌표 저장, ROICoordinates 반환 |
| `GET` | `/api/roi` | 200 | 현재 ROI 조회 (미설정 시 null) |
| `DELETE` | `/api/roi` | 200 | ROI 초기화 |
| `POST` | `/api/config` | 200 / 422 | 검사 설정 저장, 경고 포함 응답 |
| `GET` | `/api/config` | 200 | 현재 설정 조회 (경고 없음) |
| `POST` | `/api/directives` | 200 | 에이전트 지시 저장 |
| `GET` | `/api/directives` | 200 | 현재 지시 조회 |

**이슈 및 해결 사항**:
- `GET /api/roi` 미설정 시 `null` 반환: FastAPI의 `Optional[ROICoordinates]` 반환 타입 선언만으로 자동 처리됨.
- Config 경고는 `GET`에서는 불필요하므로 `POST` 라우터에서만 `_build_warnings()` 로직 적용. `GET`은 순수 `InspectionConfig` 모델 반환.
- 테스트 격리: `autouse=True` 픽스처에서 3개 스토어 모두 reset → 각 테스트 독립 실행 보장.

---

## Step 9 완료 내역

**생성/수정된 파일**:
- `backend/models/image.py` (신규 생성 — ImageMetadata Pydantic 모델)
- `backend/services/image_validator.py` (신규 생성 — validate_filename, validate_content_type)
- `backend/services/image_store.py` (신규 생성 — thread-safe 인메모리 이미지 저장소)
- `backend/routers/images.py` (신규 생성 — 이미지 업로드/조회/삭제 라우터)
- `backend/main.py` (수정 — images_router를 /api prefix로 등록)
- `tests/test_image_api.py` (신규 생성 — 60개 테스트, 전부 통과)

**pytest 결과** (전체 146개: 141 passed, 5 skipped):
```
141 passed, 5 skipped in 4.16s
tests/test_image_api.py::test_validate_ok_1_png_returns_valid_with_label_ok_index_1 PASSED
tests/test_image_api.py::test_validate_ok_2_jpg_returns_valid PASSED
tests/test_image_api.py::test_validate_ng_1_jpeg_returns_valid_with_label_ng PASSED
tests/test_image_api.py::test_validate_lowercase_prefix_normalized_to_uppercase PASSED
tests/test_image_api.py::test_validate_lowercase_ng_with_large_index PASSED
tests/test_image_api.py::test_validate_uppercase_extension_is_valid PASSED
tests/test_image_api.py::test_validate_bmp_extension_is_valid PASSED
tests/test_image_api.py::test_validate_tiff_extension_with_index PASSED
tests/test_image_api.py::test_validate_multi_digit_index_is_valid PASSED
tests/test_image_api.py::test_validate_arbitrary_name_is_invalid PASSED
tests/test_image_api.py::test_validate_ok_without_underscore_number_is_invalid PASSED
tests/test_image_api.py::test_validate_zero_index_is_invalid PASSED
tests/test_image_api.py::test_validate_negative_index_is_invalid PASSED
tests/test_image_api.py::test_validate_empty_number_after_underscore_is_invalid PASSED
tests/test_image_api.py::test_validate_gif_extension_is_invalid PASSED
tests/test_image_api.py::test_validate_filename_without_extension_is_invalid PASSED
tests/test_image_api.py::test_validate_double_extension_is_invalid PASSED
tests/test_image_api.py::test_content_type_image_png_is_valid PASSED
tests/test_image_api.py::test_content_type_image_jpeg_is_valid PASSED
tests/test_image_api.py::test_content_type_image_bmp_is_valid PASSED
tests/test_image_api.py::test_content_type_image_tiff_is_valid PASSED
tests/test_image_api.py::test_content_type_application_pdf_is_invalid PASSED
tests/test_image_api.py::test_content_type_text_plain_is_invalid PASSED
tests/test_image_api.py::test_content_type_none_is_invalid PASSED
tests/test_image_api.py::test_image_store_add_returns_metadata_with_all_fields PASSED
tests/test_image_api.py::test_image_store_file_is_written_to_disk PASSED
tests/test_image_api.py::test_image_store_get_by_id_returns_correct_metadata PASSED
tests/test_image_api.py::test_image_store_get_by_id_returns_none_for_unknown PASSED
tests/test_image_api.py::test_image_store_get_all_returns_all_uploaded_images PASSED
tests/test_image_api.py::test_image_store_delete_removes_metadata PASSED
tests/test_image_api.py::test_image_store_delete_removes_file_from_disk PASSED
tests/test_image_api.py::test_image_store_delete_returns_false_for_unknown_id PASSED
tests/test_image_api.py::test_image_store_clear_all_empties_store PASSED
tests/test_image_api.py::test_ok1_is_classified_as_analysis_group PASSED
tests/test_image_api.py::test_ng1_is_classified_as_analysis_group PASSED
tests/test_image_api.py::test_ok2_is_classified_as_test_group PASSED
tests/test_image_api.py::test_ng2_is_classified_as_test_group PASSED
tests/test_image_api.py::test_ok10_is_classified_as_test_group PASSED
tests/test_image_api.py::test_get_by_group_analysis_contains_exactly_ok1_and_ng1 PASSED
tests/test_image_api.py::test_get_by_group_test_excludes_ok1_and_ng1 PASSED
tests/test_image_api.py::test_ok1_overwrite_keeps_only_one_ok1 PASSED
tests/test_image_api.py::test_ok1_overwrite_deletes_old_file_from_disk PASSED
tests/test_image_api.py::test_upload_valid_image_returns_201 PASSED
tests/test_image_api.py::test_upload_returns_metadata_with_correct_fields PASSED
tests/test_image_api.py::test_upload_invalid_filename_returns_422 PASSED
tests/test_image_api.py::test_upload_invalid_content_type_returns_422 PASSED
tests/test_image_api.py::test_list_all_images_returns_200_with_list PASSED
tests/test_image_api.py::test_list_all_images_returns_uploaded_images PASSED
tests/test_image_api.py::test_list_images_by_analysis_group_returns_only_ok1_ng1 PASSED
tests/test_image_api.py::test_list_images_by_test_group_excludes_index1 PASSED
tests/test_image_api.py::test_get_image_by_id_returns_200_with_metadata PASSED
tests/test_image_api.py::test_get_image_by_unknown_id_returns_404 PASSED
tests/test_image_api.py::test_delete_image_by_id_returns_200 PASSED
tests/test_image_api.py::test_delete_image_by_id_removes_from_list PASSED
tests/test_image_api.py::test_delete_image_by_unknown_id_returns_404 PASSED
tests/test_image_api.py::test_clear_all_images_returns_200 PASSED
tests/test_image_api.py::test_clear_all_images_empties_the_list PASSED
tests/test_image_api.py::test_upload_ok1_twice_overwrites_first_upload PASSED
tests/test_image_api.py::test_upload_ng1_is_in_analysis_group PASSED
tests/test_image_api.py::test_upload_ok2_is_in_test_group PASSED
(기존 81 passed, 5 skipped — 회귀 없음)
```

**ImageValidator 검증 규칙 상세**:

파일명 패턴: `^(ok|ng)_([1-9]\d*)\.(png|jpg|jpeg|bmp|tiff)$` (case-insensitive)

| 항목 | 규칙 |
|------|------|
| 접두사 | `OK` 또는 `NG` (대소문자 무관, 결과는 대문자 정규화) |
| 구분자 | `_` (언더스코어) |
| 인덱스 | 양의 정수 (1 이상, 0·음수·빈값 불가) |
| 확장자 | `png`, `jpg`, `jpeg`, `bmp`, `tiff` (대소문자 무관) |
| 이중 확장자 | `OK_1.png.exe` 같은 형식 거부 (`$` 앵커로 처리) |

유효한 MIME 타입: `image/png`, `image/jpeg`, `image/bmp`, `image/tiff`, `image/x-bmp`

**ImageStore 분류 로직 상세 (analysis vs test)**:

| 조건 | 그룹 |
|------|------|
| `index == 1` (OK_1 또는 NG_1) | `analysis` — 알고리즘 설계용 기준 이미지 |
| `index >= 2` (OK_2, NG_2, ...) | `test` — 알고리즘 테스트용 이미지 |

덮어쓰기 규칙: 동일한 `(label, index)` 쌍 재업로드 시 기존 파일과 메타데이터를 삭제하고 새 항목으로 교체.

**API 엔드포인트 목록과 응답 형식**:

| 메서드 | 경로 | 상태 코드 | 설명 |
|--------|------|-----------|------|
| `POST` | `/api/images/upload` | 201 | multipart 파일 업로드, ImageMetadata 반환 |
| `GET` | `/api/images` | 200 | 전체 이미지 목록 (옵션: `?group=analysis\|test`) |
| `GET` | `/api/images/{image_id}` | 200 / 404 | 단일 이미지 메타데이터 조회 |
| `DELETE` | `/api/images/{image_id}` | 200 / 404 | 이미지 삭제 (파일 + 메타데이터) |
| `DELETE` | `/api/images` | 200 | 전체 이미지 초기화 |

ImageMetadata 응답 필드: `id`, `original_filename`, `label`, `index`, `file_size`, `upload_timestamp`, `file_path`, `group`

**이슈 및 해결 사항**:
- `DELETE /api/images`와 `DELETE /api/images/{image_id}` 라우트 순서: FastAPI는 비파라미터 경로를 우선 매칭하므로 `/images`를 `/{image_id}` 앞에 선언하여 정확한 라우팅 보장.
- 테스트 격리: `autouse=True` 픽스처에서 `tmp_path`를 주입받아 `configure_upload_dir(tmp_path/uploads)` 호출 후 `clear_all()` 실행 → 각 테스트가 독립적인 파일 시스템 환경에서 실행됨.
- `validate_content_type(None)` 처리: `None in _VALID_MIME_TYPES`는 `False`를 반환하므로 별도 None 체크 불필요.

---

## Step 8 완료 내역

**생성/수정된 파일**:
- `backend/models/engine.py` (신규 생성 — EngineMode enum + EngineSettings Pydantic 모델)
- `backend/services/engine_store.py` (신규 생성 — thread-safe 인메모리 설정 저장소)
- `backend/routers/engine.py` (신규 생성 — GET/POST /api/engine 라우터)
- `backend/services/ai_adapter/factory.py` (신규 생성 — create_adapter + get_current_adapter)
- `backend/main.py` (수정 — engine_router를 /api prefix로 등록)
- `backend/services/ai_adapter/__init__.py` (수정 — create_adapter, get_current_adapter export 추가)
- `tests/test_engine_api.py` (신규 생성 — 10개 테스트, 전부 통과)

**pytest 결과** (전체 86개: 81 passed, 5 skipped):
```
81 passed, 5 skipped in 3.46s
tests/test_engine_api.py::test_get_engine_returns_default_settings PASSED
tests/test_engine_api.py::test_post_engine_local_mode_succeeds PASSED
tests/test_engine_api.py::test_post_engine_remote_mode_with_url_succeeds PASSED
tests/test_engine_api.py::test_post_engine_remote_mode_missing_url_returns_422 PASSED
tests/test_engine_api.py::test_post_engine_updates_persist_to_get PASSED
tests/test_engine_api.py::test_post_engine_invalid_mode_returns_422 PASSED
tests/test_engine_api.py::test_factory_creates_ollama_adapter_for_local_mode PASSED
tests/test_engine_api.py::test_factory_creates_remote_adapter_for_remote_mode PASSED
tests/test_engine_api.py::test_get_current_adapter_returns_adapter_matching_current_settings PASSED
tests/test_engine_api.py::test_engine_settings_model_default_values PASSED
(기존 71 passed, 5 skipped — 회귀 없음)
```

**EngineSettings 모델 필드 상세**:
| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `mode` | `EngineMode` | `"local"` | 엔진 실행 모드 |
| `local_ollama_url` | `str` | `"http://127.0.0.1:11434"` | 로컬 Ollama 서버 주소 |
| `remote_url` | `str \| None` | `None` | 원격 AI 서버 URL |
| `remote_type` | `str` | `"colab"` | 원격 서버 종류 (colab/azure/custom) |
| `remote_auth_token` | `str \| None` | `None` | 원격 서버 Bearer 토큰 |
| `model_name` | `str` | `"qwen2.5-coder:7b"` | 사용할 모델명 |

**Pydantic 유효성 검사**: `mode == "remote"` 이고 `remote_url`이 None/비어있으면 422 반환 (`@model_validator(mode="after")`)

**Factory 동작 상세**:
| `mode` | 반환 어댑터 | 생성자 인수 |
|--------|------------|------------|
| `"local"` | `OllamaAdapter` | `base_url=settings.local_ollama_url` |
| `"remote"` | `RemoteAdapter` | `base_url=settings.remote_url, auth_token=settings.remote_auth_token` |

- `create_adapter(settings)`: EngineSettings를 받아 적절한 어댑터 인스턴스 반환
- `get_current_adapter()`: engine_store에서 현재 설정을 읽어 어댑터 생성 후 반환
- 주의: `OllamaAdapter`는 `model` 파라미터 없음 (model은 각 메서드 호출 시 전달) — 실제 생성자 시그니처 확인 후 반영

**이슈 및 해결 사항**: 없음 (TDD Red→Green 한 사이클로 완료)

---

## Step 7 완료 내역

**설치/추가된 패키지**: 없음 (httpx, asyncio 모두 기존 환경에 포함됨)

**생성/수정된 파일**:
- `backend/services/ai_adapter/remote_adapter.py` (신규 생성 — RemoteAdapter 구현체)
- `backend/services/ai_adapter/__init__.py` (수정 — RemoteAdapter 추가 export)
- `tests/test_remote_adapter.py` (신규 생성 — 27개 테스트, 전부 통과)

**pytest 결과** (전체 76개: 71 passed, 5 skipped):
```
71 passed, 5 skipped in 2.29s
tests/test_remote_adapter.py::test_remote_adapter_is_subclass_of_base PASSED
tests/test_remote_adapter.py::test_remote_adapter_implements_all_abstract_methods PASSED
tests/test_remote_adapter.py::test_name_property_returns_remote PASSED
tests/test_remote_adapter.py::test_constructor_stores_base_url PASSED
tests/test_remote_adapter.py::test_constructor_stores_auth_token PASSED
tests/test_remote_adapter.py::test_constructor_stores_timeout PASSED
tests/test_remote_adapter.py::test_constructor_defaults_auth_token_to_none PASSED
tests/test_remote_adapter.py::test_constructor_defaults_timeout_to_300 PASSED
tests/test_remote_adapter.py::test_generate_text_returns_response_string PASSED
tests/test_remote_adapter.py::test_generate_text_sends_correct_payload PASSED
tests/test_remote_adapter.py::test_generate_text_includes_auth_header_when_token_provided PASSED
tests/test_remote_adapter.py::test_generate_text_no_auth_header_when_no_token PASSED
tests/test_remote_adapter.py::test_generate_json_sends_format_json_in_payload PASSED
tests/test_remote_adapter.py::test_generate_json_returns_parsed_dict PASSED
tests/test_remote_adapter.py::test_generate_json_raises_value_error_on_invalid_json PASSED
tests/test_remote_adapter.py::test_analyze_image_returns_response_string PASSED
tests/test_remote_adapter.py::test_analyze_image_sends_base64_encoded_image PASSED
tests/test_remote_adapter.py::test_health_check_returns_true_on_200 PASSED
tests/test_remote_adapter.py::test_health_check_returns_false_on_non_200 PASSED
tests/test_remote_adapter.py::test_health_check_returns_false_on_connect_error PASSED
tests/test_remote_adapter.py::test_health_check_uses_short_timeout PASSED
tests/test_remote_adapter.py::test_retry_on_5xx_succeeds_after_two_failures PASSED
tests/test_remote_adapter.py::test_retry_on_5xx_raises_runtime_error_after_max_retries PASSED
tests/test_remote_adapter.py::test_retry_on_timeout_raises_timeout_error_after_max_retries PASSED
tests/test_remote_adapter.py::test_no_retry_on_4xx_raises_runtime_error_immediately PASSED
tests/test_remote_adapter.py::test_retry_uses_exponential_backoff PASSED
tests/test_remote_adapter.py::test_connect_error_raises_connection_error_with_url PASSED
(기존 44 passed, 5 skipped — 회귀 없음)
```

**이슈 및 해결 사항**: 없음 (TDD Red→Green 한 사이클로 완료)

**RemoteAdapter 생성자 시그니처**:
```python
RemoteAdapter(base_url: str, auth_token: str | None = None, timeout: float = 300.0)
```
- `base_url`: Colab/Azure/커스텀 엔드포인트 URL (예: `https://xxx.ngrok.io`)
- `auth_token`: 선택적 Bearer 토큰 — 전달 시 모든 요청 헤더에 `Authorization: Bearer {token}` 추가
- `timeout`: 기본 300.0초 (Colab cold start 대응), health_check는 15.0초 고정

**RemoteAdapter 구현 상세**:
- **엔드포인트**: `POST {base_url}/generate`, `GET {base_url}/health`
- **내부 `_post(payload)` 헬퍼**: generate_text/generate_json/analyze_image 공유 사용
- `generate_json`: payload에 `"format": "json"` 추가, response 필드를 `json.loads()`로 파싱
- `analyze_image`: image_data를 `base64.b64encode().decode("utf-8")`해서 `"images": [b64]`로 전송

**재시도 로직**:
- 최대 재시도 횟수: 2회 (총 3회 시도)
- 재시도 트리거: HTTP 5xx 응답, `httpx.TimeoutException`
- 백오프 간격: 1초 → 2초 (`asyncio.sleep` 사용)
- 재시도 없음: HTTP 4xx 응답, `httpx.ConnectError`

**에러 핸들링 매핑**:
| 원인 | 발생 예외 |
|------|----------|
| `httpx.TimeoutException` (재시도 소진) | `TimeoutError("Remote AI server request timed out")` |
| `httpx.ConnectError` | `ConnectionError("Cannot connect to remote AI server: {base_url}")` |
| HTTP 5xx (재시도 소진) | `RuntimeError("Remote AI server error: {status_code}")` |
| HTTP 4xx (즉시) | `RuntimeError("Remote AI server error: {status_code}")` |
| 잘못된 JSON 응답 (generate_json) | `ValueError("Invalid JSON response from remote AI: ...")` |

---

## Step 6 완료 내역

**설치된 패키지 버전** (pyenv Python 3.11.15):
- `httpx` 0.28.1 (이미 설치됨 — requirements.txt에 `httpx>=0.27.0` 추가)

**생성/수정된 파일**:
- `backend/services/ai_adapter/__init__.py` (신규 생성 — 패키지 init, BaseAIAdapter·OllamaAdapter 외부 노출)
- `backend/services/ai_adapter/base.py` (신규 생성 — 추상 기반 클래스 BaseAIAdapter: 4개 abstract 메서드 + name 프로퍼티)
- `backend/services/ai_adapter/ollama_adapter.py` (신규 생성 — OllamaAdapter 구현체: httpx AsyncClient로 Ollama REST API 호출)
- `tests/test_ollama_adapter.py` (신규 생성 — 17개 테스트: 16 passed + 1 skipped(integration))
- `requirements.txt` (`httpx>=0.27.0` 추가)
- `pyproject.toml` (`markers = ["integration: ..."]` 등록으로 PytestUnknownMarkWarning 제거)

**pytest 결과** (전체 49개: 44 passed, 5 skipped):
```
44 passed, 5 skipped in 2.06s
tests/test_api_health.py::test_health_endpoint_returns_200 PASSED
tests/test_api_health.py::test_health_response_status_is_ok PASSED
tests/test_api_health.py::test_health_response_contains_version PASSED
tests/test_api_health.py::test_cors_headers_present_on_health PASSED
tests/test_libraries.py::test_opencv_import PASSED
tests/test_libraries.py::test_numpy_import PASSED
tests/test_libraries.py::test_torch_import PASSED
tests/test_libraries.py::test_opencv_image_operations PASSED
tests/test_libraries.py::test_torch_tensor_operations PASSED
tests/test_libraries.py::test_opencv_basic_processing PASSED
tests/test_libraries.py::test_numpy_opencv_interop PASSED
tests/test_model_loading.py::test_generate_colab_notebook_script_exists PASSED
tests/test_model_loading.py::test_verify_vision_models_notebook_exists PASSED
tests/test_model_loading.py::test_model_setup_doc_exists PASSED
tests/test_model_loading.py::test_generate_script_valid_python_syntax PASSED
tests/test_model_loading.py::test_model_setup_doc_contains_all_model_sections PASSED
tests/test_model_loading.py::test_notebook_is_valid_nbformat PASSED
tests/test_model_loading.py::test_notebook_has_minimum_15_cells PASSED
tests/test_model_loading.py::test_notebook_code_cells_contain_all_model_names PASSED
tests/test_ollama.py::test_ollama_is_running SKIPPED (Ollama 서버 미실행)
tests/test_ollama.py::test_qwen_coder_model_exists SKIPPED (Ollama 서버 미실행)
tests/test_ollama.py::test_text_generation SKIPPED (Ollama 서버 미실행)
tests/test_ollama.py::test_json_output_parsing SKIPPED (Ollama 서버 미실행)
tests/test_ollama_adapter.py::test_base_ai_adapter_cannot_be_instantiated_directly PASSED
tests/test_ollama_adapter.py::test_ollama_adapter_is_a_subclass_of_base PASSED
tests/test_ollama_adapter.py::test_ollama_adapter_implements_all_abstract_methods PASSED
tests/test_ollama_adapter.py::test_ollama_adapter_name_property_returns_ollama PASSED
tests/test_ollama_adapter.py::test_default_base_url_is_localhost_11434 PASSED
tests/test_ollama_adapter.py::test_custom_base_url_is_stored PASSED
tests/test_ollama_adapter.py::test_custom_timeout_is_stored PASSED
tests/test_ollama_adapter.py::test_generate_text_returns_response_string PASSED
tests/test_ollama_adapter.py::test_generate_text_payload_contains_model_prompt_and_stream_false PASSED
tests/test_ollama_adapter.py::test_generate_json_returns_parsed_dict PASSED
tests/test_ollama_adapter.py::test_generate_json_raises_value_error_on_invalid_json_response PASSED
tests/test_ollama_adapter.py::test_analyze_image_returns_description_string PASSED
tests/test_ollama_adapter.py::test_analyze_image_encodes_image_as_base64_in_payload PASSED
tests/test_ollama_adapter.py::test_health_check_returns_true_when_ollama_responds_200 PASSED
tests/test_ollama_adapter.py::test_health_check_returns_false_on_connection_error PASSED
tests/test_ollama_adapter.py::test_generate_text_raises_timeout_error_on_httpx_timeout PASSED
tests/test_ollama_adapter.py::test_integration_generate_text_with_qwen_coder SKIPPED (Ollama 미실행)
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

**이슈 및 해결 사항**:
- `@pytest.mark.integration` 사용 시 `PytestUnknownMarkWarning` 발생 → `pyproject.toml`의 `[tool.pytest.ini_options]`에 `markers` 항목 추가로 해결

**BaseAIAdapter 인터페이스 메서드 목록**:
| 메서드 | 시그니처 | 설명 |
|--------|---------|------|
| `name` | `@property → str` | 어댑터 이름 반환 |
| `generate_text` | `(prompt, model, system_prompt=None, temperature=0.7, max_tokens=2048) → str` | 텍스트 생성 |
| `generate_json` | `(prompt, model, schema=None, system_prompt=None) → dict` | JSON 구조 생성 |
| `analyze_image` | `(image_data: bytes, prompt, model) → str` | 멀티모달 이미지 분석 (VLM) |
| `health_check` | `() → bool` | 어댑터 백엔드 가용성 확인 |

**OllamaAdapter 구현 상세**:
- **기본 URL**: `http://127.0.0.1:11434` (설정 가능)
- **기본 타임아웃**: 120.0초 (Intel Mac 느린 추론 대응), health_check는 10.0초 고정
- **API 엔드포인트**:
  - `generate_text` / `generate_json` / `analyze_image`: `POST /api/generate` (stream=false)
  - `health_check`: `GET /api/tags`
- **JSON 모드**: `generate_json`은 `format="json"` 전달 → 응답을 `json.loads()` 파싱
- **이미지 전송**: `analyze_image`는 `base64.b64encode(image_data)` → `images: [b64_str]`
- **에러 처리**:
  - `httpx.TimeoutException` → Python 내장 `TimeoutError` 로 변환 (re-raise)
  - `httpx.ConnectError` → `health_check`에서 `False` 반환
  - 잘못된 JSON 응답 → `ValueError("Invalid JSON response from Ollama: ...")`

---

## Step 5 완료 내역

**설치된 패키지 버전** (pyenv Python 3.11.15):
- `fastapi` 0.136.1
- `uvicorn` 0.46.0 (with standard extras)
- `starlette` 1.0.0 (fastapi 의존성으로 자동 설치)
- `pydantic-settings` 2.13.1 (이미 설치됨)

**생성/수정된 파일**:
- `tests/test_api_health.py` (신규 생성 — 4개 비동기 테스트: 상태코드 200, status ok, version 포함, CORS 헤더)
- `backend/main.py` (placeholder → FastAPI 앱: CORSMiddleware + GET /health)
- `backend/config.py` (placeholder → pydantic-settings BaseSettings: app_name, version, debug, host, port)
- `requirements.txt` (fastapi>=0.111.0, uvicorn[standard]>=0.29.0 추가)

**pytest 결과** (전체 32개):
```
32 passed in 38.44s
tests/test_api_health.py::test_health_endpoint_returns_200 PASSED
tests/test_api_health.py::test_health_response_status_is_ok PASSED
tests/test_api_health.py::test_health_response_contains_version PASSED
tests/test_api_health.py::test_cors_headers_present_on_health PASSED
tests/test_libraries.py::test_opencv_import PASSED
tests/test_libraries.py::test_numpy_import PASSED
tests/test_libraries.py::test_torch_import PASSED
tests/test_libraries.py::test_opencv_image_operations PASSED
tests/test_libraries.py::test_torch_tensor_operations PASSED
tests/test_libraries.py::test_opencv_basic_processing PASSED
tests/test_libraries.py::test_numpy_opencv_interop PASSED
tests/test_model_loading.py::test_generate_colab_notebook_script_exists PASSED
tests/test_model_loading.py::test_verify_vision_models_notebook_exists PASSED
tests/test_model_loading.py::test_model_setup_doc_exists PASSED
tests/test_model_loading.py::test_generate_script_valid_python_syntax PASSED
tests/test_model_loading.py::test_model_setup_doc_contains_all_model_sections PASSED
tests/test_model_loading.py::test_notebook_is_valid_nbformat PASSED
tests/test_model_loading.py::test_notebook_has_minimum_15_cells PASSED
tests/test_model_loading.py::test_notebook_code_cells_contain_all_model_names PASSED
tests/test_ollama.py::test_ollama_is_running PASSED
tests/test_ollama.py::test_qwen_coder_model_exists PASSED
tests/test_ollama.py::test_text_generation PASSED
tests/test_ollama.py::test_json_output_parsing PASSED
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

**이슈 및 해결 사항**:
- `pytest-asyncio` 1.3.0이 strict 모드로 동작 → 각 테스트에 `@pytest.mark.asyncio` 명시. anyio는 설치되어 있으나 별도 마커 설정 불필요 (pytest-asyncio가 우선 처리)
- `pydantic-settings`가 이미 설치되어 있어 추가 설치 불필요 → `BaseSettings` 그대로 사용
- CORS 테스트에서 OPTIONS preflight 대신 GET + Origin 헤더 방식 사용 → `allow_origins=["*"]` 설정으로 simple request에도 `Access-Control-Allow-Origin` 반환 확인

---

## Step 4 완료 내역

**목적**: Florence-2, Grounding DINO, SAM 2, DINOv2, Depth-Anything-V2 각 모델의 Colab 검증용 .ipynb 노트북과 모델 설정 가이드 문서 작성.
모든 SOTA 비전 모델은 Intel Mac에서 실행 불가 → Colab T4 16GB에서 실행 예정.

**생성/수정된 파일**:
- `scripts/generate_colab_notebook.py` (신규 생성 — nbformat을 사용해 verify_vision_models.ipynb를 프로그래밍 방식으로 생성하는 스크립트)
- `scripts/verify_vision_models.ipynb` (신규 생성 — Colab 업로드용 15셀 Jupyter 노트북: pip install, 공통 유틸, 5개 모델 섹션, 요약 테이블)
- `docs/MODEL_SETUP.md` (신규 생성 — 모델 설정 가이드: HuggingFace 경로, VIA2 역할, Colab 실행법, GPU 메모리 추정치, Remote Adapter 연동 방식)
- `tests/test_model_loading.py` (신규 생성 — 8개 로컬 pytest: 파일 존재, 문법 검사, nbformat 유효성, 셀 수 ≥15, 5개 모델명 포함)
- `requirements.txt` (nbformat>=5.0 추가)

**pytest 결과** (전체 28개):
```
28 passed in 36.00s
tests/test_model_loading.py::test_generate_colab_notebook_script_exists PASSED
tests/test_model_loading.py::test_verify_vision_models_notebook_exists PASSED
tests/test_model_loading.py::test_model_setup_doc_exists PASSED
tests/test_model_loading.py::test_generate_script_valid_python_syntax PASSED
tests/test_model_loading.py::test_model_setup_doc_contains_all_model_sections PASSED
tests/test_model_loading.py::test_notebook_is_valid_nbformat PASSED
tests/test_model_loading.py::test_notebook_has_minimum_15_cells PASSED
tests/test_model_loading.py::test_notebook_code_cells_contain_all_model_names PASSED
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

**Colab 검증**: Taeyang이 Colab에서 직접 실행 예정 — 실측 메모리 수치는 실행 후 업데이트
- 실행 방법: `scripts/verify_vision_models.ipynb`를 Google Colab에 업로드 → T4 GPU 런타임 선택 → 전체 셀 실행

**이슈 및 해결 사항**:
- Colab pip install 셀에서 `cu118` CUDA 버전 명시 → Colab은 CUDA 12.x 사용 → `--index-url` 제거로 해결
- SAM 2 패키지명 `sam2` (PyPI 미등록) → `git+https://github.com/facebookresearch/sam2.git` 으로 수정
- 이미지 URL 다운로드 실패 시 전체 노트북 중단 → try/except + PIL fallback 이미지 추가

**[핫픽스 1] Florence-2 로딩 실패 수정 (1차)** (Colab 실행 후 발견):
- **에러**: `'Florence2ForConditionalGeneration' object has no attribute '_supports_sdpa'`
- **원인 1**: `trust_remote_code=True` 누락 — Florence-2는 커스텀 모델 코드를 사용하므로 명시적으로 허용해야 함
- **원인 2**: 최신 transformers의 SDPA(Scaled Dot-Product Attention) 체크가 Florence-2 커스텀 코드와 충돌
- **해결**: `generate_colab_notebook.py` cell5 수정 후 `.ipynb` 재생성
  - `AutoModelForCausalLM.from_pretrained()`에 `trust_remote_code=True`, `attn_implementation="eager"` 추가
  - `AutoProcessor.from_pretrained()`에 `trust_remote_code=True` 추가

**[핫픽스 2] Florence-2 로딩 실패 수정 (2차 — transformers 버전 고정)**: ← 이후 롤백됨
- `transformers==4.46.3` 고정 → SAM 2 미지원, Grounding DINO API 변경으로 다른 모델들 실패 유발
- 결국 버전 고정 방식 폐기, 핫픽스 3으로 대체

**[핫픽스 3] 전체 모델 호환성 수정 (2차 시도 — workaround)**: ← 이후 핫픽스 4로 대체
- `flash_attn`, `Florence-2-base-ft` fallback, `sam-vit-base` fallback 추가 등 복잡한 workaround 시도
- Florence-2 근본 원인(커스텀 코드 비호환)을 해결하지 못함 → 핫픽스 4로 대체

**[핫픽스 4] 전체 모델 호환성 수정 (3차 시도 — 가정 기반)**: ← 핫픽스 5로 대체
- `florence-community/Florence-2-base` + `Florence2ForConditionalGeneration` 적용 → 로컬 검증 없이 가정 기반 작성

**[핫픽스 5] 전체 모델 호환성 수정 (최종 — 로컬 CPU 실제 테스트 기반)**:
- **전략 변경**: 가정으로 코드 작성하지 않고, 로컬 CPU에서 실제 실행해 동작 확인 후 노트북 반영
- **로컬 테스트 환경**: transformers 4.53.0, PyTorch 2.2.2 (CPU, Intel Mac) — PyTorch 2.4+ 미지원으로 transformers 5.x 사용 불가
- **발견 사항**:
  - **Florence-2**: `Florence2ForConditionalGeneration` 클래스는 transformers 4.53에 미존재 (5.x에서 추가됨). `florence-community/Florence-2-base`는 model_type=`florence2`로 4.53 미지원. `microsoft/Florence-2-base` + `trust_remote_code=True` + `torch_dtype=torch.float32` → CPU에서 정상 동작 확인 ✅
  - **Grounding DINO**: `inspect.signature()` 확인 결과 파라미터명은 `threshold` (구 파라미터 `box_threshold`는 4.51.0에서 deprecated — `@deprecate_kwarg("box_threshold", new_name="threshold", version="4.51.0")` 확인). `threshold=0.3, text_threshold=0.3`이 올바른 호출 ✅
  - **SAM 2**: `facebook/sam2-hiera-small`은 model_type=`sam2_video`로 transformers 4.53 미지원 (`KeyError: 'sam2_video'`). 최신 transformers(5.x) 필요 → Colab에서만 테스트 가능
- **최종 노트북 코드**:
  - **cell5 (Florence-2)**: transformers 5.x 환경에서는 `florence-community/Florence-2-base` + `Florence2ForConditionalGeneration` 시도, 실패 시 `microsoft/Florence-2-base` + `trust_remote_code=True` + `attn_implementation="eager"` fallback (CPU에서 동작 확인된 코드)
  - **cell7 (Grounding DINO)**: `threshold=0.3, text_threshold=0.3` (실제 signature 확인 기반)
  - **cell9 (SAM 2)**: `pipeline("mask-generation", "facebook/sam2-hiera-small")` (최신 transformers 필요)
- **로컬 pytest**: 28/28 통과
- **수정 파일**: `scripts/generate_colab_notebook.py`, `scripts/verify_vision_models.ipynb` (재생성)

**[핫픽스 6] Florence-2 추론 dtype 불일치 수정**:
- **에러**: `RuntimeError: Input type (float) and bias type (c10::Half) should be the same`
- **원인**: 모델은 `dtype=torch.float16`으로 로드됐으나 processor 출력 텐서는 float32
- **해결**: inference 입력을 `model.device`와 `torch.float16`으로 동시 캐스팅
  - 변경 전: `.to("cuda" if torch.cuda.is_available() else "cpu")`
  - 변경 후: `.to(model.device, torch.float16)`
- HuggingFace 공식 예제 패턴 (`inputs.to(model.device, torch.bfloat16)`) 참조
- **수정 파일**: `scripts/generate_colab_notebook.py`, `scripts/verify_vision_models.ipynb` (재생성)

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
