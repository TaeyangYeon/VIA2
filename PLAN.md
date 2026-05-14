# VIA2 (Vision Intelligence Agent)
## Master Development Plan v3.0

Intel Mac + 다중 SOTA 비전 모델 (로컬/Colab 하이브리드) 기반 비전 알고리즘 자동 설계 데스크톱 앱.
v2.x의 실패 분석 기반 전면 재설계. TDD + PCRO 워크플로우. 50 Steps / 8 Phases.

---

# Part 1. 프로젝트 개요

## 1.1 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 개발 환경 | Intel Mac (x86_64) / macOS |
| AI 엔진 (하이브리드) | 로컬 Ollama + Colab/Azure URL 설정 가능 |
| 백엔드 | FastAPI + Python 3.11 |
| 프론트엔드 | Electron + React + TypeScript + TailwindCSS + Redux Toolkit |
| 비전 라이브러리 | OpenCV + NumPy + PyTorch (모델 추론) |
| Light Test 렌더링 | Canvas 2D (정면도 + 평면도 듀얼 뷰) |
| 테스트 | pytest (백엔드), jest + React Testing Library (프론트엔드) |
| 개발 방식 | TDD + PCRO 프롬프트 → Claude Code 구현 → Taeyang 직접 검증 → Git 커밋 |
| 총 개발 단계 | 50 Steps / 8 Phases |

## 1.2 프로젝트 목적

이미지와 사용자 의도, ROI를 분석하여 **라이브러리에 종속되지 않은 비전 알고리즘 설계도**를 자동으로 생성하는 멀티에이전트 AI 데스크톱 앱.
로컬 또는 Colab/Azure 서버를 통해 다양한 SOTA 비전 모델을 활용.

**출력물**
- SVG Blueprint 다이어그램 (검사 시퀀스 + 노드별 파라미터)
- 한국어 알고리즘 설명 및 기술 사양서
- 테스트 메트릭 (Accuracy / 과검률 / 미검률 / 좌표 오차)
- 개선 제안 (조명 변경 / HW 개선 / Edge Learning / Deep Learning 판단 + 근거)

**지원 모드**
- **Inspection Mode**: OK/NG 이미지 이진 분류 알고리즘 설계
- **Align Mode**: X/Y 좌표 산출 알고리즘 설계 (EL/DL 제외, HW 개선만)

**별도 기능**
- **Light Test 윈도우**: 메인 파이프라인과 완전히 분리된 가상 조명 시뮬레이션 도구

## 1.3 이전 버전 실패 분석 및 v3.0 설계 원칙

v2.x는 Gemma4 단일 모델로 13개 에이전트를 모두 운영하면서 실패했다. v3.0은 그 실패 원인을 구조적으로 해결한다.

| # | v2.x 실패 원인 | v3.0 해결 방향 |
|---|---------------|---------------|
| 1 | Gemma4 단일 모델로 시각 분석, 코딩, 판단을 모두 처리 → 정확도 부족 | 역할별 SOTA 모델 분리 (시각/코딩/판단/Depth) |
| 2 | LLM이 알고리즘 카테고리를 단독 결정 → 엉뚱한 기법 선택 | Python 결정 트리가 카테고리 확정, LLM override 불가 |
| 3 | 고정된 검사 템플릿만 사용 | Inspection Plan Agent가 검사 항목을 자유롭게 다단계 설계 |
| 4 | 이미지 처리 파이프라인 고정 (CLAHE 같은 적합한 방식이 제안되지 않음) | Block Library + Pipeline Composer로 자유로운 조합 |
| 5 | 처리 품질 판단이 범용 수치뿐 → 검사 목적과 무관한 평가 | Vision Judge Agent (Qwen2.5-VL/InternVL)가 이미지를 직접 보고 목적 기준 판단 |
| 6 | OpenCV 코드 직접 생성 → 사용자 환경(Cognex/MIL 등) 미스매치 | SVG Blueprint + 파라미터 시트로 라이브러리 불가지론적 출력 |
| 7 | 조명 환경에 대한 가이드 없음 | Light Test 윈도우 신설, 가상 조명 시뮬레이션 |

### v3.0 핵심 설계 원칙

1. **모델 전문화**: 시각 분석은 시각 모델이, 로직 설계는 코드 모델이, 시각적 판단은 VLM이 담당
2. **검사 항목 설계** → Inspection Plan Agent (자유로운 다단계 설계, 고정 템플릿 없음)
3. **이미지 처리 파이프라인** → Block Library + Pipeline Composer + Parameter Searcher
4. **처리 품질 판단** → Vision Judge Agent (VLM이 이미지 직접 시각적 판단)
5. **알고리즘 카테고리 선택** → Python 결정 트리 (LLM 금지)
6. **출력 형태** → 코드가 아닌 SVG Blueprint + 파라미터 시트 (라이브러리 독립)
7. **사용자 개입** → ROI 직접 설정 + Agent Directive로 에이전트별 방향성 지시
8. **조명 시뮬레이션** → 메인 파이프라인과 완전 분리된 Light Test 윈도우
9. **하이브리드 인프라** → 로컬 또는 외부 서버(Colab/Azure) URL로 자유 전환

---

# Part 2. 시스템 설계

## 2.1 아키텍처

```
[Desktop UI: Electron + React + Redux]
  ┌─────────────────┐    ┌──────────────────┐
  │ Main Workspace  │    │ Light Test Window│ ← 완전 분리
  │ - ROI 설정      │    │ - 정면도 + 평면도│
  │ - Directive     │    │ - 가상 조명     │
  │ - Blueprint 결과│    │ - 편광 시뮬레이션│
  └────────┬────────┘    └──────────────────┘
           ↓
   [FastAPI Local Server :8000]
           ↓
    [AI Engine Adapter]
   (Local Ollama / Colab URL / Azure URL)
           ↓
  ┌────────────────────────────────────────┐
  │  [Multi-Agent Orchestration]           │
  │  Orchestrator                          │
  │  ├ Spec Agent          (Qwen2.5-Coder) │
  │  ├ Image Analysis      (OpenCV)        │
  │  ├ Depth Agent         (Depth-V2)      │
  │  ├ Material Agent      (Florence-2)    │
  │  ├ ROI Agent           (Grounding DINO+SAM 2) │
  │  ├ Pipeline Composer   (Rule-based)    │
  │  ├ Parameter Searcher  (OpenCV)        │
  │  ├ Vision Judge        (Qwen2.5-VL)    │
  │  ├ Inspection Plan     (Qwen2.5-Coder) │
  │  ├ Algorithm Selector  (결정 트리)     │
  │  ├ Blueprint Agent     (SVG 생성)      │
  │  ├ Test Agent          (OpenCV)        │
  │  ├ Evaluation Agent    (Rule-based)    │
  │  ├ Feedback Controller (Rule-based)    │
  │  └ Decision Agent      (InternVL+통계) │
  └────────────────────────────────────────┘
```

## 2.2 에이전트 구성 및 모델 매칭

| # | 에이전트 | 역할 | 사용 모델 |
|---|---------|------|----------|
| 1 | Orchestrator | 전체 파이프라인 제어, Retry, 목표 수치 사전 검증 | Python (로직) |
| 2 | Spec Agent | 사용자 텍스트 → 모드/목표/성공기준 추출 | Qwen2.5-Coder:7b |
| 3 | Image Analysis Agent | 이미지 특성 수치 + 처리 전략 진단 (히스토그램, 노이즈, 엣지 등) | OpenCV (LLM 미사용) |
| 4 | Depth Agent | 단안 깊이 추정 → 3D 구조 맵 생성 | Depth-Anything-V2 |
| 5 | Material Agent | 픽셀별 재질 분류 (금속/플라스틱/유리/고무 등) | Florence-2 + DINOv2 |
| 6 | ROI Agent | 사용자 ROI 처리 + 텍스트 기반 자동 ROI 추천 (옵션) | Grounding DINO + SAM 2 |
| 7 | Pipeline Composer | Block Library로 후보 파이프라인 조합 | Python (Rule-based) |
| 8 | Parameter Searcher | 각 파이프라인 파라미터 자동 탐색 | OpenCV (LLM 미사용) |
| 9 | Vision Judge Agent | 원본+처리 이미지 직접 보고 목적 기준 판단 | Qwen2.5-VL |
| 10 | Inspection Plan Agent | 검사 항목 목록/순서/의존성 자유 설계 | Qwen2.5-Coder:7b |
| 11 | Algorithm Selector | 이미지 진단 수치로 알고리즘 카테고리 확정 | Python (결정 트리) |
| 12 | Blueprint Agent | SVG 다이어그램 + 파라미터 시트 생성 | Qwen2.5-Coder:7b |
| 13 | Test Agent | 항목별 OpenCV 검증 실행 → 메트릭 계산 | OpenCV (LLM 미사용) |
| 14 | Evaluation Agent | 항목별 실패 원인 분석 + 성공/실패 판정 | Python (Rule-based) |
| 15 | Feedback Controller | 실패 원인별 재시도 전략 결정 | Python (Rule-based) |
| 16 | Decision Agent | 최종 판단: Rule-based 유지 / EL / DL | InternVL + 통계 분석 |

**Light Test 전용 (별도 파이프라인)**

| 컴포넌트 | 역할 | 사용 모델 |
|----------|------|----------|
| Light Rendering Engine | 정면도/평면도 PBR 렌더링 (Depth + Material 병합) | Canvas 2D + Python 연산 |
| Polarization Simulator | 말루스의 법칙 기반 편광 시뮬레이션 | Python (수식 기반) |

## 2.3 AI 모델 선택 근거

### 시각 분석 모델군

- **Florence-2** (Microsoft, 0.2B~0.7B): 경량 멀티모달. 캡셔닝/검출/세그멘테이션 통합. 재질 영역 1차 분류용
- **Grounding DINO**: 텍스트 → Bounding Box. "검은색 기스" 같은 자연어로 ROI 자동 탐지
- **SAM 2** (Meta): 픽셀 단위 정밀 세그멘테이션. ROI 내부 객체 외곽선 추출
- **DINOv2** (Meta): 자기지도학습 기반 특징 벡터 추출. 재질 유사도 판단 + Decision Agent의 변동성 분석
- **Depth-Anything-V2**: 단안 깊이 추정. Light Test의 그림자 시뮬레이션 핵심

### 로직/추론 모델군

- **Qwen2.5-Coder:7b**: 코드 및 구조화된 JSON 출력 능력 우수. Spec/Inspection Plan/Blueprint 생성
- **Qwen2.5-VL**: 멀티모달 이해. Vision Judge로 "검사 목적에 맞게 잘 보이는가" 판단
- **InternVL**: 고차원 시각적 추론. Decision Agent의 EL/DL 최종 판단

### 모델 동적 로딩

Colab T4 16GB 환경 기준, 모든 모델을 동시 로드 불가.
Ollama 클라이언트 + Python 라이브러리 로더가 단계별 필요한 모델만 로드/언로드.
사용자는 로컬 Ollama 또는 원격 서버 URL(Colab/Azure) 선택 가능.

## 2.4 실행 파이프라인

```
사용자 입력
  ├ 검사할 이미지 업로드
  ├ ROI 사각형 직접 지정 (첫 이미지 위에 드래그)
  ├ 검사 의도 텍스트 입력
  └ Agent Directives 입력 (선택, 비어있으면 자체 판단)
              ↓
[목표 수치 사전 검증]
              ↓
Spec Agent → Image Analysis → Depth Agent → Material Agent
              ↓
Pipeline Composer (Block Library로 후보 3~5개 생성)
              ↓
FOR 각 후보 파이프라인:
  Parameter Searcher → ProcessingQualityEvaluator → Vision Judge
              ↓
최고 점수 파이프라인 확정
              ↓
Algorithm Selector (결정 트리) → Inspection Plan Agent
              ↓
Blueprint Agent (SVG 다이어그램 + 파라미터 시트)
              ↓
Test Agent (항목별 OpenCV 실행 → 메트릭)
              ↓
Evaluation Agent
              ↓
  성공 → Blueprint 출력 + 조명 권장사항 출력
  실패 → Feedback Controller → Retry
         max_iteration 초과 → Decision Agent
                                ├ Rule-based 유지
                                ├ Edge Learning 권고
                                └ Deep Learning 권고
```

**Light Test 흐름 (메인과 완전 분리)**

```
[Light Test 윈도우 별도 실행]
  ↓
사용자가 이미지 새로 업로드 (메인과 별개)
  ↓
Depth Agent + Material Agent 분석
  ↓
[정면도 뷰]                    [평면도 뷰]
- 카메라 시점 렌더링            - 위에서 내려다본 평면도
- 조명 배치 (Pitch/높이)        - 조명 배치 (Yaw/거리/LWD)
- 실시간 PBR 렌더링            - 카메라 위치 중앙 고정
                              - 물체는 Depth 기반 실루엣
  ↓
사용자 조작
  ├ 조명 형상 선택 (Ring/Bar/Spot/Coaxial/Dome/Low-angle Ring)
  ├ 조명 타입 선택 (LED/Halogen/UV/IR)
  ├ 조명 컬러 (RGB) — Gray 이미지 시 비활성화
  ├ 편광 (조명측 체크박스 / 렌즈측 다이얼)
  └ 조명 위치/크기/각도 조정
  ↓
실시간 렌더링 결과 확인 + 히스토그램 변화 표시
```

## 2.5 핵심 컴포넌트

### 2.5.1 ImageDiagnosis

Image Analysis Agent가 OpenCV로 계산하는 이미지 진단 수치.

```python
@dataclass
class ImageDiagnosis:
    # 기본 광학 특성
    contrast: float
    noise_level: float
    edge_density: float
    lighting_uniformity: float
    illumination_type: str        # "uniform" / "gradient" / "spot" / "uneven"
    noise_frequency: str          # "high_freq" / "low_freq" (FFT 기반)
    reflection_level: float

    # 재질/구조 (Material Agent + Depth Agent에서 채워짐)
    surface_type: str             # "metal" / "plastic" / "glass" / "rubber" / ...
    depth_complexity: float       # 표면 굴곡 복잡도
    has_shadow_region: bool       # 그림자 영역 존재 여부

    # 알고리즘 선택용
    blob_feasibility: float
    blob_count_estimate: int
    color_discriminability: float
    dominant_channel_ratio: float
    structural_regularity: float
    pattern_repetition: float

    # 처리 힌트
    optimal_color_space: str
    threshold_candidate: float
    edge_sharpness: float
```

### 2.5.2 Pipeline Block Library

처리 블록과 조건 매칭 규칙. Pipeline Composer가 진단 수치를 보고 조합.

```python
PIPELINE_BLOCKS = {
    # 색공간
    "grayscale", "hsv_s", "hsv_v", "lab_l", "ycrcb_cr",

    # 노이즈 제거
    "gaussian_fine", "gaussian_mid", "bilateral",
    "median", "nlmeans", "clahe",

    # 임계값
    "otsu", "adaptive_mean", "adaptive_gauss", "dynamic_threshold",

    # 모폴로지
    "erosion", "dilation", "opening", "closing",
    "tophat", "blackhat", "morph_gradient",

    # 엣지
    "canny", "sobel", "laplacian", "scharr",
}
```

각 블록은 적용 조건(`when=...`)과 파라미터 탐색 범위(`params=...`)를 가짐.

### 2.5.3 ROI 설정

사용자가 첫 번째 로드된 이미지 위에 마우스 드래그로 사각형 ROI 지정.
ROI 좌표 `(x1, y1, x2, y2)`가 모든 분석 에이전트의 입력에 포함됨.

선택적으로 ROI Agent에 텍스트 입력 시 Grounding DINO + SAM 2가 자동으로 ROI 추천 가능.

### 2.5.4 Vision Judge Agent

Qwen2.5-VL이 원본 + 처리된 이미지를 직접 보고 검사 목적 기준으로 판단.
v2.x에서 Gemma4가 못 했던 "검사 목적에 맞게 잘 보이는지" 시각적 판단을 담당.

**출력**: visibility_score / separability_score / measurability_score / problems / next_suggestion

### 2.5.5 Inspection Plan Agent

고정 템플릿 없이 검사 목적에 맞는 항목을 자유롭게 설계.

**타공 검사 예시**:
```
항목 0: 구멍 후보 검출 (BLOB)          - 기초 검출
항목 1: 구멍 간 거리 검사 (GEOMETRIC)  - 오인식 방지  ← depends_on: [0]
항목 2: 구멍 크기 검사 (BLOB)          - 주 검사      ← depends_on: [1]
항목 3: 진원도 검사 (BLOB)             - 품질 검사    ← depends_on: [1]
항목 4: 구멍 개수 검사 (COUNT)         - 누락 검출    ← depends_on: [1,2,3]
```

### 2.5.6 Algorithm Selector (결정 트리)

LLM이 알고리즘 카테고리를 단독 결정하지 않음. Python 결정 트리가 확정하며 LLM이 override 불가.

```python
def select_algorithm_category(diagnosis: ImageDiagnosis) -> AlgorithmCategory:
    if diagnosis.contrast > 0.4 and diagnosis.blob_feasibility > 0.6:
        return BLOB
    if diagnosis.color_discriminability > 0.5:
        return COLOR_FILTER
    if diagnosis.edge_density > 0.3 and diagnosis.structural_regularity > 0.5:
        return EDGE_DETECTION
    if diagnosis.pattern_repetition > 0.7:
        return TEMPLATE_MATCHING
    return BLOB
```

### 2.5.7 Blueprint Agent (SVG 다이어그램)

OpenCV 코드 생성 대신 라이브러리 독립적인 SVG 설계도 출력.

**구성**:
- 알고리즘 노드 (Preprocessing / Feature Extraction / Inspection / Decision)
- 노드 간 연결선 (실행 흐름)
- 각 노드 클릭 시 우측 패널에 파라미터 시트 표시
- 파라미터: 수학적 의미 기반 (예: "Otsu 자동", "히스토그램 하위 15%", "5x5 Median")
- 다이어그램 PNG/PDF/SVG 내보내기

### 2.5.8 Agent Directive

각 에이전트마다 사용자가 방향성 입력 가능. 입력 없으면 에이전트 자체 판단.

```python
@dataclass
class AgentDirectives:
    orchestrator: str      # "과검 0.1% 이하를 반드시 달성해"
    spec: str
    image_analysis: str    # "반사광은 무시하고 구멍 경계에 집중"
    depth: str
    material: str
    pipeline_composer: str # "Blob 방식 파이프라인 우선 시도"
    vision_judge: str
    inspection_plan: str   # "오인식 방지 항목을 반드시 포함해"
    test: str              # "과검보다 미검을 더 엄격하게 평가"
```

### 2.5.9 Decision Agent (EL/DL 판단)

max_iteration 초과 시 InternVL + 통계 분석으로 최종 판단.

| 판단 | 조건 |
|------|------|
| Rule-based 유지 | Vision Judge 점수가 임계값 근처 도달, 파라미터 탐색 여지 있음 |
| Edge Learning | 불량이 미세하고 일관된 패턴 (DINOv2 특징 변동성 낮음) |
| Deep Learning | 불량 형태 다양/불규칙 (DINOv2 특징 변동성 20% 이상, InternVL이 비정형 패턴 판단) |

목표 수치(과검/미검률) max_iteration 내 달성 불가 시 핵심 근거로 사용.
Align 모드는 EL/DL 없음, HW 개선만 반환.

### 2.5.10 Light Test 윈도우

메인 파이프라인과 **완전히 분리된** 가상 조명 시뮬레이션 도구.

**듀얼 뷰 구조**:
- **정면도 (Front View)**: 카메라 시점 렌더링, 조명의 X/Y 위치 + Pitch 각도 조정
- **평면도 (Top View)**: 위에서 내려다본 뷰, 조명의 X/Z 위치 + Yaw 각도 + LWD(Light Working Distance) 조정
  - 카메라 위치 중앙 고정
  - 물체는 Depth 기반 위에서 본 실루엣
  - 조명 형상/크기 시각화 (가이드)

**조명 변수**:
- 형상: Ring / Bar / Spot / Coaxial / Dome / Low-angle Ring
- 타입: LED / Halogen / UV / IR
- 컬러: RGB 컬러 조명 (Gray 이미지일 때 비활성화)
- 편광:
  - 조명측: 체크박스 (필름 적용 여부)
  - 렌즈측: 0~180° 다이얼 (말루스의 법칙 적용)

**렌더링 우선순위 (Depth > Material)**:
1. Depth-Anything-V2가 3D 구조 추출
2. 조명 위치 기반으로 그림자 영역 우선 계산
3. 그림자 영역이 아닌 곳에서만 Material PBR (Specular/Diffuse) 적용
4. 편광 필터 효과 (말루스의 법칙) 최종 적용

**메인 파이프라인과의 관계**:
- 메인 파이프라인이 "조명을 이렇게 바꿔보세요" 권장사항 출력
- 사용자가 Light Test로 가서 새 이미지 업로드 후 권장 조명 직접 테스트
- Light Test 결과를 가지고 실제 현장에서 조명 변경 후 새 이미지로 메인 파이프라인 재실행
- **자동 피드백 없음 — 완전히 별도 도구**

### 2.5.11 AI Engine Adapter (하이브리드 구조)

설정 메뉴에서 엔진 종류 선택.

```typescript
{
  engine_mode: 'local' | 'remote',
  local_ollama_url: 'http://127.0.0.1:11434',  // 로컬
  remote_url: 'https://...',                    // Colab/Azure URL
  remote_type: 'colab' | 'azure' | 'custom'
}
```

추상 인터페이스 `BaseAIAdapter`를 따라 어떤 엔진이든 동일한 방식으로 호출.
신규 모델 추가 시 어댑터만 작성하면 됨.

## 2.6 디렉토리 구조

```
via/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── routers/           # images, roi, config, directives, execute, logs, export, light_test
│   ├── services/          # ai_adapter, image_store, logger
│   └── models/
├── agents/
│   ├── base_agent.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── spec_agent.py
│   ├── image_analysis_agent.py
│   ├── depth_agent.py              ← Depth-Anything-V2
│   ├── material_agent.py           ← Florence-2 + DINOv2
│   ├── roi_agent.py                ← Grounding DINO + SAM 2
│   ├── pipeline_blocks.py
│   ├── pipeline_composer.py
│   ├── parameter_searcher.py
│   ├── processing_quality_evaluator.py
│   ├── vision_judge_agent.py       ← Qwen2.5-VL
│   ├── inspection_plan_agent.py    ← Qwen2.5-Coder
│   ├── algorithm_selector.py       ← 결정 트리
│   ├── blueprint_agent.py          ← SVG 생성
│   ├── test_agent_inspection.py
│   ├── test_agent_align.py
│   ├── evaluation_agent.py
│   ├── feedback_controller.py
│   ├── decision_agent.py           ← InternVL
│   └── prompts/
├── light_test/
│   ├── renderer.py                 ← Canvas 2D 정면도/평면도 렌더링
│   ├── polarization.py             ← 말루스의 법칙
│   ├── material_pbr.py             ← Specular/Diffuse
│   └── lighting_models.py          ← 조명 형상별 수식
├── frontend/
│   ├── main.js
│   ├── src/
│   │   ├── store/                  ← Redux slices
│   │   ├── styles/                 ← 디자인 토큰
│   │   ├── services/               ← API client
│   │   └── components/
│   │       ├── panels/             ← Main workspace
│   │       └── light_test/         ← Light Test 윈도우
│   └── package.json
├── tests/
├── scripts/
├── docs/
├── VIA_MASTER_PLAN.md
├── progress.md
└── README.md
```

## 2.7 Redux Store 구조

```typescript
{
  project: { name, created_at },
  engine: {
    mode: 'local' | 'remote',
    local_url: string,
    remote_url: string,
    remote_type: 'colab' | 'azure' | 'custom'
  },
  images: { analysis: [...], test: [...] },
  roi: { x1, y1, x2, y2 } | null,
  config: {
    mode: 'align' | 'inspection',
    max_iteration: number,
    success_criteria: { accuracy?, fp_rate?, fn_rate?, coord_error? }
  },
  directives: {
    orchestrator, spec, image_analysis, depth, material,
    pipeline_composer, vision_judge, inspection_plan, test
  },
  execution: {
    status, execution_id, current_agent, current_iteration,
    goal_validation, progress
  },
  result: {
    summary, pipeline, inspection_plan,
    blueprint_svg, parameter_sheet,            ← 코드 대신 Blueprint
    metrics, item_results,
    lighting_suggestions,                       ← 조명 권장사항
    improvement_suggestions,
    decision, decision_reason
  },
  light_test: {                                ← Light Test 별도 상태
    image: ...,
    lights: [{ type, shape, position, intensity, color, polarizer, ... }],
    camera_view: 'front' | 'top',
    rendered_result: ...
  },
  logs: [...]
}
```

---

# Part 3. 개발 규칙

## 3.1 워크플로우

```
1. VIA_MASTER_PLAN.md + progress.md 첨부
2. "STEP N 진행해줘" 요청
3. Claude가 해당 Step 내용을 보고 아래 3가지를 생성:
   ① PCRO 형식의 Claude Code 프롬프트 (영어)
   ② 직접 검증 방법 (3-Gate)
   ③ Git 커밋 메시지
4. Claude Code에 프롬프트 입력 → TDD 방식으로 구현
5. Taeyang이 직접 3-Gate 검증 수행
6. 검증 완료 후 Taeyang이 직접 Git 커밋
7. progress.md Step N 완료 표기 ([ ] → [x])
```

**원칙**
- Claude Code는 Git 커밋하지 않음
- 커밋은 Taeyang이 3-Gate 검증 완료 후 직접 수행
- 하나의 Step = 하나의 커밋

## 3.2 TDD 규칙

Claude Code가 구현한 코드가 실제로 동작하는지 테스트 결과로만 확인 가능하다.
따라서 모든 구현은 테스트 주도 방식을 따른다.

**사이클**: Red (실패 테스트) → Green (최소 구현) → Blue (리팩토링)

**규칙**
1. 테스트 파일을 구현 파일보다 먼저 작성
2. Claude Code는 테스트 실행 결과를 확인하면서 구현
3. 모든 테스트 GREEN 확인 후 다음 기능 진행
4. 테스트 파일이 해당 기능의 스펙 역할
5. 백엔드는 pytest, 프론트엔드는 jest + React Testing Library

**PCRO Output Format 고정 순서**
```
Step 1. Write test file first
Step 2. Run tests → confirm ALL FAIL (Red)
Step 3. Implement the feature
Step 4. Run tests → confirm ALL PASS (Green)
Step 5. Refactor if needed, confirm still GREEN
```

## 3.3 PCRO 프롬프트 규칙

```
## Persona
You are a [구체적인 전문가 역할].

## Context
[프로젝트 배경]
[현재까지 구현된 내용 (이전 Step 결과)]
[이번 Step에서 구현해야 할 내용]

## Restriction
- [하지 말아야 할 것들]
- Do NOT commit to git.
(UI Step의 경우 UI 디자인 규칙 추가)

## Output Format
Step 1. Write test file first
Step 2. Run tests → confirm ALL FAIL (Red)
Step 3. Implement the feature
Step 4. Run tests → confirm ALL PASS (Green)
Step 5. Refactor if needed, confirm still GREEN
- [생성해야 할 파일 목록 및 경로]
```

**규칙**
1. 프롬프트는 반드시 영어로 작성
2. Persona는 구체적인 전문가 역할 명시
3. Context에 이전 Step 결과물 명시
4. Restriction에 `Do NOT commit to git` 반드시 포함
5. Output Format에 TDD 순서 반드시 포함
6. UI Step은 Restriction에 UI 디자인 규칙 포함

## 3.4 검증 3-Gate 규칙

매 Step마다 Taeyang이 직접 확인. 3-Gate를 전부 통과해야 다음 Step 진행.

```
Gate 1 — pytest / jest
  터미널에서 직접 실행 → 전체 GREEN 확인

Gate 2 — 코드 리뷰
  구현된 코드를 Claude에게 공유하고 리뷰 요청

Gate 3 — 직접 실행 확인
  터미널 명령어 또는 UI를 직접 실행하여 동작 확인
```

Claude는 Step 내용을 보고 Gate별 구체적인 명령어와 기대 결과를 제공한다.

## 3.5 Git 커밋 규칙

**형식**
```
<type>: <영어 제목>

<한국어 본문>

- 완료 항목 1
- 완료 항목 2
```

**Type**

| type | 용도 |
|------|------|
| feat | 새 기능 추가 |
| fix | 버그 수정 |
| test | 테스트 추가/수정 |
| refactor | 리팩토링 |
| docs | 문서 수정 |
| chore | 빌드/설정 변경 |

## 3.6 UI 디자인 규칙

VIA는 외부 서비스로 공개 가능한 수준의 UI 품질을 목표로 한다.
Phase 5~7의 모든 UI 구현은 아래 규칙을 따른다.

### 색상 시스템 (Neutral Black/Gray 전용)

```
배경
  최상위:     #0a0a0a
  카드/패널:  #111111
  보조 패널:  #1a1a1a
  호버/선택:  #222222

경계선
  기본:       #2a2a2a
  강조:       #3a3a3a

텍스트
  주요:       #f5f5f5
  보조:       #a0a0a0
  비활성:     #555555

강조색 (포인트 컬러만 사용)
  주요 액션:  #ffffff
  성공:       #4ade80
  경고:       #facc15
  오류:       #f87171
  정보:       #60a5fa  (최소화)
```

**금지**: 파랑/퍼플/그린 계열의 다크 테마 배경 사용 금지.

### 디자인 패턴

- **Glass Morphism**: `bg-white/5 backdrop-blur-sm border border-white/10`
- **Micro Interaction**: 모든 인터랙션에 `transition-all duration-150`
- **Typography**: Inter 또는 시스템 sans-serif, 코드는 JetBrains Mono
- **Spacing**: 8px 그리드
- **Icon**: lucide-react 통일

### UI Step PCRO Restriction 템플릿

```
- Use ONLY neutral black/gray dark theme (NO blue/purple/green backgrounds)
- Apply glass morphism: bg-white/5 backdrop-blur border border-white/10
- All interactive elements must have transition-all duration-150
- Use lucide-react for all icons
- Implement empty/loading/error states for every component
- UI quality must be production-ready
- Do NOT commit to git.
```

---

# Part 4. 50단계 개발 계획

## 4.1 Phase 개요

| Phase | 이름 | Steps | 산출물 |
|-------|------|-------|--------|
| 1 | 환경 설정 | 1-4 | Python, AI 모델 사전 검증 |
| 2 | 백엔드 기반 + AI Adapter | 5-11 | FastAPI, 이미지/ROI API, 하이브리드 AI Adapter |
| 3 | 시각 분석 에이전트 | 12-19 | Image Analysis, Depth, Material, ROI |
| 4 | 파이프라인 설계 | 20-27 | Block Library, Composer, Vision Judge, Inspection Plan |
| 5 | Blueprint + 평가 루프 | 28-34 | Blueprint Agent, Test, Evaluation, Decision, Orchestrator |
| 6 | 메인 프론트엔드 | 35-41 | Electron + React UI, ROI 드로잉, Blueprint Viewer |
| 7 | Light Test 윈도우 | 42-46 | 듀얼 뷰 + 조명/편광 시뮬레이션 |
| 8 | 통합/패키징/배포 | 47-50 | E2E 테스트, DMG 패키징 |

---

## Phase 1: 환경 설정

### Step 1 — Python 환경 + 프로젝트 디렉토리 초기화
- **작업 내용**: pyenv + Python 3.11. 전체 폴더 구조 생성. `.gitignore`, `README.md`, `progress.md` 초기화
- **생성 파일**: `pyproject.toml`, `requirements.txt`, `.python-version`, 디렉토리 구조, `.gitignore`, `README.md`, `progress.md`
- **검증 포인트**: 파이썬 버전 확인, 디렉토리 구조 확인

### Step 2 — OpenCV + NumPy + PyTorch 설치
- **작업 내용**: `opencv-python-headless`, `numpy`, `torch` (CPU). Intel Mac x86_64 호환성 검증
- **생성 파일**: `requirements.txt` 업데이트, `tests/test_libraries.py`
- **검증 포인트**: import 확인, OpenCV 이미지 로드/저장, PyTorch tensor 동작 확인

### Step 3 — Ollama 설치 + Qwen2.5-Coder 검증
- **작업 내용**: Ollama 설치. `qwen2.5-coder:7b` pull. `ollama serve` 스크립트. 텍스트 생성 동작 검증
- **생성 파일**: `scripts/start_ollama.sh`, `tests/test_ollama.py`
- **검증 포인트**: 텍스트 응답, JSON 출력 파싱 확인

### Step 4 — SOTA Vision 모델 사전 검증 (Colab 가이드)
- **작업 내용**: Florence-2, Grounding DINO, SAM 2, DINOv2, Depth-Anything-V2 각각 Colab/로컬 로드 가능 여부 검증. 메모리 사용량 측정. 모델 로딩 가이드 문서화
- **생성 파일**: `scripts/verify_vision_models.py`, `docs/MODEL_SETUP.md`, `tests/test_model_loading.py`
- **검증 포인트**: 각 모델이 로컬 또는 Colab에서 정상 로드되는지 확인, 메모리 점유량 기록

---

## Phase 2: 백엔드 기반 + AI Adapter

### Step 5 — FastAPI 초기화 + Health 엔드포인트
- **작업 내용**: `fastapi`, `uvicorn` 설치. `/health` 엔드포인트. CORS 미들웨어
- **생성 파일**: `backend/main.py`, `backend/config.py`, `tests/test_api_health.py`
- **검증 포인트**: `/health` 응답 확인

### Step 6 — AI Engine Adapter 추상 인터페이스 + 로컬 Ollama 어댑터
- **작업 내용**: `BaseAIAdapter` 추상 클래스 정의. `OllamaAdapter` 구현 (로컬). 텍스트/이미지 입력 통합 인터페이스
- **생성 파일**: `backend/services/ai_adapter/base.py`, `backend/services/ai_adapter/ollama_adapter.py`, `tests/test_ollama_adapter.py`
- **검증 포인트**: 추상 인터페이스 동작 확인, 로컬 Ollama로 Qwen2.5-Coder 호출 성공

### Step 7 — Remote AI Adapter (Colab/Azure URL)
- **작업 내용**: `RemoteAdapter` 구현 (httpx 기반). URL/인증 토큰 설정. 타임아웃/재시도. 로컬과 동일 인터페이스
- **생성 파일**: `backend/services/ai_adapter/remote_adapter.py`, `tests/test_remote_adapter.py`
- **검증 포인트**: Mock 서버로 원격 호출 동작 확인. 타임아웃 처리 확인

### Step 8 — Engine 설정 API
- **작업 내용**: `POST /api/engine` (mode, urls 저장). `GET /api/engine` (현재 설정 조회). Adapter Factory가 설정에 따라 적절한 어댑터 반환
- **생성 파일**: `backend/routers/engine.py`, `backend/services/ai_adapter/factory.py`, `tests/test_engine_api.py`
- **검증 포인트**: 로컬/원격 설정 전환 시 동작 변경 확인

### Step 9 — 이미지 업로드 + 저장소 API
- **작업 내용**: `POST /api/images/upload`. 파일명 검증 (OK_N.png / NG_N.png). Analysis/Test 분류. CRUD API
- **생성 파일**: `backend/routers/images.py`, `backend/services/image_validator.py`, `backend/services/image_store.py`, `tests/test_image_api.py`
- **검증 포인트**: 유효/무효 파일명 처리, 업로드/조회/삭제 동작 확인

### Step 10 — ROI 설정 API + Config + Directive API
- **작업 내용**: `POST /api/roi` (사각형 좌표 저장). `POST /api/config`, `POST /api/directives`. 극단 목표 경고 로직
- **생성 파일**: `backend/routers/roi.py`, `backend/routers/config.py`, `backend/routers/directives.py`, `tests/test_settings_api.py`
- **검증 포인트**: ROI 좌표 저장/조회, 설정 저장, 극단 목표 경고 확인

### Step 11 — 로깅 시스템
- **작업 내용**: `structlog` 기반 에이전트별 로그. `GET /api/logs`
- **생성 파일**: `backend/services/logger.py`, `backend/routers/logs.py`, `tests/test_logger.py`
- **검증 포인트**: 로그 파일 생성 및 API 조회 확인

---

## Phase 3: 시각 분석 에이전트

### Step 12 — Agent 기본 인터페이스 + 전체 모델 정의
- **작업 내용**: `BaseAgent` 추상 클래스. `AgentResult`, `ImageDiagnosis`, `InspectionPlan`, `JudgementResult`, `AgentDirectives`, `ProcessingPipeline`, `Blueprint` 데이터 클래스
- **생성 파일**: `agents/base_agent.py`, `agents/models.py`, `tests/test_models.py`
- **검증 포인트**: 모든 모델 import 및 인스턴스 생성 확인

### Step 13 — Spec Agent (Qwen2.5-Coder)
- **작업 내용**: 사용자 텍스트 + ROI → mode/목표/성공기준 추출. Agent Directive 반영. JSON 출력
- **생성 파일**: `agents/spec_agent.py`, `agents/prompts/spec_prompt.py`, `tests/test_spec_agent.py`
- **검증 포인트**: 다양한 입력으로 파싱 결과 확인

### Step 14 — Image Analysis Agent (OpenCV 전용)
- **작업 내용**: OpenCV로 ImageDiagnosis 기본 광학 수치 계산 (contrast, noise_level, edge_density, illumination_type, noise_frequency FFT 등). ROI 영역 집중 분석
- **생성 파일**: `agents/image_analysis_agent.py`, `tests/test_image_analysis.py`
- **검증 포인트**: 샘플 이미지로 각 수치 출력 확인

### Step 15 — Depth Agent (Depth-Anything-V2)
- **작업 내용**: Depth-Anything-V2 모델 로더. 이미지 → Depth Map (numpy array). ROI 영역의 깊이 복잡도 수치화
- **생성 파일**: `agents/depth_agent.py`, `tests/test_depth_agent.py`
- **검증 포인트**: 샘플 이미지로 Depth Map 시각화 확인, 깊이 통계 출력 확인

### Step 16 — Material Agent (Florence-2 + DINOv2)
- **작업 내용**: Florence-2로 재질 영역 1차 분류. DINOv2로 특징 벡터 추출 → 표준 재질 LUT(Look-up Table)와 매칭하여 픽셀별 surface_type 결정. 학술 표준 수치 LUT 구축
- **생성 파일**: `agents/material_agent.py`, `agents/material_lut.py`, `tests/test_material_agent.py`
- **검증 포인트**: 금속/플라스틱/유리 등 분류 확인, LUT 매칭 결과 확인

### Step 17 — ROI Agent (Grounding DINO + SAM 2)
- **작업 내용**: 사용자가 마우스로 그린 사각형 ROI 처리. 선택적으로 텍스트 입력 시 Grounding DINO로 위치 찾고 SAM 2로 정밀 분할 → ROI 자동 추천
- **생성 파일**: `agents/roi_agent.py`, `tests/test_roi_agent.py`
- **검증 포인트**: 사각형 ROI 처리, 텍스트 기반 자동 ROI 추천 결과 확인

### Step 18 — 분석 결과 통합 모듈
- **작업 내용**: Image Analysis + Depth + Material + ROI 결과를 하나의 `SceneContext`로 병합. 후속 에이전트들이 참조할 통합 데이터 구조
- **생성 파일**: `agents/scene_context.py`, `tests/test_scene_context.py`
- **검증 포인트**: 통합 데이터 구조 생성 및 모든 필드 채워짐 확인

### Step 19 — Vision Judge Agent (Qwen2.5-VL)
- **작업 내용**: Qwen2.5-VL에 원본 + 처리 이미지 2장 + 검사 목적 전달. 가시성/분리도/측정가능성 점수화. 문제점 + 개선 방향 출력. Agent Directive 반영
- **생성 파일**: `agents/vision_judge_agent.py`, `agents/prompts/vision_judge_prompt.py`, `tests/test_vision_judge.py`
- **검증 포인트**: 좋은 처리 vs 나쁜 처리 판별, 개선 제안 출력 확인

---

## Phase 4: 파이프라인 설계

### Step 20 — Pipeline Block Library
- **작업 내용**: 모든 처리 블록 정의 (색공간/노이즈/임계값/모폴로지/엣지). 조건 매칭 로직. 파라미터 탐색 범위
- **생성 파일**: `agents/pipeline_blocks.py`, `tests/test_pipeline_blocks.py`
- **검증 포인트**: SceneContext 조건별 블록 매칭 결과 확인

### Step 21 — Pipeline Composer
- **작업 내용**: SceneContext + Block Library → 후보 파이프라인 3~5개 생성. 블록 순서 결정. Agent Directive 반영. CLAHE 같은 적합한 방식이 자동으로 검토되는지 검증
- **생성 파일**: `agents/pipeline_composer.py`, `tests/test_pipeline_composer.py`
- **검증 포인트**: 불균일 조명 이미지에 CLAHE 포함된 파이프라인 생성되는지 확인

### Step 22 — Parameter Searcher + ProcessingQualityEvaluator
- **작업 내용**: 파라미터 자동 탐색 (sigma/kernel/threshold 범위). ProcessingQualityEvaluator로 빠른 필터링 (OpenCV 수치)
- **생성 파일**: `agents/parameter_searcher.py`, `agents/processing_quality_evaluator.py`, `tests/test_parameter_searcher.py`
- **검증 포인트**: 탐색 후 최적 파라미터 출력 확인

### Step 23 — Algorithm Selector (결정 트리)
- **작업 내용**: SceneContext 수치 기반 Python 결정 트리. BLOB/COLOR_FILTER/EDGE/TEMPLATE 카테고리 확정. LLM override 불가
- **생성 파일**: `agents/algorithm_selector.py`, `tests/test_algorithm_selector.py`
- **검증 포인트**: 다양한 SceneContext로 카테고리 선택 결과 확인

### Step 24 — Inspection Plan Agent
- **작업 내용**: 검사 목적 → 자유로운 검사 항목 설계. 항목별 depends_on/safety_role/success_criteria. 고정 템플릿 없음. 타공 검사 같은 경우 오인식 방지 항목 자동 포함
- **생성 파일**: `agents/inspection_plan_agent.py`, `agents/prompts/inspection_plan_prompt.py`, `tests/test_inspection_plan.py`
- **검증 포인트**: 타공/스크래치 등 다양한 목적으로 다른 항목 구성 확인

### Step 25 — Vision Judge 기반 파이프라인 선정 루프
- **작업 내용**: Composer가 생성한 후보 파이프라인 각각에 Parameter Searcher + Quality Evaluator + Vision Judge 적용 → 최고 점수 파이프라인 확정
- **생성 파일**: `agents/pipeline_selection.py`, `tests/test_pipeline_selection.py`
- **검증 포인트**: 후보 비교 후 최적 파이프라인 선정 동작 확인

### Step 26 — Test Agent (Inspection, 항목별 OpenCV 실행)
- **작업 내용**: InspectionPlan 항목별 OpenCV 코드 내부 실행. 항목별 Accuracy/FP/FN 계산. depends_on 순서 준수. Agent Directive 반영
- **생성 파일**: `agents/test_agent_inspection.py`, `tests/test_test_agent_inspection.py`
- **검증 포인트**: 항목별 메트릭 출력 및 의존성 순서 확인

### Step 27 — Test Agent (Align)
- **작업 내용**: Align 코드 실행. 좌표 오차/성공률 계산. Template → Edge → Caliper Fallback 체인
- **생성 파일**: `agents/test_agent_align.py`, `tests/test_test_agent_align.py`
- **검증 포인트**: Fallback 체인 동작 + 좌표 오차 계산 확인

---

## Phase 5: Blueprint + 평가 루프

### Step 28 — Blueprint Agent (SVG 다이어그램 생성)
- **작업 내용**: 확정된 파이프라인 + Inspection Plan → SVG 다이어그램 생성. 노드 (Preprocessing/Feature/Inspection/Decision) + 연결선. Auto-layout. 한국어 알고리즘 설명
- **생성 파일**: `agents/blueprint_agent.py`, `agents/prompts/blueprint_prompt.py`, `tests/test_blueprint_agent.py`
- **검증 포인트**: SVG 파일 생성 확인, 노드/엣지 정상 배치 확인

### Step 29 — 파라미터 시트 생성기
- **작업 내용**: 각 Blueprint 노드의 파라미터를 수학적 의미 기반으로 정리 (예: "Otsu 자동", "히스토그램 하위 15%"). 라이브러리 독립적 표현
- **생성 파일**: `agents/parameter_sheet.py`, `tests/test_parameter_sheet.py`
- **검증 포인트**: 각 노드별 파라미터 시트 출력 형식 확인

### Step 30 — Evaluation Agent
- **작업 내용**: 항목별 실패 원인 분석. `failure_reason` 6가지 세분화 (pipeline_bad_fit / pipeline_bad_params / algorithm_wrong_category / runtime_error / inspection_plan_issue / spec_issue)
- **생성 파일**: `agents/evaluation_agent.py`, `tests/test_evaluation_agent.py`
- **검증 포인트**: 각 failure_reason 경계 케이스 확인

### Step 31 — Feedback Controller
- **작업 내용**: failure_reason별 재시도 전략. Vision Judge 피드백 반영. 실패 컨텍스트 누적
- **생성 파일**: `agents/feedback_controller.py`, `tests/test_feedback_controller.py`
- **검증 포인트**: 전략 선택 및 컨텍스트 누적 확인

### Step 32 — Decision Agent (InternVL + DINOv2 통계)
- **작업 내용**: Rule-based 유지 / EL / DL 최종 판단. DINOv2 특징 변동성 통계 + InternVL 시각적 패턴 분석. 목표 수치 달성 불가 여부를 핵심 근거로. Align 모드는 HW 개선만
- **생성 파일**: `agents/decision_agent.py`, `agents/prompts/decision_prompt.py`, `tests/test_decision_agent.py`
- **검증 포인트**: EL/DL/Rule-based 각 시나리오 및 근거 출력 확인

### Step 33 — Orchestrator (기본 파이프라인 + Retry + Decision 연결)
- **작업 내용**: 전체 파이프라인 순차 실행. 목표 수치 사전 검증. Directive 각 에이전트 전달. failure_reason별 재시도 분기 (6가지). max_iteration 초과 시 Decision Agent 호출
- **생성 파일**: `agents/orchestrator.py`, `tests/test_orchestrator.py`
- **검증 포인트**: Mock 에이전트로 전체 흐름 + 재시도 + Decision 호출 확인

### Step 34 — 파이프라인 실행 API + 조명 권장사항 출력
- **작업 내용**: `POST /api/execute` (비동기 실행). `execution_id` 발급. 상태 조회/취소. 결과에 Blueprint SVG + 파라미터 시트 + **조명 권장사항** 포함 (Material Agent + Image Analysis 결과 기반)
- **생성 파일**: `backend/routers/execute.py`, `backend/services/execution_manager.py`, `agents/lighting_advisor.py`, `tests/test_execute_api.py`
- **검증 포인트**: 비동기 실행, 상태 폴링, 조명 권장사항 텍스트 출력 확인

---

## Phase 6: 메인 프론트엔드

> Phase 6~7의 모든 UI Step은 **Part 3.6 UI 디자인 규칙**을 반드시 준수한다.

### Step 35 — Electron + React + TypeScript + TailwindCSS 초기화
- **작업 내용**: Electron, electron-builder, Vite, React, TypeScript. TailwindCSS black/gray 다크 테마. 디자인 토큰 정의 (`design-tokens.ts`). lucide-react. ESLint + Prettier
- **생성 파일**: `frontend/main.js`, `frontend/src/App.tsx`, `frontend/tailwind.config.js`, `frontend/src/styles/design-tokens.ts`
- **검증 포인트**: Electron 윈도우에서 다크 배경(#0a0a0a) 렌더링 확인

### Step 36 — Redux Store + API 클라이언트
- **작업 내용**: 전체 Store 구현 (project, engine, images, roi, config, directives, execution, result, light_test, logs). axios 인스턴스. 각 API 함수화. TypeScript 타입
- **생성 파일**: `frontend/src/store/index.ts`, `frontend/src/store/slices/*.ts`, `frontend/src/services/api.ts`, `frontend/src/services/types.ts`
- **검증 포인트**: Redux DevTools에서 슬라이스 확인, API 호출 동작 확인

### Step 37 — 전체 레이아웃 + Input Panel
- **작업 내용**: Sidebar + Main Workspace 레이아웃. 드래그&드롭 이미지 업로드. OK/NG 파일명 검증. 썸네일
- **생성 파일**: `frontend/src/components/Layout.tsx`, `frontend/src/components/panels/InputPanel.tsx`
- **검증 포인트**: 기능 동작 + UI 품질 확인

### Step 38 — ROI 드로잉 UI (첫 이미지 위 사각형)
- **작업 내용**: 첫 번째 로드된 이미지를 캔버스에 표시. 마우스 드래그로 사각형 ROI 그리기. ROI 좌표 표시 및 수정/삭제. `POST /api/roi` 연동
- **생성 파일**: `frontend/src/components/ROICanvas.tsx`, `frontend/src/hooks/useROIDrawing.ts`
- **검증 포인트**: 마우스 드래그로 사각형 그려지고 좌표 저장 확인

### Step 39 — Engine 설정 + Directive Panel
- **작업 내용**: Engine 설정 UI (Local/Remote, URL 입력). 각 에이전트 카드마다 선택적 텍스트 입력란. 빈 값 = 자동 판단. 접기/펼치기
- **생성 파일**: `frontend/src/components/panels/EnginePanel.tsx`, `frontend/src/components/panels/DirectivePanel.tsx`
- **검증 포인트**: Engine 설정 전환 동작, Directive 입력 및 저장 확인

### Step 40 — Config Panel + Execution Panel
- **작업 내용**: 모드 토글. 성공 기준 폼. 극단 목표 경고. 실행 시작/중지. 에이전트별 진행 상태. 폴링 업데이트
- **생성 파일**: `frontend/src/components/panels/ConfigPanel.tsx`, `frontend/src/components/panels/ExecutionPanel.tsx`
- **검증 포인트**: 기능 동작 + 로딩/에러 상태 UI 확인

### Step 41 — Result Panel (Blueprint Viewer + 메트릭 + 조명 권장사항)
- **작업 내용**: SVG Blueprint 뷰어 (확대/축소/팬). 노드 클릭 시 파라미터 시트 사이드 패널 표시. 항목별 검사 결과 테이블. 과검/미검 차트. **조명 권장사항 카드** ("Light Test로 가서 검증해보세요" 버튼 포함). Decision 결과 강조. SVG/PDF 내보내기
- **생성 파일**: `frontend/src/components/panels/ResultPanel.tsx`, `frontend/src/components/BlueprintViewer.tsx`, `frontend/src/components/ParameterSheet.tsx`, `frontend/src/components/MetricsChart.tsx`, `frontend/src/components/LightingSuggestion.tsx`
- **검증 포인트**: SVG 렌더링, 노드 클릭 인터랙션, 조명 권장사항 표시 확인

---

## Phase 7: Light Test 윈도우

### Step 42 — Light Test 윈도우 + 별도 이미지 업로드 + 듀얼 뷰 레이아웃
- **작업 내용**: 메뉴에서 Light Test 윈도우 별도 오픈. 메인과 완전히 분리된 이미지 업로드. 정면도/평면도 듀얼 뷰 캔버스 레이아웃. 좌측: 정면도, 우측: 평면도. 우측 사이드: 조명 컨트롤 패널
- **생성 파일**: `frontend/src/components/light_test/LightTestWindow.tsx`, `frontend/src/components/light_test/DualViewLayout.tsx`
- **검증 포인트**: 별도 윈도우 오픈, 이미지 업로드, 듀얼 뷰 레이아웃 표시 확인

### Step 43 — Depth + Material 분석 백엔드 연동
- **작업 내용**: Light Test 전용 분석 API (`POST /api/light_test/analyze`). 업로드 이미지에 Depth Agent + Material Agent 적용. Depth Map + Material Map 반환. Canvas에 데이터 로드
- **생성 파일**: `backend/routers/light_test.py`, `frontend/src/services/light_test_api.ts`, `tests/test_light_test_api.py`
- **검증 포인트**: Depth Map + Material Map 시각화 확인

### Step 44 — 조명 배치 UI (정면도 + 평면도 동기화)
- **작업 내용**: 조명 객체를 두 뷰에서 동시에 표시. 정면도에서 X/Y/Pitch 조정, 평면도에서 X/Z/Yaw/LWD 조정. 두 뷰가 동일 조명 객체의 다른 시점 보여주도록 동기화. 조명 형상 선택 (Ring/Bar/Spot/Coaxial/Dome/Low-angle Ring). 조명 타입 선택 (LED/Halogen/UV/IR). 크기/각도 조절
- **생성 파일**: `frontend/src/components/light_test/FrontView.tsx`, `frontend/src/components/light_test/TopView.tsx`, `frontend/src/components/light_test/LightController.tsx`, `frontend/src/hooks/useLightSync.ts`
- **검증 포인트**: 정면도에서 이동 시 평면도도 동기화, 조명 형상/타입 변경 확인

### Step 45 — PBR 렌더링 엔진 (Depth > Material 우선순위)
- **작업 내용**: Canvas 2D 기반 렌더링. **Depth 우선**: 조명 위치 기반 그림자 영역 먼저 계산 (Depth-Anything-V2의 Z 맵 활용). **Material 후처리**: 그림자 영역이 아닌 곳에서만 재질별 Specular/Diffuse 적용 (학술 LUT 기반). 실시간 렌더링
- **생성 파일**: `light_test/renderer.py`, `light_test/material_pbr.py`, `light_test/lighting_models.py`, `frontend/src/components/light_test/RenderEngine.tsx`, `tests/test_renderer.py`
- **검증 포인트**: 조명 이동 시 그림자/하이라이트 변화 확인, 금속 재질 정반사 표현 확인

### Step 46 — 컬러 조명 + 편광 시뮬레이션
- **작업 내용**:
  - **컬러 조명**: RGB 채널 곱셈 연산. Color Picker UI. Gray 이미지 업로드 시 컬러 기능 비활성화 + 안내 메시지
  - **편광 (조명측)**: 형상별 체크박스 (Ring/Bar/Coaxial/Dome 적용 가능, Spot은 별도 다이얼)
  - **편광 (렌즈측)**: 0~180° 다이얼. 말루스의 법칙 `I = I₀·cos²θ` 적용. 금속 정반사 영역에 교차 편광 시 광량 감쇄
  - 히스토그램 실시간 업데이트
- **생성 파일**: `light_test/polarization.py`, `frontend/src/components/light_test/ColorLightControl.tsx`, `frontend/src/components/light_test/PolarizerControl.tsx`, `frontend/src/components/light_test/HistogramPanel.tsx`, `tests/test_polarization.py`
- **검증 포인트**: Gray 이미지에서 컬러 기능 비활성화, 렌즈 편광 다이얼 회전 시 금속 정반사 소멸 확인

---

## Phase 8: 통합 / 패키징 / 배포

### Step 47 — 전체 E2E 테스트 (Inspection + Align + Directive)
- **작업 내용**: 샘플 이미지 + ROI + Directive 시나리오. Vision Judge + Inspection Plan + Blueprint 생성 전체 흐름. Align Fallback 체인. 실제 AI 모델 호출 포함
- **생성 파일**: `tests/e2e/test_inspection_pipeline.py`, `tests/e2e/test_align_pipeline.py`, `tests/e2e/test_directive_e2e.py`, `tests/fixtures/sample_images/`
- **검증 포인트**: 각 시나리오 성공/실패/재시도/Decision 호출 확인

### Step 48 — Light Test E2E + 결과 내보내기
- **작업 내용**: Light Test 윈도우 E2E (이미지 업로드 → 조명 배치 → 편광 조작 → 렌더링 결과 확인). 메인 결과 SVG/PDF 내보내기. 파라미터 시트 JSON 내보내기. Light Test 프리셋 저장/불러오기
- **생성 파일**: `tests/e2e/test_light_test_e2e.py`, `backend/routers/export.py`, `frontend/src/components/ExportButton.tsx`
- **검증 포인트**: Light Test 모든 조작 동작, SVG/PDF/JSON 파일 정상 출력 확인

### Step 49 — FastAPI 자동 시작 + 모델 상태 확인 + macOS DMG 패키징
- **작업 내용**: Electron 시작 시 FastAPI 자동 실행. AI Engine 상태 확인 (로컬 Ollama 실행 여부, 원격 URL 연결 가능 여부). 미연결 시 안내 모달. electron-builder로 macOS Intel x86_64 DMG 패키징
- **생성 파일**: `frontend/main.js` 확장, `frontend/src/components/EngineSetupGuide.tsx`, `frontend/electron-builder.yml`, `build/icons/`
- **검증 포인트**: 앱 시작 시 서버 자동 실행, Ollama 안내 모달, DMG 생성 및 설치 후 실행 확인

### Step 50 — 문서화 + 최종 통합 테스트 + 배포 준비
- **작업 내용**: 패키징 앱으로 5개 시나리오 전체 테스트 (Inspection 성공, Directive 영향, EL/DL Decision, Align 모드, Light Test). README/INSTALL/MODEL_SETUP/LIMITATIONS 문서 완성. `.env.example`. progress.md 전체 완료
- **생성 파일**: `tests/e2e/test_final_integration.md`, `README.md`, `docs/INSTALL.md`, `docs/MODEL_SETUP.md`, `docs/LIMITATIONS.md`, `progress.md`, `.env.example`
- **검증 포인트**: 패키징 앱에서 5개 시나리오 통과, 문서 내용 검토

