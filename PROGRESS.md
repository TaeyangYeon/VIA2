# VIA2 Progress

## 현재 진행 단계: Step 43 (완료)

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
- [x] Step 24: Inspection Plan Agent
- [x] Step 25: Vision Judge 기반 파이프라인 선정 루프 (PipelineSelector)
- [x] Step 26: Test Agent (Inspection, 항목별)

- [x] Step 27: Test Agent (Align)

## Phase 5: Blueprint + 평가 루프
- [x] Step 28: Blueprint Agent (SVG 다이어그램)
- [x] Step 29: 파라미터 시트 생성기
- [x] Step 30: Evaluation Agent
- [x] Step 31: Feedback Controller
- [x] Step 32: Decision Agent (InternVL + DINOv2 통계)
- [x] Step 33: Orchestrator (기본 + Retry + Decision 연결)
- [x] Step 34: 파이프라인 실행 API + 조명 권장사항

## Phase 6: 메인 프론트엔드
- [x] Step 35: Electron + React + TypeScript + TailwindCSS 초기화
- [x] Step 36: Redux Store + API 클라이언트
- [x] Step 37: 전체 레이아웃 + Input Panel
- [x] Step 38: ROI 드로잉 UI
- [x] Step 39: Engine 설정 + Directive Panel
- [x] Step 40: Config Panel + Execution Panel
- [x] Step 41: Result Panel (Blueprint Viewer)

## Phase 7: Light Test 윈도우
- [x] Step 42: Light Test 윈도우 + 듀얼 뷰 레이아웃
- [x] Step 43: Depth + Material 분석 백엔드 연동
- [ ] Step 44: 조명 배치 UI (정면도/평면도 동기화)
- [ ] Step 45: PBR 렌더링 엔진
- [ ] Step 46: 컬러 조명 + 편광 시뮬레이션

## Phase 8: 통합 / 패키징 / 배포
- [ ] Step 47: 전체 E2E 테스트
- [ ] Step 48: Light Test E2E + 결과 내보내기
- [ ] Step 49: FastAPI 자동 시작 + macOS DMG 패키징
- [ ] Step 50: 문서화 + 최종 통합 테스트

---

## Step 43 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `backend/routers/light_test.py` | `POST /api/light_test/analyze` 엔드포인트 | 신규 생성 |
| `backend/main.py` | light_test_router 등록 | 수정 |
| `tests/test_light_test_api.py` | 백엔드 API 테스트 26개 | 신규 생성 |
| `frontend/src/services/light_test_api.ts` | 프론트엔드 Light Test API 서비스 | 신규 생성 |
| `frontend/src/store/slices/lightTestSlice.ts` | 분석 상태/액션 4종 추가 | 수정 |
| `frontend/src/components/light_test/LightTestWindow.tsx` | 분석 트리거 + UI 상태 표시 | 수정 |
| `frontend/src/components/light_test/DualViewLayout.tsx` | 깊이맵 오버레이 + surface type 뱃지 | 수정 |
| `frontend/src/__tests__/LightTestWindow.test.tsx` | 분석 상태 테스트 7개 추가 | 수정 |
| `frontend/src/__tests__/DualViewLayout.test.tsx` | 깊이/재질 표시 테스트 6개 추가 | 수정 |
| `frontend/src/__tests__/light_test_api.test.ts` | API 서비스 테스트 9개 | 신규 생성 |
| `frontend/src/__tests__/slices.test.ts` | lightTestSlice 신규 액션 8개 추가 | 수정 |
| `frontend/src/__tests__/store.test.ts` | light_test 초기 상태 갱신 | 수정 |

### 백엔드 엔드포인트

| 항목 | 값 |
|------|----|
| Method | POST |
| Path | `/api/light_test/analyze` |
| Request | `multipart/form-data` — `file: UploadFile` |
| Response status | `"success"` / `"partial"` / `"error"` |
| depth 필드 | `status`, `depth_stats`, `depth_map_shape`, `depth_map_base64`, `error_message` |
| material 필드 | `status`, `surface_type`, `material_map`, `confidence`, `error_message` |
| 엔진 체크 | local 모드 → HTTP 400 |
| 잘못된 이미지 | HTTP 422 |
| 동시 실행 | `asyncio.gather()` 로 DepthAgent + MaterialAgent 병렬 실행 |

### 프론트엔드 API 서비스 (`light_test_api.ts`)

| 인터페이스 | 설명 |
|-----------|------|
| `DepthAnalysisResult` | status, depth_stats, depth_map_shape, depth_map_base64, error_message |
| `MaterialAnalysisResult` | status, surface_type, material_map, confidence, error_message |
| `LightTestAnalysisResponse` | status, depth, material |
| `analyzeLightTestImage(file)` | FormData POST → `/api/light_test/analyze` |

### lightTestSlice 상태 변경

| 신규 필드 | 타입 | 초기값 |
|-----------|------|--------|
| `analysis_status` | `'idle' \| 'loading' \| 'success' \| 'partial' \| 'error'` | `'idle'` |
| `depth_result` | `DepthAnalysisResult \| null` | `null` |
| `material_result` | `MaterialAnalysisResult \| null` | `null` |
| `analysis_error` | `string \| null` | `null` |

| 신규 액션 | 설명 |
|-----------|------|
| `setAnalysisLoading()` | status → loading, results 초기화 |
| `setAnalysisResult({depth, material, status})` | 분석 결과 저장 |
| `setAnalysisError(message)` | 에러 메시지 저장 |
| `clearAnalysis()` | 분석 상태 idle/null 초기화 |

### LightTestWindow UI 변경

| data-testid | 조건 | 설명 |
|-------------|------|------|
| `lt-analysis-loading` | `analysis_status === 'loading'` | "Analyzing depth & material…" + spinner |
| `lt-analysis-complete` | `analysis_status === 'success' \| 'partial'` | 녹색 뱃지 |
| `lt-analysis-error` | `analysis_status === 'error'` | 빨간 에러 메시지 |

### DualViewLayout 변경

- Front View 캔버스: `depth_map_base64` 존재 시 40% 투명도로 깊이맵 오버레이
- Top View: `depth_map_base64` 없으면 "Depth data required" 텍스트 표시, 있으면 깊이맵 렌더링
- Light Controls: `material_result.surface_type` 있으면 `surface-type-badge` (data-testid) 표시

### 테스트 커버리지

| 테스트 파일 | 신규 테스트 수 | 내용 |
|-------------|-------------|------|
| `test_light_test_api.py` | 26 (신규) | 백엔드 엔드포인트 전체 시나리오 |
| `LightTestWindow.test.tsx` | +7 | 분석 로딩/성공/부분/에러 상태 UI |
| `DualViewLayout.test.tsx` | +6 | 깊이맵/재질 결과 표시 |
| `light_test_api.test.ts` | 9 (신규) | API 서비스 함수 |
| `slices.test.ts` | +8 | lightTestSlice 신규 액션 |
| `store.test.ts` | +0 (수정 1) | 초기 상태 필드 갱신 |

### Jest 결과

```
Test Suites: 21 passed, 21 total
Tests:       443 passed, 443 total
Time:        ~4.8s
```

### TypeScript 검사 결과

```
npx tsc --noEmit → 오류 없음 (0 errors)
```

### pytest 결과

```
tests/test_light_test_api.py: 26 passed
전체: 1688 passed, 5 skipped (신규 26 추가)
```

---

## Step 42 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `frontend/src/components/light_test/LightTestWindow.tsx` | Light Test 전용 윈도우 컴포넌트 | 신규 생성 |
| `frontend/src/components/light_test/DualViewLayout.tsx` | 듀얼 뷰 레이아웃 (정면도/평면도/Light Controls) | 신규 생성 |
| `frontend/src/__tests__/LightTestWindow.test.tsx` | LightTestWindow 테스트 (20개) | 신규 생성 |
| `frontend/src/__tests__/DualViewLayout.test.tsx` | DualViewLayout 테스트 (15개) | 신규 생성 |
| `frontend/main.js` | Electron 멀티 윈도우 IPC + Tools 메뉴 | 수정 |
| `frontend/preload.js` | contextBridge로 electronAPI 노출 | 신규 생성 |
| `frontend/src/App.tsx` | `#/light-test` 해시 라우팅 추가 | 수정 |
| `frontend/src/components/LightingSuggestion.tsx` | Open Light Test 버튼 IPC 연결 | 수정 |
| `frontend/src/components/Layout.tsx` | Light Test 사이드바 항목 추가 | 수정 |
| `frontend/src/__tests__/LightingSuggestion.test.tsx` | window.open 동작 반영으로 테스트 갱신 | 수정 |

### LightTestWindow 기능 목록

| 기능 | data-testid |
|------|-------------|
| 루트 컨테이너 | `light-test-window` |
| 헤더 바 ("VIA2 — Light Test") | `light-test-header` |
| 드래그 앤 드롭 존 | `lt-drop-zone` |
| 빈 상태 안내 | `lt-empty-state` |
| 파일 인풋 (항상 존재, hidden) | `lt-file-input` |
| 파일 찾아보기 버튼 | `lt-browse-btn` |
| 업로드 중 로딩 상태 | `lt-loading-state` |
| 업로드 실패 에러 상태 | `lt-error-state` |
| 업로드된 이미지 썸네일 | `lt-image-thumbnail` |
| 이미지 제거 버튼 | `lt-remove-btn` |
| 듀얼 뷰 레이아웃 (이미지 로드 후 표시) | `dual-view-layout` |

### DualViewLayout 기능 목록

| 기능 | data-testid |
|------|-------------|
| 루트 컨테이너 | `dual-view-layout` |
| 정면도 패널 (45%) | `front-view-panel` |
| 정면도 캔버스 | `front-view-canvas` |
| 평면도 패널 (45%) | `top-view-panel` |
| 평면도 캔버스 | `top-view-canvas` |
| Light Controls 사이드바 | `light-controls-panel` |
| Add Light 버튼 | `add-light-btn` |

### Electron main.js 변경 사항

- `ipcMain.on('open-light-test')` 핸들러 추가
- `createLightTestWindow()` 함수: 1200×800 BrowserWindow, `#/light-test` 해시 경로 로드
- 이미 열려 있으면 포커스, 닫히면 참조 null 처리
- `Tools > Light Test` 메뉴 항목 추가 (단축키: Cmd+Shift+L)
- `preload.js` 경로 참조 추가

### App.tsx 라우팅 변경 사항

- `window.location.hash === '#/light-test'` 조건으로 분기
- hash 일치 시 `<LightTestWindow />` 렌더, 아니면 기존 `<Layout />` 렌더
- JSDOM 기본값 `hash = ''`이므로 기존 App 테스트 전부 통과

### LightingSuggestion.tsx 변경 사항

- `window.alert` → `window.electronAPI?.openLightTest()` (contextBridge) 우선 시도
- Electron 없는 환경(웹 개발 모드)에서는 `window.open('#/light-test', '_blank')` 폴백

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 내용 |
|-------------|---------|------|
| `LightTestWindow.test.tsx` | 20 | 렌더링, 업로드 플로우, 에러/로딩 상태, Redux dispatch |
| `DualViewLayout.test.tsx` | 15 | 레이아웃 구조, 캔버스 요소, 레이블, 이미지 preload |
| `LightingSuggestion.test.tsx` | 9 | 기존 9개 (window.open 동작 반영) |

### Jest 결과

```
Test Suites: 20 passed, 20 total
Tests:       413 passed, 413 total  (기존 376 + 신규 36 + 기존 수정 1)
Time:        ~4.3s
```

### TypeScript 검사 결과

```
npx tsc --noEmit → 오류 없음 (0 errors)
```

### 주요 구현 노트

- JSDOM 호환: `style={{ display: 'none' }}` 패턴 유지, Tailwind `hidden` 미사용
- Canvas mock: `jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(mockCtx)` 패턴 적용
- Light Test 이미지 업로드는 `light_test` Redux 슬라이스 전용 (`images` 슬라이스 미사용)
- OK_/NG_ 파일명 검증 없음 — 임의 파일명 허용
- `contextBridge`를 통한 IPC (`preload.js` 신규 생성) + `window.open` 폴백 구조
- `DualViewLayout`의 Top View는 "Depth data required" 텍스트를 DOM 요소로 표시 (canvas.fillText는 DOM 접근 불가)

### 이슈 및 특이사항

- `preload.js`가 `main.js`에서 참조되었으나 파일이 없었음 → 신규 생성
- 기존 `LightingSuggestion.test.tsx`에서 `window.alert` 검증 → `window.open` 검증으로 업데이트 (변경된 동작에 맞게 수정)
- `DualViewLayout`의 Light Controls는 Step 45(PBR 렌더링) 이전까지 플레이스홀더로 유지

---

## Step 39 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `frontend/src/components/panels/EnginePanel.tsx` | AI Engine 설정 UI (Local/Remote 모드 전환, 저장, 연결 테스트) | 신규 |
| `frontend/src/components/panels/DirectivePanel.tsx` | 9개 에이전트 Directive 편집 UI (카드 접기/펼치기, 전체 저장/초기화) | 신규 |
| `frontend/src/__tests__/EnginePanel.test.tsx` | EnginePanel 컴포넌트 단위 테스트 (22개) | 신규 |
| `frontend/src/__tests__/DirectivePanel.test.tsx` | DirectivePanel 컴포넌트 단위 테스트 (18개) | 신규 |
| `frontend/src/components/Layout.tsx` | Engine/Directive 플레이스홀더 → 실제 컴포넌트 교체 | 수정 |
| `PROGRESS.md` | 진행 기록 업데이트 | 수정 |

### EnginePanel 기능 목록

- **모드 토글**: Local (Ollama) / Remote 라디오 버튼 전환
- **Local 모드 필드**: `local_ollama_url` 입력, `model_name` 입력
- **Remote 모드 필드**: `remote_type` select (colab/azure/custom), `remote_url` 입력, `remote_auth_token` 패스워드 입력
- **연결 테스트**: "Test Connection" 버튼 → `getEngine()` 호출 → 성공/실패 피드백 (`connection-success` / `connection-error`)
- **저장**: "Save" 버튼 → `updateEngine()` POST + Redux `setEngine` dispatch
- **저장 상태**: 저장 중 `save-loading` 인디케이터, 완료 후 `save-success` / `save-error` 피드백 (3~4초 자동 소멸)
- **Redux 초기화**: 마운트 시 `store.engine` 값으로 필드 초기화
- **UI 스타일**: glass morphism (bg-white/5 backdrop-blur border-white/10), 중성 다크 테마, 전환 transition-all duration-150

### DirectivePanel 기능 목록

- **9개 에이전트 카드**: orchestrator, spec, image_analysis, depth, material, pipeline_composer, vision_judge, inspection_plan, test
- **에이전트 레이블**: Orchestrator, Spec Agent, Image Analysis, Depth Agent, Material Agent, Pipeline Composer, Vision Judge, Inspection Plan, Test Agent
- **카드 접기/펼치기**: 헤더 클릭으로 토글, 기본값 전체 접힘 (`style={{ display: 'none' }}` — JSDOM 호환)
- **빈 값 표시**: 값이 비어있으면 "auto" 힌트 표시
- **텍스트 미리보기**: 값이 있으면 헤더에 40자 축약 미리보기
- **Save All**: `saveDirectives()` POST + Redux `setDirectives` dispatch, 저장 중 `save-loading` 인디케이터
- **Clear All**: 모든 필드를 빈 문자열로 리셋 (API 호출 없음)
- **성공/에러 피드백**: `save-success` / `save-error` (3~4초 자동 소멸)
- **Redux 초기화**: 마운트 시 `store.directives` 값으로 필드 초기화
- **로컬 상태**: `useState<AgentDirectives>` 로 로컬 편집, Save All 시 Redux 동기화

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `EnginePanel.test.tsx` | 22 | ✅ PASS |
| `DirectivePanel.test.tsx` | 18 | ✅ PASS |
| 기존 전체 (Step 38까지) | 214 | ✅ PASS (회귀 없음) |

### Jest 결과

```
Test Suites: 11 passed, 11 total
Tests:       254 passed, 254 total (신규 40 + 기존 214)
Time:        ~3.2s
```

### TypeScript 검사 결과

```
npx tsc --noEmit → 오류 없음 (출력 없음)
```

### 주요 구현 노트

- **JSDOM 호환 접기**: TailwindCSS `hidden` 클래스 대신 `style={{ display: isExpanded ? 'block' : 'none' }}` 사용 — JSDOM은 Tailwind 클래스를 실제로 적용하지 않으므로 `toBeVisible()` 테스트가 실패함. `style` 인라인은 JSDOM에서 정확히 동작함
- **로컬 상태 vs Redux**: 편집 중에는 로컬 `useState`로 관리하고, Save 성공 시에만 Redux 동기화 (불필요한 Redux 업데이트 방지)
- **updateEngine 시그니처**: `api.ts`에서 `updateEngine(settings: EngineSettings)`는 `Partial`이 아닌 전체 객체를 받으므로 `buildSettings()`로 전체 EngineSettings 구성 후 전달

---

## Step 40 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `frontend/src/components/panels/ConfigPanel.tsx` | 모드 토글, 최대 반복 수, 성공 기준 입력 폼, 극단 목표 경고, 저장 피드백 | 신규 |
| `frontend/src/components/panels/ExecutionPanel.tsx` | 실행 시작/중지, 에이전트 진행 표시, 상태 폴링, 목표 검증 경고 | 신규 |
| `frontend/src/__tests__/ConfigPanel.test.tsx` | ConfigPanel 단위 테스트 (30개) | 신규 |
| `frontend/src/__tests__/ExecutionPanel.test.tsx` | ExecutionPanel 단위 테스트 (22개) | 신규 |
| `frontend/src/components/Layout.tsx` | Config / Execution 플레이스홀더 → 실제 컴포넌트 교체 | 수정 |
| `PROGRESS.md` | 진행 기록 업데이트 | 수정 |

### ConfigPanel 기능 목록

- **모드 토글**: "Inspection" / "Align" 라디오 버튼 → `setConfig` dispatch
- **최대 반복 수**: number input (1–10 범위), 기본값 3, Redux `config.max_iteration` 초기화
- **성공 기준 — Inspection 모드**: accuracy, fp_rate, fn_rate 입력 (0–1 범위, nullable 숫자)
- **성공 기준 — Align 모드**: coord_error 입력 (양수, px 단위, nullable)
- **모드 기반 조건부 렌더링**: Inspection ↔ Align 전환 시 관련 필드만 표시 (조건부 렌더링으로 DOM에서 제거)
- **극단 목표 경고** (`extreme-goal-warning`): accuracy ≥ 0.99 · fp_rate ≤ 0.001 · fn_rate ≤ 0.001 · coord_error ≤ 0.5 중 하나라도 해당 시 노란색 경고 표시 (#facc15)
- **저장**: "Save" 버튼 → `api.saveConfig(config)` POST + Redux `setConfig` dispatch
- **저장 피드백**: 저장 중 `save-loading` 스피너, 성공 시 `save-success` (3초 소멸), 실패 시 `save-error` (4초 소멸)
- **Redux 초기화**: 마운트 시 `store.config` 값으로 로컬 상태 초기화

### ExecutionPanel 기능 목록

- **시작 버튼** (`start-btn`): `api.startExecution({ user_text: '' })` POST, 이미지 없으면 비활성화
- **중지 버튼** (`stop-btn`): `api.cancelExecution(execution_id)` DELETE, running 상태에서만 표시
- **에이전트 진행 표시**: `current_agent` 이름 + 펄스 점 인디케이터 (`current-agent-display`)
- **반복 카운터**: `current_iteration` / `max_iteration` (`iteration-counter`)
- **진행률 바**: 0–100% width 애니메이션 (`progress-bar`)
- **상태 폴링**: execution_id 설정 + running 상태일 때 `api.getExecution(execution_id)` 2초 간격 폴링, `setInterval` / `useEffect` cleanup으로 메모리 누수 방지
- **폴링 → Redux 업데이트**: 응답으로 execution 슬라이스 갱신, result 포함 시 `setResult` dispatch
- **폴링 종료 조건**: status가 completed / failed / cancelled 도달 시 clearInterval
- **상태별 UI**: idle(준비 메시지), running(진행 표시), completed(성공 메시지 + 재실행 버튼), failed(에러 메시지 + 재시도 버튼), cancelled(취소 메시지 + 재실행 버튼)
- **목표 검증 경고** (`goal-validation-warnings`): `execution.goal_validation.warnings` 항목 노란색 리스트 표시
- **실행 중 비활성화**: running 상태에서 start 버튼 숨김 (조건부 렌더링)

### API 서명 주의 사항

- `startExecution`: `ExecuteRequest = { user_text: string }` — 프롬프트 설명과 달리 실제 API는 단순 user_text만 받음. 백엔드가 저장된 config/directives를 직접 사용하므로 빈 user_text 전달.
- Execution 상태: executionSlice는 `'idle' | 'running' | 'completed' | 'failed' | 'cancelled'` 사용 (`'error'` 아님), API 응답의 `'pending'` → `'running'` 매핑 필요

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `ConfigPanel.test.tsx` | 30 | ✅ PASS |
| `ExecutionPanel.test.tsx` | 22 | ✅ PASS |
| 기존 전체 (Step 39까지) | 254 | ✅ PASS (회귀 없음) |

### Jest 결과

```
Test Suites: 13 passed, 13 total
Tests:       306 passed, 306 total (신규 52 + 기존 254)
```

### TypeScript 검사 결과

```
npx tsc --noEmit → 오류 없음 (출력 없음)
```

### 주요 구현 노트

- **combineReducers 해결**: ExecutionPanel 테스트에서 `configureStore`에 reducer 맵 + `preloadedState: any`를 동시에 사용 시 TypeScript 오버로드 해결 실패 문제 발생. `combineReducers`로 명시적 결합 후 단일 Reducer 함수로 전달하여 해결
- **조건부 렌더링**: ConfigPanel의 모드별 필드는 `style={{ display }}` 대신 조건부 렌더링(`{mode === 'inspection' && ...}`) 사용 — `toBeInTheDocument()` 테스트가 DOM 존재 여부를 확인하므로 조건부 렌더링이 정확
- **폴링 cleanup**: `useRef`로 interval ID 보관, `useEffect` return에서 `clearInterval` + `null` 초기화. 중지 후 재폴링 방지
- **API pending 상태 매핑**: 백엔드 `ExecutionStatus.status`는 `'pending'`을 포함하지만 Redux 슬라이스는 `'idle'`에서 시작하고 `'pending'`이 없음. 폴링 응답의 `'pending'` → `'running'` 변환 처리

---

## Step 41 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `frontend/src/components/panels/ResultPanel.tsx` | 결과 패널 컨테이너 — 빈 상태, Decision/Summary/Blueprint/Metrics/Lighting/Improvement 오케스트레이션 | 신규 |
| `frontend/src/components/BlueprintViewer.tsx` | SVG 블루프린트 렌더러 — 줌/팬/리셋/Fit 컨트롤, data-node-id 노드 클릭 감지 | 신규 |
| `frontend/src/components/ParameterSheet.tsx` | 노드 파라미터 사이드 패널 — isOpen 가시성 제어, 키-값 표시, 닫기 버튼 | 신규 |
| `frontend/src/components/MetricsChart.tsx` | 검사 결과 테이블 — pass/fail 색상 코딩, FP/FN CSS 바 시각화, 요약 행 | 신규 |
| `frontend/src/components/LightingSuggestion.tsx` | 조명 제안 카드 리스트 — 문자열 배열 렌더링, Open Light Test 버튼 | 신규 |
| `frontend/src/__tests__/ResultPanel.test.tsx` | ResultPanel 단위 테스트 (18개) | 신규 |
| `frontend/src/__tests__/BlueprintViewer.test.tsx` | BlueprintViewer 단위 테스트 (17개) | 신규 |
| `frontend/src/__tests__/ParameterSheet.test.tsx` | ParameterSheet 단위 테스트 (12개) | 신규 |
| `frontend/src/__tests__/MetricsChart.test.tsx` | MetricsChart 단위 테스트 (14개) | 신규 |
| `frontend/src/__tests__/LightingSuggestion.test.tsx` | LightingSuggestion 단위 테스트 (9개) | 신규 |
| `frontend/src/components/Layout.tsx` | Result 플레이스홀더 → `<ResultPanel />` 교체, 미사용 `PlaceholderPanel` 함수 제거 | 수정 |
| `PROGRESS.md` | 진행 기록 업데이트 | 수정 |

### ResultPanel 기능 목록

- **빈 상태** (`result-empty-state`): summary·blueprint_svg·decision 모두 null일 때 BarChart2 아이콘 + "No results yet" 안내 UI 표시
- **hasResult 판단**: `summary !== null || blueprint_svg !== null || decision !== null` 조건 — 셋 중 하나라도 non-null이면 결과 패널 표시
- **Summary 카드** (`result-summary`): `result.summary` 텍스트 표시
- **Decision 카드** (`decision-card`): `result.decision` 값에 따른 컬러 코딩 — `rule_based_ok`=#4ade80 / `edge_learning`=#facc15 / `deep_learning`=#60a5fa / `hw_improvement`=#f87171
- **Decision Reason** (`decision-reason`): `result.decision_reason` 보조 텍스트 표시
- **Blueprint Viewer**: `result.blueprint_svg` 있을 때 BlueprintViewer + ParameterSheet 나란히 렌더링
- **Parameter Sheet**: 노드 클릭 시 `selectedNodeId` 상태 설정 → ParameterSheet `isOpen=true`
- **Metrics 테이블**: `result.item_results` 있을 때 MetricsChart 렌더링
- **Lighting 권장사항**: `result.lighting_suggestions` 있을 때 LightingSuggestion 렌더링
- **Improvement 제안**: `result.improvement_suggestions` 불릿 리스트 표시
- **Export SVG** (`export-svg-btn`): `blueprint_svg` 있을 때만 표시 → `Blob` + `URL.createObjectURL` → 임시 `<a>` 태그 클릭으로 다운로드
- **Export PDF** (`export-pdf-btn`): 결과 있을 때 항상 표시 → `window.alert('PDF export coming soon')` 플레이스홀더

### BlueprintViewer 기능 목록

- **SVG 렌더링**: `dangerouslySetInnerHTML={{ __html: svgContent }}`로 SVG 문자열 직접 DOM 삽입 — 백엔드 생성 SVG의 모든 속성·스타일 원본 보존
- **줌 인/아웃** (`zoom-in-btn` / `zoom-out-btn`): 0.25 step, 0.25x ~ 4x 범위 클램프
- **스케일 표시** (`scale-display`): `{Math.round(scale * 100)}%` 텍스트 (초기값 100%)
- **리셋** (`reset-btn`): scale=1, translateX=0, translateY=0 초기화
- **Fit** (`fit-btn`): 현재 resetView와 동일 동작 (플레이스홀더 — 추후 컨테이너 크기 기반 auto-fit 구현 예정)
- **팬 (drag)**: `onMouseDown/Move/Up/Leave`로 translateX/Y 조정, `useRef`로 드래그 상태 관리 (불필요한 리렌더 방지)
- **노드 클릭**: `e.target.closest('[data-node-id]')` DOM 탐색 → `onNodeClick(nodeId)` 콜백 호출
- **onNodeClick 미전달 시 크래시 없음**: prop 없어도 안전하게 동작

### ParameterSheet 기능 목록

- **가시성 제어**: `style={{ display: isOpen ? 'flex' : 'none' }}` (JSDOM 호환 — Tailwind `hidden` 미사용)
- **노드 ID 표시** (`parameter-node-id`): 선택된 nodeId 표시
- **파라미터 목록**: `data[nodeId]` 객체 `Object.entries` → 키-값 쌍 렌더링
- **파라미터 값 렌더링**: 문자열·숫자 → `String(v)`, 객체 → `JSON.stringify(v)`, null/undefined → `"—"`
- **빈 상태**: nodeId가 null이거나 data가 null이거나 매칭 nodeId 키가 없으면 "No parameters available" 표시
- **닫기 버튼** (`parameter-close-btn`): `onClose` 콜백 호출

### MetricsChart 기능 목록

- **테이블 컬럼**: Item ID, Category, Status, Accuracy, FP Rate, FN Rate
- **상태 표시**: `passed=true` → CheckCircle + "Pass" (#4ade80), `passed=false` → XCircle + "Fail" (#f87171)
- **Accuracy 표시**: `(accuracy * 100).toFixed(1)%` 형식
- **FP Rate 바** (`fp-bar-{item_id}`): CSS `width: ${fp_rate * 100}%`, 배경색 #f87171
- **FN Rate 바** (`fn-bar-{item_id}`): CSS `width: ${fn_rate * 100}%`, 배경색 #facc15
- **퍼센트 텍스트**: 바 옆에 `(rate * 100).toFixed(1)%` 텍스트 표시
- **요약 행** (`metrics-summary-row`): `passedCount pass / failedCount fail` + `passed/total` 비율
- **빈 배열**: 크래시 없이 0 pass / 0 fail 표시

### LightingSuggestion 기능 목록

- **카드 리스트** (`lighting-card-{index}`): `string[]` 배열 각 항목을 개별 카드로 렌더링
- **Open Light Test** (`open-light-test-btn`): `window.alert('Navigate to Light Test')` 플레이스홀더
- **빈 배열**: 크래시 없이 카드 미표시
- **Lightbulb 아이콘**: 헤더 + 버튼에 lucide-react `Lightbulb` 사용

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `ResultPanel.test.tsx` | 18 | ✅ PASS |
| `BlueprintViewer.test.tsx` | 17 | ✅ PASS |
| `ParameterSheet.test.tsx` | 12 | ✅ PASS |
| `MetricsChart.test.tsx` | 14 | ✅ PASS |
| `LightingSuggestion.test.tsx` | 9 | ✅ PASS |
| 기존 전체 (Step 40까지) | 306 | ✅ PASS (회귀 없음) |

### Jest 결과

```
Test Suites: 18 passed, 18 total
Tests:       376 passed, 376 total (신규 70 + 기존 306)
Time:        ~4.6s
```

### TypeScript 검사 결과

```
npx tsc --noEmit → 오류 없음 (출력 없음)
```

### 주요 구현 노트

- **SVG 렌더링 방식**: `dangerouslySetInnerHTML`로 SVG 문자열을 직접 DOM에 삽입. React JSX SVG 파싱 대신 원본 SVG를 그대로 렌더링하여 백엔드 생성 SVG의 모든 속성·스타일 보존
- **줌/팬 구현**: `useRef`로 드래그 상태 관리 (렌더링 트리거 없이), `useState`로 scale·translateX·translateY만 상태 관리. `transform: translate() scale()` CSS 적용
- **노드 클릭 감지**: `e.target.closest('[data-node-id]')` DOM 탐색으로 SVG 내부 어떤 깊이의 요소를 클릭해도 `data-node-id` 속성이 있는 부모까지 탐색하여 감지
- **ParameterSheet 가시성**: JSDOM 호환을 위해 Tailwind `hidden` 대신 `style={{ display: isOpen ? 'flex' : 'none' }}` 사용
- **FP/FN 바 시각화**: 외부 차트 라이브러리 없이 CSS `width` 퍼센트 + 배경색으로 구현. FP=#f87171 (error), FN=#facc15 (warning)
- **Export SVG**: `Blob([svgContent], {type: 'image/svg+xml'})` → `URL.createObjectURL` → 임시 `<a>` 태그 클릭 → `URL.revokeObjectURL` 패턴
- **JSDOM URL mock**: `export-svg-btn` 테스트에서 `global.URL.createObjectURL` / `revokeObjectURL`을 `Object.defineProperty`로 모킹 (`jest.fn()` 직접 할당 시 `readonly` 오류 회피)
- **PlaceholderPanel 제거**: Result가 마지막 플레이스홀더였으므로 `PlaceholderPanel` 함수 완전 삭제 → TypeScript unused-variable 오류 해결

### 이슈 및 특이사항

1. **ParameterSheet 데이터 구조 불일치**: 현재 `Record<string, unknown>` (객체 key 기반 lookup `data[nodeId]`) 방식으로 구현. 실제 백엔드 Orchestrator는 `parameter_sheets: [{node_id, node_name, parameters}]` 배열을 반환하므로, 실제 데이터 연동 시 배열 → 객체 변환 로직 추가 또는 컴포넌트 인터페이스 수정 필요

2. **LightingSuggestion 단순화**: 현재 `string[]`로 구현 (types.ts 실제 타입 반영). 실제 백엔드 LightingAdvisor는 `{category, suggestion, reason, priority}` 객체 배열을 반환. priority별 색상 코딩 (high=#f87171, medium=#facc15, low=#4ade80) 실제 연동 시 추가 필요

3. **fit-btn placeholder**: 현재 `resetView`와 동일 동작 (scale=1, translate=0). 추후 컨테이너 크기 기반 auto-fit scale 계산 구현 필요

4. **MetricsChart name 필드 미포함**: `ItemResult` 인터페이스에 `name` 필드가 없어 `item_id`만 테이블에 표시. 백엔드 `item_results`에는 `name` 포함 (예: "구멍 후보 검출"). 추후 name 컬럼 추가 가능

5. **Decision fallback**: `DECISION_LABELS` 매핑에 없는 `decision` 값이 오면 `decision-card`가 렌더링되지 않음 (크래시 없음, silent ignore). 필요 시 "Unknown decision" fallback 카드 추가 가능

---

## Step 38 완료 내역

### 생성/수정된 파일

| 파일 경로 | 역할 | 상태 |
|-----------|------|------|
| `frontend/src/hooks/useROIDrawing.ts` | Canvas 마우스 드로잉 로직 훅 | 신규 |
| `frontend/src/components/ROICanvas.tsx` | ROI 드로잉 컴포넌트 | 신규 |
| `frontend/src/__tests__/useROIDrawing.test.ts` | 훅 단위 테스트 | 신규 |
| `frontend/src/__tests__/ROICanvas.test.tsx` | 컴포넌트 통합 테스트 | 신규 |
| `frontend/src/components/Layout.tsx` | ROI 플레이스홀더 → ROICanvas 교체 | 수정 |
| `PROGRESS.md` | 진행 기록 업데이트 | 수정 |

### ROICanvas 컴포넌트 기능 목록

- **이미지 표시**: Redux `images.analysis[0]` (첫 번째 analysis 이미지)를 HTML5 Canvas에 렌더링
- **이미지 URL**: `http://localhost:8000/api/images/{id}/file` 패턴 사용
- **Aspect ratio 보존**: `Math.min(canvasW/imgW, canvasH/imgH)` 스케일로 letterbox/pillarbox 처리
- **ROI 드로잉**: 마우스 드래그(mousedown → mousemove → mouseup)로 직사각형 ROI 그리기
- **ROI 오버레이**: 이미지 위에 반투명 다크 오버레이 + ROI 영역 원본 밝기 복원 + 흰색 점선 테두리 + 코너 핸들
- **좌표 수동 편집**: x1/y1/x2/y2 number input으로 직접 조정 (드로잉 중 disabled)
- **저장**: Save ROI 버튼 → `api.setRoi(roi)` POST + Redux `setRoi` dispatch
- **삭제**: Delete 버튼 → `api.clearRoi()` DELETE + Redux `clearRoi` dispatch + localRoi 초기화
- **Redux 초기화**: 마운트 시 `store.roi`(저장된 ROI)를 localRoi로 로드
- **빈 상태**: analysis 이미지 없을 때 "Upload images first" 안내 UI (`roi-empty-state`)
- **로딩 상태**: 이미지 로딩 중 스피너 (`roi-loading`)
- **에러 상태**: 이미지 로드 실패 시 에러 메시지 (`roi-error`)

### useROIDrawing 훅 인터페이스

**export:**
```typescript
export interface DrawContext {
  canvasWidth: number;
  canvasHeight: number;
  imageWidth: number;
  imageHeight: number;
}

export interface UseROIDrawingReturn {
  isDrawing: boolean;
  roi: ROICoordinates | null;  // { x1, y1, x2, y2 } — 항상 x1<x2, y1<y2
  startDraw: (x: number, y: number, ctx: DrawContext) => void;
  updateDraw: (x: number, y: number, ctx: DrawContext) => void;
  endDraw: (x: number, y: number, ctx: DrawContext) => void;
  clearROI: () => void;
}
```

**매개변수:** x, y는 캔버스 display 좌표 (mouse event에서 얻은 canvas-relative 픽셀값)

**반환값:**
- `isDrawing`: mousedown 이후 mouseup 이전 드로잉 진행 중 여부
- `roi`: 현재 ROI (이미지 원본 좌표계, integer, 항상 정규화됨)
- `startDraw`: mousedown 시 호출 — isDrawing=true, roi 초기화
- `updateDraw`: mousemove 시 호출 — roi 실시간 업데이트 (startRef가 없으면 no-op)
- `endDraw`: mouseup 시 호출 — isDrawing=false, 최종 roi 확정
- `clearROI`: ROI 삭제 — roi=null, isDrawing=false

### 캔버스 좌표 변환 로직

```
scale = Math.min(canvasWidth / imageWidth, canvasHeight / imageHeight)
displayW = imageWidth * scale
displayH = imageHeight * scale
offsetX = (canvasWidth - displayW) / 2    ← pillarboxing
offsetY = (canvasHeight - displayH) / 2   ← letterboxing

imageX = Math.round(clamp(0, imageWidth,  (canvasX - offsetX) / scale))
imageY = Math.round(clamp(0, imageHeight, (canvasY - offsetY) / scale))
```

- 스케일: `Math.min()` 으로 캔버스에 완전히 맞는 최대 스케일 선택
- 오프셋: 이미지를 캔버스 중앙에 배치 (letterbox/pillarbox)
- 클램핑: 이미지 영역 밖의 마우스 좌표는 경계값으로 자동 클램프
- 정수화: `Math.round()` 로 픽셀 단위 정수 보장
- 정규화: `Math.min(start, end)` / `Math.max(start, end)` 로 x1<x2, y1<y2 보장

**역변환 (canvas draw 시):**
```
canvasX = imageX * scale + offsetX
canvasY = imageY * scale + offsetY
```

### ROI 오버레이 렌더링 전략

```
1. ctx.clearRect(0, 0, W, H)
2. ctx.drawImage(img, offsetX, offsetY, displayW, displayH)   ← 이미지 전체
3. ctx.fillStyle = 'rgba(0,0,0,0.45)'
   ctx.fillRect(offsetX, offsetY, displayW, displayH)          ← 다크 오버레이
4. ctx.drawImage(img, roi.x1,roi.y1,roiW,roiH, rx,ry,rw,rh)  ← ROI 영역 복원
5. ctx.strokeRect(rx, ry, rw, rh)                              ← 흰 점선 테두리
6. 4개 코너에 6×6px 흰색 사각형 핸들
```

### displayRoi 전략 (canvas 드로잉 vs 입력 편집)

- **드로잉 중** (`isDrawing=true`): 캔버스는 훅의 `drawnRoi` 사용 (실시간 피드백)
- **드로잉 완료** (`isDrawing=false`): 캔버스는 `localRoi` 사용 (수동 편집 반영)
- **isDrawing 전환 시**: `useEffect([isDrawing, drawnRoi])` 로 `drawnRoi → localRoi` 동기화
- **수동 편집**: `localRoi` 직접 업데이트 → 즉시 캔버스 리드로

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `useROIDrawing.test.ts` | 30 | PASS |
| `ROICanvas.test.tsx` | 24 | PASS |
| `Layout.test.tsx` | 12 | PASS (회귀 없음) |
| `InputPanel.test.tsx` | 32 | PASS (회귀 없음) |
| `App.test.tsx` | 4 | PASS (회귀 없음) |
| `store.test.ts` | 11 | PASS (회귀 없음) |
| `slices.test.ts` | 60 | PASS (회귀 없음) |
| `api.test.ts` | 30 | PASS (회귀 없음) |
| `design-tokens.test.ts` | 11 | PASS (회귀 없음) |
| **합계** | **214** | **전체 PASS** |

### useROIDrawing 테스트 분류 (30개)

| 카테고리 | 테스트 수 |
|---------|---------|
| 초기 상태 (isDrawing=false, roi=null, 함수 노출) | 3 |
| startDraw (isDrawing=true, roi 초기화) | 2 |
| updateDraw (roi 업데이트, no-op 검증) | 3 |
| endDraw (isDrawing=false, roi 확정, no-op 검증) | 3 |
| clearROI (roi=null, isDrawing=false) | 2 |
| 좌표 변환 (스케일, Math.round, 1:1) | 3 |
| pillarboxing 오프셋 검증 | 1 |
| letterboxing 오프셋 검증 | 1 |
| 경계 클램핑 (음수, 초과, pillarbox 좌우) | 4 |
| ROI 정규화 (우→좌, 하→상) | 2 |
| 좌표 정수화 검증 | 1 |
| 합계 | 25 → 실제 30 |

### ROICanvas 테스트 분류 (24개)

| 카테고리 | 테스트 수 |
|---------|---------|
| 빈 상태 (이미지 없음, 텍스트, canvas 미노출) | 4 |
| 로딩 상태 (스피너 노출, canvas 미노출) | 2 |
| 로드 완료 (canvas, 버튼, getContext 호출) | 6 |
| 에러 상태 (에러 노출, 메시지, canvas 미노출) | 3 |
| ROI 좌표 패널 (x1/y1/x2/y2 입력값) | 5 |
| Save 버튼 (api.setRoi 호출, redux 반영) | 2 |
| Delete 버튼 (api.clearRoi 호출, redux 초기화, 패널 숨김) | 3 |
| 수동 입력 (x1, y2 변경) | 2 |
| 이미지 URL (id 포함, 백엔드 주소) | 2 |
| 레이아웃 통합 (roi-panel testid) | 1 |

### Jest 결과

```
Test Suites: 9 passed, 9 total
Tests:       214 passed, 214 total
Snapshots:   0 total
Time:        2.66 s
```

### TypeScript 체크 결과

```
npx tsc --noEmit → 오류 0개
```

### 이슈 및 해결사항

1. **`import React`의 TS6133 오류**: ROICanvas.test.tsx에서 `import React from 'react'` 를 추가했으나 React 18 + `jsx: react-jsx` 환경에서 미사용으로 TS 오류. import 제거로 해결.

2. **JSDOM Canvas 제약**: `HTMLCanvasElement.prototype.getContext`가 JSDOM에서 null 반환. `jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(mockCtx)` 패턴으로 해결.

3. **JSDOM Image 로딩 불가**: `new Image()` 의 `onload`/`onerror`가 JSDOM에서 자동 발화되지 않음. 컨트롤 가능한 `MockImage` 클래스를 구현하여 `currentMockImage.onload?.()` 로 수동 발화. `ControllableMockImage` 패턴으로 loading/loaded/error 상태를 독립적으로 테스트.

4. **displayRoi 전략 설계**: 드로잉 중 실시간 피드백과 수동 편집의 공존 문제. `isDrawing ? drawnRoi : localRoi` 조건부 선택 + `useEffect([isDrawing, drawnRoi])` 동기화로 해결. 드로잉 완료 시 localRoi 자동 업데이트.

5. **canvas.width/height 기본값**: JSDOM에서 `container.clientWidth/Height = 0` 이므로 resize 효과가 없음. 캔버스에 `width={800} height={500}` HTML 속성을 기본값으로 설정하여 JSDOM 테스트에서도 유효한 치수 보장.

6. **startRef vs useState**: `startPoint`를 useState 대신 useRef로 관리 — 렌더링 트리거 없이 mousedown 시작 좌표 유지, updateDraw/endDraw의 클로저 스테일 문제 방지.

### 주의사항

- ROICanvas는 `http://localhost:8000/api/images/{id}/file` URL을 사용. 백엔드가 이 경로로 이미지를 서빙해야 함.
- `canvas.getContext('2d')` 가 null을 반환하면 드로잉 전체가 no-op (로딩 완료 후 에러 미표시).
- 드로잉 중 수동 입력 필드는 `disabled` 처리되어 좌표 충돌 방지.
- Layout test에서 ROI 패널 클릭 시 ROICanvas 렌더링: 이미지가 없는 빈 store 상태이므로 empty state만 표시, canvas 초기화 없음 → 회귀 없음.
- InputPanel의 기존 `act()` 경고는 이번 Step과 무관하며 이전부터 존재.

---

## Step 37 완료 내역

### 생성된 파일

| 파일 경로 | 역할 |
|-----------|------|
| `frontend/src/components/Layout.tsx` | 사이드바 + 메인 워크스페이스 레이아웃 |
| `frontend/src/components/panels/InputPanel.tsx` | 이미지 업로드/관리 패널 |
| `frontend/src/__tests__/Layout.test.tsx` | Layout 컴포넌트 테스트 (12개) |
| `frontend/src/__tests__/InputPanel.test.tsx` | InputPanel 컴포넌트 테스트 (32개) |
| `frontend/src/App.tsx` | Layout + Provider 통합으로 교체 |
| `frontend/src/__tests__/App.test.tsx` | App 테스트를 새 Layout 구조에 맞게 업데이트 |

### Layout 구조 설명

- **사이드바**: 기본 너비 `280px` (`w-[280px]`), 축소 시 `56px` (`w-14`)
- **Collapse 동작**: `sidebar-toggle` 버튼 클릭 → `collapsed` 상태 토글. 축소 시 레이블에 `style={{ display: 'none' }}` 적용 (JSDOM `toBeVisible()` 호환)
- **Active 인디케이터**: 활성 패널 좌측에 흰색 2px 세로 바 (`bg-accent-action`)
- **기본 활성 패널**: `input` (InputPanel 렌더)
- **Nav 항목**: Input, ROI, Engine, Directive, Config, Execution, Result (lucide-react 아이콘)
- **메인 워크스페이스**: `flex-1 overflow-hidden`, 활성 패널에 따라 동적 렌더링

### InputPanel 기능 목록

- **드래그 & 드롭**: `dragenter` / `dragleave` / `dragover` / `drop` 이벤트 처리, `data-dragging` 속성으로 시각 피드백
- **파일 브라우저**: 숨겨진 `<input type="file">` + `ref` 클릭 트리거, `accept="image/png,image/jpeg,image/bmp,image/tiff"` + `multiple`
- **파일명 유효성 검사** (클라이언트 즉시 피드백):
  - 정규식: `/^(ok|ng)_[1-9]\d*\.(png|jpg|jpeg|bmp|tiff)$/i`
  - 유효: `OK_1.png`, `NG_3.jpg`, `ok_2.PNG`, `ng_1.bmp`, `OK_10.jpeg`
  - 무효: `test.png`, `OK.png`, `NG_0.png` (index ≥ 1 필수), `OK_abc.png`
  - 오류 시 `validation-error` testid로 메시지 표시
- **썸네일 그리드**: 2열 그리드, 각 썸네일에 레이블(OK/NG) + 파일명 + 삭제 버튼
- **이미지 수 요약**: `OK: N / NG: N` 카운터 (`count-summary` testid)
- **Clear All 버튼**: 이미지가 있을 때만 표시 (`clear-all-btn` testid)
- **빈 상태**: 이미지 없을 때 `empty-state` testid 안내 UI
- **로딩 상태**: 업로드 중 `upload-loading` testid 스피너
- **오류 상태**: 업로드/삭제 실패 시 `upload-error` testid 메시지

### 사용된 컴포넌트/훅/아이콘

**훅:** `useAppDispatch`, `useAppSelector`, `useState`, `useEffect`, `useRef`, `useCallback`, `useMemo`

**Redux 액션:** `addImage`, `removeImage`, `clearImages`, `setAnalysisImages` (imagesSlice)

**API 함수:** `uploadImage`, `getImages`, `deleteImage`, `clearAllImages`

**lucide-react 아이콘:**
- Layout: `Image`, `Crop`, `Cpu`, `FileText`, `Settings`, `Play`, `BarChart2`, `ChevronLeft`, `ChevronRight`
- InputPanel: `Upload`, `X`, `Trash2`, `Image`, `AlertCircle`, `Loader2`, `FolderOpen`

**선택자 최적화:** `useAppSelector(s => s.images.analysis)` + `useAppSelector(s => s.images.test)` + `useMemo` 결합 — 매 렌더마다 새 배열 생성 방지

### 테스트 커버리지

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `Layout.test.tsx` | 12 | PASS |
| `InputPanel.test.tsx` | 32 | PASS |
| `App.test.tsx` | 4 | PASS (업데이트) |
| `store.test.ts` | 11 | PASS |
| `slices.test.ts` | 60 | PASS |
| `api.test.ts` | 30 | PASS |
| `design-tokens.test.ts` | 11 | PASS |
| **합계** | **160** | **전체 PASS** |

### jest 결과

```
Test Suites: 7 passed, 7 total
Tests:       160 passed, 160 total
Snapshots:   0 total
Time:        2.123 s
```

### TypeScript 체크 결과

```
npx tsc --noEmit → 오류 0개
```

### 이슈 및 해결사항

1. **useAppSelector 배열 참조 문제**: `s => [...s.images.analysis, ...s.images.test]`는 매 렌더마다 새 배열을 생성하여 react-redux의 "selector returned different result" 경고 발생. 두 개의 개별 selector + `useMemo`로 결합하여 해결.

2. **JSDOM CSS 클래스 미적용**: `opacity-0 w-0` TailwindCSS 클래스는 JSDOM에서 처리되지 않아 `toBeVisible()` 테스트 실패. `style={{ display: 'none' }}`으로 변경하여 JSDOM이 인식하는 visibility 제어 방식으로 전환.

3. **App.test.tsx 회귀**: App이 Layout으로 교체되면서 기존 "Vision Intelligence Agent" 텍스트 테스트 실패. App 테스트를 새 구조(sidebar, main-workspace, VIA2 브랜드)에 맞게 업데이트.

4. **미사용 `formatBytes` 함수**: InputPanel에서 파일 크기 표시를 구현하지 않아 `TS6133` 오류 발생. 함수 제거로 해결.

### 주의사항

- `InputPanel`의 `useEffect`에서 `getImages()` 후 dispatch가 act() 래핑 없이 실행되어 테스트에서 `console.error` 경고 발생. 실제 기능에는 영향 없으며 테스트는 모두 통과함.
- 사이드바 ROI/Engine/Directive/Config/Execution/Result 패널은 플레이스홀더로 구현 (다음 Step에서 구현 예정).
- 썸네일의 이미지 미리보기는 현재 아이콘으로 표시됨 — 실제 `<img>` 미리보기는 백엔드 서버가 이미지를 서빙할 때 추가 가능.

---

## Step 36 완료 내역

### 생성된 파일

| 파일 경로 | 역할 |
|-----------|------|
| `frontend/src/services/types.ts` | 전체 TypeScript 인터페이스/타입 정의 |
| `frontend/src/services/api.ts` | axios 인스턴스 + 22개 API 함수 |
| `frontend/src/store/slices/projectSlice.ts` | project 슬라이스 |
| `frontend/src/store/slices/engineSlice.ts` | engine 슬라이스 |
| `frontend/src/store/slices/imagesSlice.ts` | images 슬라이스 |
| `frontend/src/store/slices/roiSlice.ts` | roi 슬라이스 |
| `frontend/src/store/slices/configSlice.ts` | config 슬라이스 |
| `frontend/src/store/slices/directivesSlice.ts` | directives 슬라이스 |
| `frontend/src/store/slices/executionSlice.ts` | execution 슬라이스 |
| `frontend/src/store/slices/resultSlice.ts` | result 슬라이스 |
| `frontend/src/store/slices/lightTestSlice.ts` | light_test 슬라이스 |
| `frontend/src/store/slices/logsSlice.ts` | logs 슬라이스 |
| `frontend/src/store/index.ts` | configureStore + RootState + AppDispatch + typed hooks |
| `frontend/src/__tests__/store.test.ts` | 스토어 구성 및 초기 상태 테스트 (11개) |
| `frontend/src/__tests__/slices.test.ts` | 슬라이스 리듀서/액션 테스트 (60개) |
| `frontend/src/__tests__/api.test.ts` | API 함수 존재 및 엔드포인트 호출 테스트 (30개) |

### 설치된 패키지

```
@reduxjs/toolkit  (최신)
react-redux       (최신)
axios             (최신)
```

### 슬라이스 이름 및 초기 상태

#### 1. `project` (projectSlice)
```typescript
{ name: '', created_at: '' }
```
액션: `setProject(ProjectState)`

#### 2. `engine` (engineSlice)
```typescript
{
  mode: 'local',
  local_ollama_url: 'http://127.0.0.1:11434',
  remote_url: null,
  remote_type: 'colab',
  remote_auth_token: null,
  model_name: 'qwen2.5-coder:7b',
}
```
액션: `setEngine(EngineSettings)`
> ⚠️ PLAN.md와 차이: 실제 백엔드 모델(EngineSettings)은 `local_url` 대신 `local_ollama_url`, 그리고 `remote_auth_token`, `model_name` 필드 추가.

#### 3. `images` (imagesSlice)
```typescript
{ analysis: ImageMetadata[], test: ImageMetadata[] }
```
액션: `addImage(ImageMetadata)`, `setAnalysisImages(ImageMetadata[])`, `setTestImages(ImageMetadata[])`, `removeImage(id: string)`, `clearImages()`
> ⚠️ PLAN.md와 차이: `ImageFile` 대신 실제 백엔드 `ImageMetadata` 사용. 필드: `id`, `original_filename`, `label`, `index`, `file_size`, `upload_timestamp`, `file_path`, `group`. (`filename`/`url`/`category` 없음)

#### 4. `roi` (roiSlice)
```typescript
null  // ROICoordinates | null
```
액션: `setRoi(ROICoordinates)`, `clearRoi()`

#### 5. `config` (configSlice)
```typescript
{
  mode: 'inspection',
  max_iteration: 3,
  success_criteria: { accuracy: null, fp_rate: null, fn_rate: null, coord_error: null },
}
```
액션: `setConfig(InspectionConfig)`

#### 6. `directives` (directivesSlice)
```typescript
{ orchestrator: '', spec: '', image_analysis: '', depth: '', material: '',
  pipeline_composer: '', vision_judge: '', inspection_plan: '', test: '' }
```
액션: `setDirectives(AgentDirectives)`, `updateDirective({ key, value })`

#### 7. `execution` (executionSlice)
```typescript
{ status: 'idle', execution_id: null, current_agent: null,
  current_iteration: 0, goal_validation: null, progress: 0 }
```
액션: `setExecutionStatus(status)`, `setExecutionId(id)`, `setCurrentAgent(agent)`, `setCurrentIteration(n)`, `setGoalValidation(gv)`, `setProgress(n)`, `setExecution(Partial<ExecutionState>)`, `resetExecution()`

#### 8. `result` (resultSlice)
```typescript
{ summary: null, pipeline: null, inspection_plan: null, blueprint_svg: null,
  parameter_sheet: null, metrics: null, item_results: null,
  lighting_suggestions: null, improvement_suggestions: null,
  decision: null, decision_reason: null }
```
액션: `setResult(ExecutionResult)`, `clearResult()`

#### 9. `light_test` (lightTestSlice)
```typescript
{ image: null, lights: [], camera_view: 'front', rendered_result: null }
```
액션: `setLightTestImage(ImageMetadata | null)`, `addLight(LightConfig)`, `removeLight(id)`, `updateLight({ id, changes })`, `setCameraView('front' | 'top')`, `setRenderedResult(string | null)`, `clearLightTest()`

#### 10. `logs` (logsSlice)
```typescript
[]  // LogEntry[]
```
액션: `addLog(LogEntry)`, `setLogs(LogEntry[])`, `clearLogs()`

### TypeScript 타입 이름 (frontend/src/services/types.ts)

| 타입명 | 설명 |
|--------|------|
| `EngineSettings` | 백엔드 EngineSettings 미러 |
| `ImageMetadata` | 백엔드 ImageMetadata 미러 |
| `ROICoordinates` | 백엔드 ROICoordinates 미러 |
| `SuccessCriteria` | 백엔드 SuccessCriteria 미러 |
| `InspectionConfig` | 백엔드 InspectionConfig 미러 |
| `ConfigSaveResponse` | InspectionConfig + warnings 확장 |
| `AgentDirectives` | 백엔드 AgentDirectives 미러 |
| `ExecuteRequest` | POST /api/execute 요청 바디 |
| `GoalValidation` | { valid: boolean, warnings: string[] } |
| `ExecutionResult` | 실행 결과 데이터 |
| `ExecutionStatus` | 실행 상태 + 선택적 result |
| `LogEntry` | { timestamp, agent, level, message } |
| `LogsResponse` | { logs: LogEntry[], total: number } |
| `LightPosition` | { x, y, z: number } |
| `LightColor` | { r, g, b: number } |
| `LightConfig` | 조명 설정 (frontend-only) |
| `ProjectState` | { name, created_at } (frontend-only) |

### API 함수 시그니처 (frontend/src/services/api.ts)

baseURL: `http://localhost:8000`

| 함수명 | HTTP | 경로 | 반환 타입 |
|--------|------|------|-----------|
| `getHealth()` | GET | `/health` | `{ status, version }` |
| `getEngine()` | GET | `/api/engine` | `EngineSettings` |
| `updateEngine(settings)` | POST | `/api/engine` | `EngineSettings` |
| `uploadImage(file)` | POST | `/api/images/upload` | `ImageMetadata` |
| `getImages(group?)` | GET | `/api/images` | `ImageMetadata[]` |
| `clearAllImages()` | DELETE | `/api/images` | `{ message }` |
| `getImageById(id)` | GET | `/api/images/{id}` | `ImageMetadata` |
| `deleteImage(id)` | DELETE | `/api/images/{id}` | `{ message }` |
| `getRoi()` | GET | `/api/roi` | `ROICoordinates \| null` |
| `setRoi(roi)` | POST | `/api/roi` | `ROICoordinates` |
| `clearRoi()` | DELETE | `/api/roi` | `{ message }` |
| `getConfig()` | GET | `/api/config` | `InspectionConfig` |
| `saveConfig(config)` | POST | `/api/config` | `ConfigSaveResponse` |
| `getDirectives()` | GET | `/api/directives` | `AgentDirectives` |
| `saveDirectives(directives)` | POST | `/api/directives` | `AgentDirectives` |
| `startExecution(req)` | POST | `/api/execute` | `{ execution_id, status }` |
| `listExecutions()` | GET | `/api/execute` | `ExecutionStatus[]` |
| `getExecution(id)` | GET | `/api/execute/{id}` | `ExecutionStatus` |
| `cancelExecution(id)` | DELETE | `/api/execute/{id}` | `{ message, execution_id }` |
| `getLogAgents()` | GET | `/api/logs/agents` | `{ agents: string[] }` |
| `getLogs(params?)` | GET | `/api/logs` | `LogsResponse` |
| `clearLogs()` | DELETE | `/api/logs` | `{ cleared: boolean }` |

> ⚠️ PLAN.md와 차이: 취소는 `POST /api/execute/{id}/cancel` 아닌 `DELETE /api/execute/{id}`, 상태 조회는 `/api/execute/{id}/status` 아닌 `/api/execute/{id}`. ROI에 DELETE 엔드포인트 추가. 로그 응답은 `{ logs, total }` 래핑 형식.

### 스토어 설정 (frontend/src/store/index.ts)

```typescript
export const store = configureStore({ reducer: { project, engine, images, roi, config, directives, execution, result, light_test, logs } })
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
export const useAppDispatch: () => AppDispatch
export const useAppSelector: TypedUseSelectorHook<RootState>
```

### 테스트 결과

| 테스트 파일 | 테스트 수 | 결과 |
|------------|----------|------|
| `store.test.ts` | 11 | PASS |
| `slices.test.ts` | 60 | PASS |
| `api.test.ts` | 30 | PASS |
| (기존 유지) design-tokens.test.ts | 12 | PASS |
| (기존 유지) App.test.tsx | 3 | PASS |
| **합계** | **116** | **전체 PASS** |

```
Test Suites: 5 passed, 5 total
Tests:       116 passed, 116 total
Time:        1.326s
```

TypeScript 오류: 0개 (`npx tsc --noEmit` 통과)

### 이슈 및 해결

1. **PLAN.md vs 실제 백엔드 불일치**: 백엔드 모델 파일(`backend/models/`)을 직접 읽어 실제 필드를 확인. `EngineSettings`의 `local_url` → `local_ollama_url`, `ImageMetadata`의 `filename`/`url`/`category` 없음(대신 `original_filename`/`file_path`/`group`/`label`/`index`/`file_size`/`upload_timestamp` 사용), 취소 엔드포인트가 `POST` 아닌 `DELETE`.

2. **axios 모킹 전략**: `jest.mock('axios', () => {...})` 팩토리 패턴을 사용하여 모듈 로드 시점에 axios.create가 mock 인스턴스를 반환하도록 설정. `mockAxiosCreate.mock.results[0]?.value ?? mockAxiosCreate()` 패턴으로 테스트 내에서 mock 인스턴스 참조.

3. **roiSlice 초기 상태**: `null as RoiState` 캐스팅으로 `ROICoordinates | null` 타입에서 `null` 초기값 TypeScript 오류 방지.

4. **logsSlice 초기 상태**: `[] as LogEntry[]` 캐스팅으로 배열 슬라이스 타입 추론 처리.

5. **light_test 슬라이스명**: Redux key를 `light_test`(언더스코어)로 설정 — PLAN.md 명세 준수.

---

## Step 35 완료 내역

### 생성된 파일

**프로젝트 설정**
- `frontend/package.json` (신규) — Electron 32 + Vite 5 + React 18 + TypeScript 5 + TailwindCSS 3
- `frontend/tsconfig.json` (신규) — ESNext target, bundler moduleResolution, strict 모드
- `frontend/tsconfig.node.json` (신규) — Vite 설정 파일용 TypeScript 설정
- `frontend/vite.config.ts` (신규) — @vitejs/plugin-react, base='./', port=5173
- `frontend/tailwind.config.js` (신규) — custom color 테마, darkMode='class'
- `frontend/postcss.config.js` (신규) — tailwindcss + autoprefixer
- `frontend/.eslintrc.cjs` (신규) — @typescript-eslint + react-hooks 플러그인
- `frontend/.prettierrc` (신규) — singleQuote, semi, tabWidth=2

**Electron 메인 프로세스**
- `frontend/main.js` (신규) — BrowserWindow 1280×800, dev/prod 분기 로드

**React 소스**
- `frontend/index.html` (신규) — Vite 진입점, `<div id="root">`
- `frontend/src/main.tsx` (신규) — ReactDOM.createRoot + StrictMode
- `frontend/src/App.tsx` (신규) — 다크 배경 앱 셸, VIA2 타이틀 표시
- `frontend/src/styles/design-tokens.ts` (신규) — 전체 디자인 토큰 export
- `frontend/src/styles/globals.css` (신규) — Tailwind 지시자 + glass morphism 유틸리티
- `frontend/src/jest.setup.ts` (신규) — @testing-library/jest-dom import
- `frontend/src/__mocks__/styleMock.js` (신규) — CSS import mock

**테스트 파일**
- `frontend/src/__tests__/design-tokens.test.ts` (신규)
- `frontend/src/__tests__/App.test.tsx` (신규)

### 디자인 토큰 색상값

| 그룹 | 키 | 값 |
|------|----|----|
| background | top | `#0a0a0a` |
| background | card | `#111111` |
| background | secondary | `#1a1a1a` |
| background | hover | `#222222` |
| border | default | `#2a2a2a` |
| border | accent | `#3a3a3a` |
| text | primary | `#f5f5f5` |
| text | secondary | `#a0a0a0` |
| text | disabled | `#555555` |
| accent | action | `#ffffff` |
| accent | success | `#4ade80` |
| accent | warning | `#facc15` |
| accent | error | `#f87171` |
| accent | info | `#60a5fa` |

### package.json 스크립트 및 주요 의존성

| 스크립트 | 명령 |
|---------|------|
| `dev` | `vite` |
| `build` | `tsc && vite build` |
| `electron` | `electron .` |
| `electron:dev` | `ELECTRON_DEV=true electron .` |
| `test` | `jest` |
| `lint` | `eslint src --ext .ts,.tsx` |

| 패키지 | 버전 | 용도 |
|--------|------|------|
| react | ^18.3.1 | UI 라이브러리 |
| react-dom | ^18.3.1 | DOM 렌더러 |
| lucide-react | ^0.446.0 | 아이콘 라이브러리 |
| electron | ^32.1.2 | 데스크톱 런타임 |
| vite | ^5.4.8 | 번들러 / 개발 서버 |
| tailwindcss | ^3.4.13 | CSS 유틸리티 (v3) |
| typescript | ^5.6.3 | 타입 시스템 |
| jest | ^29.7.0 | 테스트 러너 |
| ts-jest | ^29.2.5 | TypeScript Jest 변환기 |
| @testing-library/react | ^16.0.0 | React 테스트 유틸리티 |
| @testing-library/jest-dom | ^6.6.3 | jest DOM matcher 확장 |

### Jest 설정 상세

- preset: `ts-jest`
- testEnvironment: `jsdom`
- setupFilesAfterEnv: `src/jest.setup.ts` (@testing-library/jest-dom 로드)
- moduleNameMapper: CSS 파일 → `styleMock.js`
- ts-jest transform: `jsx: "react-jsx"` (tsconfig override)

### Electron main.js 설정

- 창 크기: 1280×800 (minWidth=960, minHeight=600)
- backgroundColor: `#0a0a0a`
- titleBarStyle: `hiddenInset` (macOS 네이티브 느낌)
- 개발 모드 감지: `ELECTRON_DEV=true` 환경변수 또는 `!app.isPackaged`
- 개발: `http://localhost:5173` 로드 + DevTools 자동 열기
- 프로덕션: `dist/index.html` 파일 로드

### TailwindCSS 커스텀 테마 확장

```js
colors: {
  'bg-top': '#0a0a0a', 'bg-card': '#111111',
  'bg-secondary': '#1a1a1a', 'bg-hover': '#222222',
  'border-default': '#2a2a2a', 'border-accent': '#3a3a3a',
  'text-primary': '#f5f5f5', 'text-secondary': '#a0a0a0', 'text-disabled': '#555555',
  'accent-action': '#ffffff', 'accent-success': '#4ade80',
  'accent-warning': '#facc15', 'accent-error': '#f87171', 'accent-info': '#60a5fa',
}
```

### 테스트 커버리지

| 테스트 파일 | 카테고리 | 테스트 수 |
|-----------|---------|---------|
| design-tokens.test.ts | background 키 존재 | 1 |
| design-tokens.test.ts | border 키 존재 | 1 |
| design-tokens.test.ts | text 키 존재 | 1 |
| design-tokens.test.ts | accent 키 존재 | 1 |
| design-tokens.test.ts | 유효한 hex 값 검증 | 1 |
| design-tokens.test.ts | 어두운 중성 배경 검증 | 1 |
| design-tokens.test.ts | typography.fontFamily body/code | 2 |
| design-tokens.test.ts | Inter 폰트 포함 | 1 |
| design-tokens.test.ts | JetBrains Mono 포함 | 1 |
| design-tokens.test.ts | spacing.base = 8 | 1 |
| design-tokens.test.ts | transitions.default 문자열 | 1 |
| App.test.tsx | 렌더 크래시 없음 | 1 |
| App.test.tsx | VIA2 타이틀 표시 | 1 |
| App.test.tsx | Vision Intelligence Agent 표시 | 1 |
| App.test.tsx | 다크 배경 클래스/스타일 | 1 |
| **합계** | | **15** |

### npm test 결과

```
Test Suites: 2 passed, 2 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        1.757 s
```

### npm run dev 결과

```
VITE v5.4.21  ready in 559 ms
➜  Local:   http://localhost:5173/
HTTP 200 확인
```

### npm run build 결과

```
vite v5.4.21 building for production...
✓ 33 modules transformed.
dist/index.html                   0.59 kB │ gzip:  0.38 kB
dist/assets/index-WW6IoAM_.css    6.18 kB │ gzip:  1.81 kB
dist/assets/index-C2LTl-lj.js   143.29 kB │ gzip: 46.09 kB
✓ built in 1.06s
```

### 이슈 및 해결

1. **`setupFilesAfterFramework` → `setupFilesAfterEnv`**: package.json jest 설정에서 Jest 설정 키명을 잘못 사용 (`setupFilesAfterFramework`). `node_modules/jest-config/build/Defaults.js` 확인으로 올바른 키 `setupFilesAfterEnv` 발견 후 수정.
2. **CSS import mock**: ts-jest 환경에서 CSS import가 실패하므로 `src/__mocks__/styleMock.js`와 `moduleNameMapper` 설정 추가.
3. **TailwindCSS v3**: v4가 아닌 v3.4.13 사용 — 안정성 우선, PostCSS 방식 유지.
4. **TS6133 `import React` 제거**: React 18 + `jsx: "react-jsx"` 설정에서는 JSX transform이 자동 처리되므로 `import React from 'react'`가 불필요. `tsconfig.json`의 `noUnusedLocals: true`가 빌드 오류를 유발. `src/App.tsx`와 `src/__tests__/App.test.tsx` 양쪽에서 해당 import 제거로 해결. `npm run build` 성공 확인.

### 주의사항

- `npm run electron` / `npm run electron:dev`는 반드시 `frontend/` 디렉토리 안에서 실행해야 함 (프로젝트 루트에서 실행 시 `main.js`를 찾지 못함).

---

## Step 34 완료 내역

### 생성된 파일
- `agents/lighting_advisor.py` (신규)
- `backend/services/execution_manager.py` (신규)
- `backend/routers/execute.py` (신규)
- `backend/main.py` (execute_router 등록)
- `tests/test_lighting_advisor.py` (신규)
- `tests/test_execution_manager.py` (신규)
- `tests/test_execute_api.py` (신규)

### LightingAdvisor 규칙 테이블

| 조건 | 카테고리 | 우선순위 |
|------|----------|----------|
| `surface_type == "metal"` | polarization | high |
| `reflection_level > 0.6` | light_shape | high |
| `lighting_uniformity < 0.5` | light_shape | high |
| `illumination_type == "spot"` | light_type | medium |
| `contrast < 0.3` | angle | medium |
| `has_shadow_region == True` | light_type | medium |
| `noise_level > 0.3` | intensity | low |

### ExecutionManager 인터페이스

**Constructor:** `ExecutionManager()` — asyncio.Lock 기반, 모듈 레벨 싱글턴 (`get_manager()`)

**States:** `"pending"` → `"running"` → `"completed"` / `"failed"` / `"cancelled"`

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `start_execution(user_text, images, ng_images, roi, text_query, success_criteria, directives, engine_settings)` | `str` (execution_id) | Orchestrator를 백그라운드 태스크로 실행 |
| `get_status(execution_id)` | `dict \| None` | execution_id, status, result, error, created_at, completed_at |
| `cancel_execution(execution_id)` | `"cancelled" \| "not_found" \| "already_completed"` | 태스크 취소 |
| `list_executions()` | `list[dict]` | 전체 실행 요약 목록 |

### Execute API 엔드포인트

| Method | Path | Status | 설명 |
|--------|------|--------|------|
| POST | `/api/execute` | 202 | 파이프라인 실행 시작 |
| GET | `/api/execute` | 200 | 전체 실행 목록 조회 |
| GET | `/api/execute/{id}` | 200 | 실행 상태 + 결과 조회 (완료 시 lighting_suggestions 포함) |
| DELETE | `/api/execute/{id}` | 200/404/409 | 실행 취소 |

### API Request/Response 예시

**POST /api/execute**
```json
// Request
{"user_text": "용접 비드 검사"}

// Response 202
{"execution_id": "550e8400-e29b-41d4-a716-446655440000", "status": "pending"}
```

**GET /api/execute/{id} (completed)**
```json
{
  "execution_id": "550e8400-...",
  "status": "completed",
  "created_at": "2026-05-24T10:00:00+00:00",
  "completed_at": "2026-05-24T10:02:30+00:00",
  "result": {
    "mode": "inspection",
    "scene_context": {"contrast": 0.4, "surface_type": "metal"},
    "lighting_suggestions": [
      {"category": "polarization", "suggestion": "...", "reason": "...", "priority": "high"}
    ]
  }
}
```

**DELETE /api/execute/{id}**
```json
// 200: {"message": "Execution cancelled", "execution_id": "..."}
// 404: {"detail": "Execution not found"}
// 409: {"detail": "Execution already completed or cancelled"}
```

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|----------|----------|
| LightingAdvisor 규칙 | 24 |
| ExecutionManager 라이프사이클 | 14 |
| Execute API 엔드포인트 | 14 |
| **합계** | **52** |

### pytest 결과

**Step 34 테스트 (52개):**
```
52 passed in 1.07s
```

**전체 테스트 스위트:**
```
1659 passed, 5 skipped in 8.21s
```

### 이슈 및 특이사항
- 백그라운드 태스크 패치 스코프: `asyncio.create_task()` 후 patch 블록을 벗어나면 mock이 해제되어 실제 Orchestrator가 실행됨. `await asyncio.sleep()`을 `with patch()` 블록 안으로 이동하여 해결.
- scene_context 필드: Orchestrator `_build_result()`는 contrast, surface_type, depth_complexity, optimal_color_space, roi만 포함한 요약 dict를 반환. LightingAdvisor는 `.get()` + 안전한 기본값으로 누락 필드를 처리.
- `cancel_execution()`: 세 가지 문자열 반환값(`"cancelled"`, `"not_found"`, `"already_completed"`)으로 라우터에서 HTTP 상태코드 분기.

---

## Step 33 완료 내역

### 생성된 파일
- `agents/orchestrator.py` (신규)
- `tests/test_orchestrator.py` (신규)
- `PROGRESS.md` (업데이트)

### Orchestrator 인터페이스

**Constructor:**
```python
Orchestrator(
    adapter: BaseAIAdapter,
    remote_url: str,
    model: str = "qwen2.5-coder:7b",
    max_iterations: int = 3,
    directives: AgentDirectives | None = None,
) -> None
```

**run() signature:**
```python
async def run(
    self,
    user_text: str,
    images: list[np.ndarray],               # OK images
    ng_images: list[np.ndarray] | None = None,  # NG images (inspection mode)
    roi: dict | None = None,                # {x1, y1, x2, y2}
    text_query: str | None = None,          # For ROI auto-detection
    success_criteria: dict | None = None,   # Override from SpecAgent
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `mode` | `str` | `"inspection"` \| `"align"` |
| `spec` | `dict` | SpecAgent 결과 전체 |
| `scene_context` | `dict` | 이미지 진단 요약 (contrast, surface_type, roi 등) |
| `pipeline` | `dict \| None` | 선택된 ProcessingPipeline (asdict) |
| `algorithm_category` | `str \| None` | AlgorithmCategory enum 값 |
| `inspection_plan` | `dict \| None` | InspectionPlan (asdict), inspection 모드만 |
| `blueprint` | `dict \| None` | Blueprint (asdict), inspection 모드만 |
| `parameter_sheets` | `list[dict] \| None` | NodeParameterSheet 목록, inspection 모드만 |
| `test_result` | `dict` | TestAgent 결과 데이터 |
| `evaluation` | `dict` | EvaluationAgent 결과 데이터 |
| `iterations_used` | `int` | 실제 사용된 반복 횟수 |
| `decision` | `dict` | DecisionAgent 결과 (max_iterations 초과 시만) |

### Pipeline Execution Order

| 단계 | 에이전트 | 비고 |
|------|---------|------|
| 1 | SpecAgent | mode, goal, success_criteria 파싱 |
| 2 | ImageAnalysisAgent | 이미지 진단 (OpenCV) |
| 3 | DepthAgent | 깊이 지도 (원격) |
| 4 | MaterialAgent | 재질 분류 (원격) |
| 5 | ROIAgent | ROI 처리 (원격 auto / 로컬 manual) |
| 6 | build_scene_context | 분석 결과 통합 |
| 7 | PipelineComposer | 3~5개 후보 파이프라인 생성 |
| 8 | PipelineSelector | 최적 파이프라인 선정 (ParameterSearcher + VisionJudge 내부) |
| 9 | AlgorithmSelector | 알고리즘 카테고리 결정 |
| 10 | InspectionPlanAgent | 검사 항목 설계 (inspection 모드만) |
| 11 | BlueprintAgent | SVG 블루프린트 생성 (inspection 모드만) |
| 12 | ParameterSheetGenerator | 파라미터 시트 생성 (inspection 모드만) |
| 13 | TestAgentInspection / TestAgentAlign | 실행 및 메트릭 측정 |
| 14 | EvaluationAgent | 결과 분석, 실패 원인 분류 |
| 15 | (통과) → 성공 반환 | |
| 16 | (실패) → FeedbackController | 재시도 전략 결정 |
| 17 | 재시도 루프 | max_iterations까지 반복 |
| 18 | (초과) → DecisionAgent | 최종 verdict 판정 |

### Retry Logic 매핑

| `failure_reason` | FeedbackController 전략 | Retry 시작 스테이지 | 재실행 에이전트 |
|-----------------|------------------------|-------------------|----------------|
| `pipeline_bad_fit` | `replace_pipeline` | `compose` | PipelineComposer 이후 전체 |
| `pipeline_bad_params` | `retry_params` | `select` | PipelineSelector 이후 |
| `algorithm_wrong_category` | `change_category` | `compose` | PipelineComposer 이후 전체 |
| `runtime_error` | `retry_pipeline` | `select` | PipelineSelector 이후 |
| `inspection_plan_issue` | `revise_plan` | `plan` | InspectionPlanAgent 이후 |
| `spec_issue` | `relax_spec` | `compose` | success_criteria 완화 후 전체 |

### Directive Routing 테이블

| `AgentDirectives` 필드 | 전달 대상 에이전트 |
|----------------------|----------------|
| `spec` | SpecAgent |
| `image_analysis` | ImageAnalysisAgent |
| `depth` | DepthAgent |
| `material` | MaterialAgent |
| `pipeline_composer` | PipelineComposer |
| `vision_judge` | VisionJudgeAgent, PipelineSelector |
| `inspection_plan` | InspectionPlanAgent |
| `test` | TestAgentInspection, TestAgentAlign |

### Error Handling 케이스

| 케이스 | 응답 |
|--------|------|
| `user_text` 빈 문자열 | `status="error"`, `"user_text is required"` |
| `images` 빈 리스트 | `status="error"`, `"images list is empty"` |
| `success_criteria` 값 > 1.0 또는 < 0.0 | `status="error"`, 필드명 포함 메시지 |
| inspection 모드에서 `ng_images=None` | `status="error"`, `"inspection mode requires ng_images"` |
| 각 에이전트 실패 | `status="error"`, 에이전트명 + 원본 에러 메시지 |
| max_iterations 초과 | `status="success"` + `data.decision` 포함 |

### 테스트 커버리지

| 테스트 클래스 | 테스트 수 | 내용 |
|------------|---------|------|
| TestOrchestratorInstantiation | 11 | 생성자, 기본값, 서브에이전트 생성, directive 라우팅 |
| TestOrchestratorInputValidation | 7 | 빈 입력, 잘못된 criteria, ng_images 누락 |
| TestOrchestratorHappyPathInspection | 14 | 전체 필드 검증, 에이전트 호출 횟수 |
| TestOrchestratorHappyPathAlign | 8 | align 모드 전용 동작 검증 |
| TestOrchestratorAgentErrors | 6 | 각 에이전트 실패 → 오류 전파 |
| TestOrchestratorRetryMechanics | 3 | 반복 횟수 증가, FeedbackController 호출 |
| TestOrchestratorRetryPaths | 6 | 6가지 failure_reason별 재시도 스테이지 검증 |
| TestOrchestratorMaxIterations | 5 | DecisionAgent 호출, decision 필드 포함 |
| TestOrchestratorDirectiveRouting | 8 | directive 필드별 에이전트 전달 확인 |
| TestOrchestratorSuccessCriteria | 2 | 사용자 override vs SpecAgent criteria |
| TestOrchestratorEdgeCases | 5 | 다중 이미지, roi/text_query 전달, 실행 시간 |
| **합계** | **75** | |

### pytest 결과
```
tests/test_orchestrator.py: 75 passed in 0.81s
전체: 1607 passed, 0 failed, 5 skipped in 6.10s
```

### 이슈 및 특이사항
- Orchestrator는 BaseAgent를 상속하지 않음 — 에이전트 코디네이터이므로 독립 클래스
- FeedbackController도 BaseAgent를 상속하지 않으므로 `directive` 필드를 통해 생성
- `PipelineSelector` 생성 시 `ParameterSearcher`와 `VisionJudgeAgent`를 내부에서 생성하여 주입
- align 모드에서는 InspectionPlanAgent, BlueprintAgent, ParameterSheetGenerator를 건너뜀
- test 실패(status="error") 시 합성 runtime_error 평가로 FeedbackController 실행 후 "select" 스테이지에서 재시도
- DecisionAgent 호출 시 align 모드에서 ng_images가 None이면 ok_images를 대신 전달 (DecisionAgent는 align 시 즉시 HARDWARE_IMPROVEMENT 반환)
- `spec_issue` 재시도 시 `min_accuracy`를 0.1 감소하여 완화 (최소 0.0)

---

## Step 32 완료 내역

### 생성된 파일
- `agents/decision_agent.py` (신규)
- `agents/prompts/decision_prompt.py` (신규)
- `tests/test_decision_agent.py` (신규)

### DecisionAgent 인터페이스

**Constructor:**
```python
DecisionAgent(remote_url: str, directive: str = "")
```

**run() signature:**
```python
async def run(
    self,
    mode: str,                              # "inspection" | "align"
    ng_images: list[np.ndarray],            # NG sample images
    evaluation_result: AgentResult | None = None,
    feedback_context: dict | None = None,   # FeedbackContext.to_dict() output
    vision_judge_scores: list[float] | None = None,
    success_criteria: dict | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `verdict` | `str` | DecisionVerdict enum 값 |
| `reasoning` | `str` | 한국어 판정 이유 |
| `dinov2_variability` | `float \| None` | DINOv2 특징 변동계수(CV) |
| `internvl_analysis` | `dict \| None` | InternVL 응답 또는 None |
| `vision_judge_avg_score` | `float \| None` | Vision Judge 점수 평균 |
| `recommendation` | `str` | 한국어 실행 권고문 |
| `confidence` | `float` | 판정 신뢰도 (0.0~1.0) |

### Decision logic priority

| 우선순위 | 조건 | Verdict |
|---------|------|---------|
| 1 | mode == "align" | `HARDWARE_IMPROVEMENT` |
| 2 | vision_judge_avg >= 0.7 AND tried_strategies < 4 | `RULE_BASED` |
| 3 | DINOv2 CV < 0.2 | `EDGE_LEARNING` |
| 4 | DINOv2 CV >= 0.2 | `DEEP_LEARNING` |
| 5 | DINOv2 실패, InternVL "consistent" | `EDGE_LEARNING` |
| 6 | DINOv2 실패, InternVL "diverse"/"mixed" | `DEEP_LEARNING` |
| 7 | 양쪽 모두 실패 | `DEEP_LEARNING` (confidence=0.3) |

### DINOv2 variability 임계값

| CV 범위 | 해석 | 권장 방향 |
|---------|------|----------|
| CV < 0.2 | 일관된 결함 패턴 | Edge Learning |
| CV >= 0.2 | 다양/불규칙한 결함 패턴 | Deep Learning |

**CV 계산 공식:**
```
feature_matrix = stack([f0, f1, ...])   # shape [N, D]
cv_per_dim = std(dim) / (|mean(dim)| + 1e-8)
overall_cv = mean(cv_per_dim)
```

### InternVL remote protocol

**Request:**
```
POST {remote_url}/internvl/analyze
Content-Type: application/json
{"images": ["<base64 JPEG>", ...], "prompt": "<analysis prompt>"}
```

**Response:**
```json
{"pattern_type": "consistent"|"diverse"|"mixed", "complexity_score": float, "reasoning": str}
```

### 에러 처리 케이스

| 케이스 | 응답 |
|--------|------|
| `ng_images` 빈 리스트 | `status="error"`, `error_message="No NG images provided for decision"` |
| mode == "align" | 즉시 `HARDWARE_IMPROVEMENT` 반환 (HTTP 호출 없음) |
| DINOv2 `ConnectError` | 경고 로그, `dinov2_variability=None`, InternVL로 진행 |
| InternVL `ConnectError` | 경고 로그, `internvl_analysis=None`, DINOv2로 진행 |
| 양쪽 모두 실패 | `DEEP_LEARNING`, `confidence=0.3` |

### Directive 처리

| 상황 | 사용되는 directive |
|------|------------------|
| `directive=None` | `self.directive` (생성자 값) |
| `directive=""` | 빈 문자열 (override) |
| `directive="x"` | `"x"` (override) |
| `self.directive` 변경 없음 | run() 호출이 self.directive를 변경하지 않음 |

### 테스트 커버리지

| 테스트 클래스 | 테스트 수 | 내용 |
|------------|---------|------|
| TestInstantiation | 5 | 상속, name, remote_url, directive |
| TestAlignMode | 6 | HARDWARE_IMPROVEMENT, HTTP 미호출, confidence=1.0 |
| TestAgentResultStructure | 12 | status, 7개 data 필드, 타입 검증 |
| TestComputeFeatureCv | 5 | 동일/단일/빈/다양/유사 feature CV |
| TestDinov2VariabilityVerdict | 4 | 낮은/높은 CV → verdict, 저장, 경계값 |
| TestInternVLIntegration | 4 | 저장, DINOv2만, InternVL만 (consistent/mixed) |
| TestVisionJudgeScoreInfluence | 6 | RULE_BASED 조건 (avg, tried_count) |
| TestDecisionLogicPriority | 3 | align > rule_based > EL/DL |
| TestErrorHandling | 6 | 빈 이미지, DINOv2 실패, InternVL 실패, 양쪽 실패 |
| TestDirectiveHandling | 4 | 생성자/override/None/빈 문자열 |
| TestReasoningOutput | 5 | 한국어 포함, RULE_BASED 점수 언급 |
| TestConfidenceScoring | 5 | 범위, align=1.0, rule_based, 실패=0.3, 합의 |
| TestBuildDecisionPrompt | 8 | tuple, 문자열, mode/CV/directive 포함 |
| **합계** | **73** | |

### pytest 결과
```
tests/test_decision_agent.py: 73 passed in 0.56s
전체: 1532 passed, 0 failed, 5 skipped in 7.20s
```

### 이슈 및 특이사항
- `DecisionVerdict.HARDWARE_IMPROVEMENT` (not HW_IMPROVEMENT) — 프롬프트의 약식 표기와 실제 enum 값 불일치, 소스 파일 확인 필수
- DINOv2는 NG 이미지당 1회 호출 (N images → N calls), InternVL은 모든 이미지를 한 번에 전송
- `_compute_feature_cv` 함수를 모듈 레벨에서 export하여 단위 테스트에서 직접 검증 가능
- 샘플 수 < 2일 때 CV = 0.0 반환 (단일 이미지 → Edge Learning으로 보수적 처리)
- InternVL "mixed" pattern_type → DEEP_LEARNING (inconsistent의 보수적 처리)
- 양쪽 서버 모두 실패 시 가장 강력한 방법(DL)을 안전 기본값으로 사용

---

## Step 28 완료 내역

### 생성된 파일
- `agents/blueprint_agent.py` (신규)
- `agents/prompts/blueprint_prompt.py` (신규)
- `tests/test_blueprint_agent.py` (신규)
- `PROGRESS.md` (업데이트)

### BlueprintAgent 인터페이스

**생성자**
```python
BlueprintAgent(adapter: BaseAIAdapter, model: str = "qwen2.5-coder:7b", directive: str = "") -> None
```

**run 시그니처**
```python
async def run(
    self,
    pipeline: ProcessingPipeline | None = None,
    inspection_plan: InspectionPlan | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `blueprint` | `dict` | Blueprint dataclass를 asdict() 변환 (nodes, edges, svg_content, algorithm_description, parameter_sheet) |
| `svg` | `str` | 완성된 SVG 다이어그램 문자열 |
| `description` | `str` | LLM 생성 한국어 알고리즘 설명 |
| `node_count` | `int` | 전체 노드 수 |
| `edge_count` | `int` | 전체 엣지 수 |

### 노드 타입 매핑

| block_type | node_type |
|-----------|-----------|
| color_space, denoise, gaussian_blur, bilateral_filter, normalize, resize, grayscale 등 | `preprocessing` |
| threshold, morphology, canny, edge, sobel, laplacian 등 나머지 블록 | `feature` |
| 각 InspectionItem (1개씩) | `inspection` |
| 최종 판정 (항상 1개) | `decision` |

### SVG 색상 체계

| node_type | fill 색상 |
|-----------|----------|
| preprocessing | `#4ade80` (green) |
| feature | `#60a5fa` (blue) |
| inspection | `#facc15` (yellow) |
| decision | `#f87171` (red) |
| 배경 | `#1a1a1a` |
| 텍스트 | `#f5f5f5` |

### Error handling

| 조건 | status | error_message |
|------|--------|---------------|
| pipeline is None | `"error"` | `"Pipeline is required"` |
| inspection_plan is None | `"error"` | `"InspectionPlan is required"` |
| pipeline.blocks 비어있음 | `"error"` | `"Pipeline has no blocks"` |
| inspection_plan.items 비어있음 | `"error"` | `"InspectionPlan has no items"` |
| LLM adapter 예외 | `"success"` (graceful degradation) | `None` (fallback: "파이프라인 기반 비전 검사 알고리즘") |

### Directive handling

- 생성자 `directive` → 기본값
- `run(directive=...)` → 생성자 directive 덮어씀
- `run(directive=None)` → 생성자 directive 사용

### 그래프 구조 (결정적 생성)

엣지 생성 규칙:
1. preprocessing 노드 간 순차 연결
2. feature 노드 간 순차 연결
3. preprocessing 마지막 → feature 첫 번째
4. inspection 루트 노드 (depends_on 없음) → feature 마지막 노드에서 연결
5. inspection depends_on 기반 노드 간 연결
6. terminal inspection 노드 (다른 항목의 depends_on에 없는 것) → decision

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|---------|---------|
| Constructor | 6 |
| Input validation | 10 |
| AgentResult structure | 9 |
| Blueprint nodes | 9 |
| Blueprint edges | 5 |
| SVG generation | 10 |
| Korean description (LLM) | 5 |
| LLM graceful degradation | 5 |
| Directive handling | 4 |
| Prompt builder | 7 |
| **합계** | **72** |

### pytest 결과

- 신규 테스트: 72 passed
- 전체 테스트: 1231 passed (기존 1159 + 신규 72)
- 실행 시간: 58.29s
- 경고: 기존과 동일 (PytestCollectionWarning)

### 특이사항
- BlueprintEdge 실제 필드명은 `source_id`/`target_id` (plan 명세의 `source`/`target`과 다름) — 실제 models.py 확인으로 수정
- Blueprint 모델에 `blueprint_id`, `title` 없음 — `svg_content`, `algorithm_description`, `parameter_sheet` 사용
- LLM 실패 시 Blueprint + SVG는 정상 생성, description만 한국어 fallback으로 대체 (status는 "success" 유지)

---

## Step 29 완료 내역

### 생성된 파일
- `agents/parameter_sheet.py` (신규)
- `tests/test_parameter_sheet.py` (신규)
- `PROGRESS.md` (업데이트)

### 데이터 모델

**ParameterEntry** (`agents/parameter_sheet.py`)
```python
@dataclass
class ParameterEntry:
    name: str
    value: Any
    mathematical_description: str
    unit: Optional[str] = None
```

**NodeParameterSheet** (`agents/parameter_sheet.py`)
```python
@dataclass
class NodeParameterSheet:
    node_id: str
    node_name: str
    node_type: str                 # preprocessing / feature / inspection / decision
    parameters: list[ParameterEntry]
    algorithm_summary: str         # 1줄 한국어 설명

    def to_dict(self) -> dict: ...  # JSON 직렬화 (tuple → list 자동 변환)
```

### ParameterSheetGenerator 인터페이스

```python
class ParameterSheetGenerator:
    def generate(
        self,
        blueprint: Blueprint,
        pipeline: ProcessingPipeline,
        inspection_plan: InspectionPlan,
    ) -> list[NodeParameterSheet]
```

### 노드 타입별 처리 전략

| node_type | 처리 방식 |
|-----------|----------|
| `preprocessing` | node.label(block_type) → `_PREPROCESSING_SUMMARIES` 조회 + `_make_preprocessing_entries()` |
| `feature` | node.label(block_type) → `_FEATURE_SUMMARIES` 조회 + `_make_feature_entries()` |
| `inspection` | node_id에서 item_id 추출 → `item_map[item_id]` 조회 → success_criteria → ParameterEntry |
| `decision` | inspection 노드 수 카운트 → "전체 N개 검사 항목 … 합격/불합격 판정" |

### 수학적 설명 매핑 (주요 예시)

| block_type / param | mathematical_description |
|--------------------|--------------------------|
| `grayscale` (summary) | "RGB→그레이스케일 단일 채널 변환" |
| `gaussian_fine` kernel_size=5 | "5×5 가우시안 커널" |
| `gaussian_fine` sigma=1.0 | "σ=1.0 가우시안 분포" |
| `bilateral` d=7 | "필터 직경 7px" |
| `median` kernel_size=5 | "5×5 중앙값 필터" |
| `clahe` clip_limit=2.0 | "CLAHE 대비 제한 계수 2.0" |
| `clahe` tile_grid_size=(8,8) | "타일 격자 8×8" |
| `otsu` (summary) | "오츠 알고리즘에 의한 자동 임계값 이진화" |
| `adaptive_mean` block_size=11 | "11×11 로컬 영역 적응형 임계값" |
| `adaptive_mean` c=5 | "임계값 보정 상수 5" |
| `erosion` kernel_size=3 | "3×3 침식 커널" |
| `erosion` iterations=2 | "2회 반복 형태학적 침식" |
| `canny` low_threshold=50 | "하한 임계값 50" |
| `canny` high_threshold=150 | "상한 임계값 150" |
| `sobel` ksize=3 | "3×3 소벨 미분 필터" |
| `laplacian` ksize=5 | "5×5 라플라시안 이차 미분 필터" |
| `scharr` (summary) | "샤르 고정밀 방향성 그래디언트 검출" |
| inspection (blob) | "{name} — 블랍 분석 기반 검사" |
| inspection (safety_role=True) | "… [안전 항목]" 접미 |
| decision | "전체 N개 검사 항목의 결과를 종합하여 합격/불합격 판정" |

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|---------|----------|
| ParameterEntry dataclass | 5 |
| NodeParameterSheet dataclass + to_dict() | 6 |
| Generator 기본 인터페이스 | 6 |
| Preprocessing — color space (grayscale, hsv_s/v, lab_l, ycrcb_cr) | 5 |
| Preprocessing — gaussian_fine/mid | 4 |
| Preprocessing — bilateral | 2 |
| Preprocessing — median | 1 |
| Preprocessing — clahe | 2 |
| Preprocessing — nlmeans | 1 |
| Feature — threshold (otsu, adaptive_mean/gauss, dynamic) | 7 |
| Feature — morphology (erosion, dilation, opening, closing, tophat, blackhat, morph_gradient) | 8 |
| Feature — edge detection (canny, sobel, laplacian, scharr) | 6 |
| Inspection nodes (type, name, summary, category, criteria, safety_role) | 7 |
| Decision node | 3 |
| Full pipeline integration | 3 |
| Edge cases (unknown block, empty params, missing plan item, empty nodes) | 8 |
| **합계** | **74** |

### pytest 결과

- 신규 테스트: 74 passed
- 전체 테스트: 1305 passed (기존 1231 + 신규 74)
- 실행 시간: 53.25s
- 경고: 기존과 동일 (PytestCollectionWarning)

### 특이사항
- `agents/models.py` 실제 확인: `InspectionItem`에는 `algorithm_category` 없고 `category` 필드만 존재 — 명세의 필드명과 달라 실제 코드로 검증 필수
- inspection node_id `"insp_{item_id}"` 패턴으로 item_id 역추출, 매칭 실패 시 graceful degradation ("비전 검사" fallback)
- `tile_grid_size`가 tuple인 경우 `to_dict()` 에서 list로 변환하여 JSON 직렬화 보장
- 순수 Python 표준 라이브러리만 사용, AI/LLM 어댑터 의존성 없음

---

## Step 27 완료 내역

### 생성된 파일
- `agents/test_agent_align.py` (신규)
- `tests/test_test_agent_align.py` (신규)
- `PROGRESS.md` (업데이트)

### TestAgentAlign 인터페이스

**생성자**
```python
TestAgentAlign(directive: str = "")
```

**run 시그니처**
```python
async def run(
    self,
    pipeline: ProcessingPipeline,
    ok_images: list[np.ndarray],
    roi: dict | None = None,        # {"x1": int, "y1": int, "x2": int, "y2": int}
    error_threshold: float = 5.0,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `per_image_results` | `list[dict]` | 이미지별 정렬 결과 |
| `overall_success_rate` | `float` | 성공 이미지 비율 |
| `overall_mean_error` | `float` | 평균 유클리드 오차 (px) |
| `overall_max_error` | `float` | 최대 오차 (px) |
| `overall_passed` | `bool` | success_rate ≥ 0.8 |
| `method_stats` | `dict` | 각 방법 사용 횟수 {"template": N, "edge": N, "caliper": N} |
| `error_threshold` | `float` | directive 보정 후 실제 임계값 |
| `total_images` | `int` | 처리한 이미지 수 |

### per_image_result 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `image_index` | `int` | 0-based 인덱스 |
| `detected_x` | `float` | 검출된 X 좌표 (전체 이미지 공간) |
| `detected_y` | `float` | 검출된 Y 좌표 (전체 이미지 공간) |
| `ground_truth_x` | `float` | ROI 중심 X ((x1+x2)/2) |
| `ground_truth_y` | `float` | ROI 중심 Y ((y1+y2)/2) |
| `error_px` | `float` | 유클리드 거리 오차 |
| `method_used` | `str` | "template" / "edge" / "caliper" |
| `match_score` | `float \| None` | 템플릿 매칭 점수 (비-template은 None) |
| `success` | `bool` | error_px < threshold |

### Fallback 체인 동작

1. **Template Matching**: `cv2.matchTemplate(TM_CCOEFF_NORMED)` — 첫 번째 OK 이미지 ROI 중심 50% 패치를 템플릿으로 사용. score ≥ 0.5이면 채택.
2. **Edge Detection**: Canny → HoughLinesP (라인 ≥ 2개 시 엔드포인트 COM, 미만 시 Canny 픽셀 COM). edge_pixel_count ≥ 2이면 채택.
3. **Caliper** (최종 fallback): 중간 행/열 프로파일에서 최대 기울기 2개 피크 위치의 중점을 검출 좌표로 사용.

### Error handling

| 조건 | status | error_message |
|------|--------|---------------|
| ok_images 비어있음 | `"error"` | `"No OK images provided"` |
| roi가 None | `"error"` | `"ROI is required for align mode"` |
| ROI 너무 작음 (w<3 or h<3) | `"error"` | `"ROI too small for alignment"` |

### Directive handling

| directive | 동작 |
|-----------|------|
| `"strict"` | error_threshold × 0.5 (더 엄격) |
| `"lenient"` | error_threshold × 2.0 (더 관대) |
| 기타 / 빈 문자열 | threshold 변경 없음 |

- `run(directive=...)` 호출 시 → run 인자 우선
- `run(directive=None)` → 생성자 directive 사용
- 좌표는 전체 이미지 공간 (ROI offset 가산 후 ROI 경계로 클리핑)

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|---------|---------|
| Instantiation | 5 |
| Error handling | 6 |
| Result structure | 11 |
| Per-image result fields | 3 |
| Ground truth | 2 |
| Coordinate space | 2 |
| Error calculation | 6 |
| Method stats | 2 |
| Template method | 3 |
| Directive handling | 6 |
| Pipeline preprocessing | 3 |
| Single image | 2 |
| Alignment accuracy | 2 |
| **합계** | **53** |

### pytest 결과

- 신규 테스트: 53 passed
- 전체 테스트: 1159 passed (기존 1106 + 신규 53)
- 실행 시간: 59.16s
- 경고: 기존과 동일 (PytestCollectionWarning — TestAgentInspection 클래스명 충돌)

### 특이사항
- `_build_template`은 ROI 크기에 따라 center-50% 패치 추출 실패 시 top-left 1/3 패치로 자동 fallback
- 좌표 공간 변환: ROI 내부 검출 좌표 + (x1, y1) → 전체 이미지 공간으로 변환 후 ROI 경계 클리핑
- `_detect_template` 재사용 불가 (template 크기는 proc_roi별 고정) → 첫 번째 이미지 기준 단일 template 사용

---

## Step 26 완료 내역

### 생성된 파일
- `agents/test_agent_inspection.py` (신규)
- `tests/test_test_agent_inspection.py` (신규)
- `PROGRESS.md` (업데이트)

### TestAgentInspection 인터페이스

**Constructor:**
```python
TestAgentInspection(directive: str = "")
```

**run signature:**
```python
async def run(
    self,
    inspection_plan: InspectionPlan,
    pipeline: ProcessingPipeline,
    ok_images: list[np.ndarray],
    ng_images: list[np.ndarray],
    roi: dict | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `item_results` | `list[dict]` | 항목별 결과 (execution_order 순) |
| `overall_accuracy` | `float` | 비스킵 항목들의 accuracy 평균 |
| `overall_passed` | `bool` | 모든 비스킵 항목이 통과했는지 여부 |
| `execution_order` | `list[int]` | 위상정렬된 item_id 순서 |
| `total_items` | `int` | 전체 항목 수 |
| `passed_items` | `int` | 통과한 항목 수 |
| `skipped_items` | `int` | 스킵된 항목 수 |
| `failed_items` | `int` | 실패한 항목 수 |

**item_result 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `item_id` | `int` | 항목 ID |
| `name` | `str` | 항목명 |
| `category` | `str` | 검사 카테고리 |
| `accuracy` | `float` | (TP+TN)/(n_ok+n_ng) |
| `fp_rate` | `float` | FP/n_ok — OK 이미지 오검출률 |
| `fn_rate` | `float` | FN/n_ng — NG 이미지 미검출률 |
| `passed` | `bool` | success_criteria 충족 여부 |
| `skipped` | `bool` | 의존 항목 실패로 스킵 여부 |
| `details` | `dict` | 카테고리별 세부 정보 |

### Topological Sort 동작 설명

Kahn's Algorithm 사용:
1. `depends_on`으로 인접 리스트 + 진입차수(in_degree) 구성
2. 진입차수 0인 노드부터 BFS 순서로 실행 순서 결정
3. **순환 의존성**: 정렬 후 항목 수가 맞지 않으면 `ValueError` → `AgentResult(status="error")`
4. **누락된 의존성**: `depends_on`에 존재하지 않는 item_id가 있으면 무시하고 계속 진행
5. **연쇄 스킵**: 스킵된 항목을 의존하는 항목도 연쇄적으로 스킵 (failed_ids + skipped_ids 모두 추적)

### Per-item Metric 계산 공식

```
accuracy  = (TP + TN) / (n_ok + n_ng)
fp_rate   = FP / n_ok         # OK 이미지 중 잘못 defect 판정된 비율
fn_rate   = FN / n_ng         # NG 이미지 중 잘못 OK 판정된 비율
```

- OK 이미지 + defect NOT detected = TN (True Negative)
- OK 이미지 + defect detected = FP (False Positive)
- NG 이미지 + defect detected = TP (True Positive)
- NG 이미지 + defect NOT detected = FN (False Negative)

### Error Handling

| 조건 | status | error_message |
|------|--------|---------------|
| `inspection_plan.items` 비어있음 | `"error"` | "Inspection plan has no items" |
| `ok_images` 비어있음 | `"error"` | "No OK images provided" |
| `ng_images` 비어있음 | `"error"` | "No NG images provided" |
| 순환 의존성 감지 | `"error"` | "Circular dependency detected in inspection plan" |

### Directive Handling

- 생성자 directive를 기본값으로 사용
- `run(directive="...")` 호출 시 해당 값으로 override
- `run(directive=None)` 호출 시 생성자 directive fallback
- `"strict"` 포함 시: `min_accuracy` 기준 +0.1 (더 엄격)
- `"lenient"` 포함 시: `min_accuracy` 기준 -0.1 (더 완화)

### 카테고리별 검사 로직

| 카테고리 | 검사 방식 | details 키 |
|----------|-----------|------------|
| BLOB / COUNT | OTSU threshold + findContours로 blob 수 계산, OK baseline과 비교 | `blob_counts`, `ok_blob_counts`, `ng_blob_counts`, `baseline`, `threshold` |
| COLOR_FILTER | R-B 채널 차이로 색상 분포 측정, OK baseline과 비교 | `channel_scores`, `ok_channel_scores`, `ng_channel_scores`, `baseline` |
| EDGE_DETECTION | Canny 엣지 밀도 계산, OK baseline과 비교 | `edge_scores`, `ok_edge_scores`, `ng_edge_scores`, `baseline` |
| TEMPLATE_MATCHING | 첫 OK 이미지 중심 패치를 template으로 matchTemplate, OK mean의 90% 미만이면 defect | `match_scores`, `ok_match_scores`, `ng_match_scores`, `threshold` |
| GEOMETRIC | 최대 contour의 원형도(circularity) 계산, OK baseline과 비교 | `geometric_scores`, `ok_geometric_scores`, `ng_geometric_scores`, `baseline` |

### Test Coverage

| 테스트 클래스 | 테스트 수 | 검증 항목 |
|---------------|-----------|-----------|
| TestInstantiation | 5 | 생성, 상속, name, directive |
| TestResultStructure | 11 | AgentResult 필드, 실행시간 |
| TestItemResultFields | 15 | item_result 각 필드 타입/값 |
| TestTopologicalSort | 6 | 순서, 독립 항목, 순환, 누락 의존성, fan-in |
| TestDependencySkip | 4 | 스킵 전파, 카운트, 비의존 항목, 스킵 accuracy=0 |
| TestMetricCalculation | 5 | 완벽 분류 accuracy/fp/fn, passed/failed |
| TestBlobCategory | 5 | details 키, ok<ng blob counts, COUNT 서브카테고리 |
| TestEdgeDetectionCategory | 4 | 실행, details, edge 밀도 방향성, accuracy |
| TestColorFilterCategory | 3 | 실행, details, blue vs red 구분 |
| TestTemplateMatchingCategory | 3 | 실행, details, ok>ng match score |
| TestGeometricCategory | 4 | 실행, details, 원형도 방향성, accuracy |
| TestROIHandling | 3 | ROI 적용, None ROI, 크롭 효과 |
| TestPipelineExecution | 3 | 빈 파이프라인, 다중 블록, BGR 입력 |
| TestDirectiveHandling | 4 | override, fallback, strict, lenient |
| TestErrorHandling | 7 | 빈 plan, 빈 ok/ng, 오류 메시지, 실행시간 |
| TestOverallMetrics | 11 | 카운트, 평균, 합계, 타입 검증 |

### pytest 결과

- **신규 테스트**: 93개 (tests/test_test_agent_inspection.py)
- **전체 테스트**: 1106개 통과 (기존 1008개 + 신규 98개 포함)
- **실행 시간**: 90.25s (1:30)
- **회귀 없음**: 기존 전체 테스트 통과 유지

### 특이사항

- `TestAgentInspection` 클래스명이 pytest 수집 대상으로 오인될 수 있어 `PytestCollectionWarning` 발생하나, `__init__` 생성자로 인해 수집 불가로 처리됨. 기능 및 테스트에 영향 없음.
- 연쇄 스킵(cascade skip): 실패한 항목뿐 아니라 스킵된 항목도 `skipped_ids`로 추적하여, 3단계 이상 의존 관계에서도 올바르게 연쇄 스킵 적용.
- BLOB에서 균일한(std < 1) 이미지는 blob 수 0으로 처리하여 OTSU가 불안정한 flat histogram에서 오동작하는 것을 방지.

---

## Step 25 완료 내역

### 생성된 파일
- `agents/pipeline_selection.py` (신규)
- `tests/test_pipeline_selection.py` (신규)
- `PROGRESS.md` (업데이트)

### PipelineSelector 인터페이스

```python
class PipelineSelector(BaseAgent):
    def __init__(
        self,
        parameter_searcher: ParameterSearcher,
        vision_judge: VisionJudgeAgent,
        directive: str = "",
    ) -> None

    async def run(
        self,
        pipelines: list[ProcessingPipeline],
        image: np.ndarray,
        purpose: str,
        roi: dict | None = None,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult

    def _execute_pipeline(
        self,
        pipeline: ProcessingPipeline,
        image: np.ndarray,
        roi: dict | None,
    ) -> np.ndarray
```

- name: `"pipeline_selection"`
- ParameterSearcher (파라미터 최적화) + VisionJudgeAgent (품질 평가)를 조합하여 최적 파이프라인 선정
- `_apply_block`을 `parameter_searcher.py`에서 import하여 블록 실행 로직 재사용

### AgentResult data 필드 (성공 시)
| 필드 | 타입 | 설명 |
|------|------|------|
| `selected_pipeline` | `ProcessingPipeline` | 파라미터 최적화된 최고 점수 파이프라인 |
| `selected_index` | `int` | 입력 목록 기준 0-based 인덱스 |
| `combined_score` | `float` | 최종 복합 점수 |
| `quality_score` | `dict` | ParameterSearcher의 QualityScore (asdict) |
| `judgement` | `dict` | VisionJudgeAgent의 JudgementResult (asdict) |
| `all_candidates` | `list[dict]` | 후보별 평가 요약 (pipeline_id, combined_score, quality_score, judgement_score, status) |

### 점수 계산 공식
```
judgement_overall = (visibility_score + separability_score + measurability_score) / 3
combined_score    = 0.4 × quality_overall + 0.6 × judgement_overall
```
- `judgement_overall`은 VisionJudgeAgent의 `overall_score`를 사용하지 않고, 세 점수의 산술 평균으로 직접 계산

### ROI 처리
- `_execute_pipeline`은 `{"x1": ..., "y1": ..., "x2": ..., "y2": ...}` 형식으로 크롭
- 동일 `roi` dict를 ParameterSearcher에도 전달

### 에러 처리
| 조건 | status | error_message |
|------|--------|---------------|
| `pipelines`가 빈 리스트 | `"error"` | `"No candidate pipelines provided"` |
| 이미지 크기 < 3×3 | `"error"` | `"Image too small for pipeline selection"` |
| `purpose`가 빈 문자열 | `"error"` | `"Purpose is required for pipeline selection"` |
| 단일 후보 실패 (searcher/judge 오류 또는 예외) | `"skipped"` (all_candidates 내) | — |
| 모든 후보 실패 | `"error"` | `"All candidate pipelines failed evaluation"` |

### Directive 처리
- 생성자 directive: 기본값
- `run(directive=...)`: 생성자 directive를 override
- `run(directive=None)`: 생성자 directive로 fallback
- 최종 directive를 ParameterSearcher와 VisionJudgeAgent 모두에 전달

### 테스트 커버리지
| 카테고리 | 테스트 수 |
|----------|----------|
| Instantiation | 6 |
| AgentResult structure | 14 |
| Score weighting | 4 |
| Pipeline selection logic | 10 |
| Candidate failure handling | 7 |
| Error handling | 7 |
| ROI handling | 4 |
| Pipeline execution | 4 |
| Directive handling | 5 |
| **합계** | **62** |

### pytest 결과
- 신규 테스트: 62개 (모두 통과)
- 전체 테스트: 1008개 (946 → 1008, regressions 없음, 5 skipped)
- 실행 시간: ~5초

### 특이사항
- `_apply_block`을 `parameter_searcher.py`에서 직접 import (`from agents.parameter_searcher import _apply_block`) — 블록 실행 로직 중복 없이 재사용
- ParameterSearcher와 VisionJudgeAgent 모두 mock 처리하여 외부 의존성 완전 격리
- 예외 발생 시 해당 후보를 `"skipped"`로 기록하고 계속 진행 (try/except로 방어)

---

## Step 24 완료 내역

### 생성된 파일
- `agents/inspection_plan_agent.py` (신규)
- `agents/prompts/inspection_plan_prompt.py` (신규)
- `tests/test_inspection_plan.py` (신규)
- `PROGRESS.md` (업데이트)

### InspectionPlanAgent 인터페이스

```python
class InspectionPlanAgent(BaseAgent):
    def __init__(
        self,
        adapter: BaseAIAdapter,
        model: str = "qwen2.5-coder:7b",
        directive: str = "",
    ) -> None
    async def run(
        self,
        purpose: str,
        scene_context: SceneContext | None,
        algorithm_category: AlgorithmCategory | None,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult
```

- name: `"inspection_plan"`
- Qwen2.5-Coder를 통해 LLM이 검사 항목을 자유롭게 설계 (고정 템플릿 없음)
- JSON 배열을 파싱하여 `InspectionItem` 리스트 → `InspectionPlan` 구성

### Prompt Builder (`build_inspection_plan_prompt`)

```python
def build_inspection_plan_prompt(
    purpose: str,
    scene_context: SceneContext,
    algorithm_category: AlgorithmCategory,
    directive: str | None,
) -> tuple[str, str]:
```

- system_prompt: JSON 배열 스키마 명세 (item_id, name, category, depends_on, safety_role, success_criteria)
- user_prompt: purpose + algorithm_category + scene 진단 지표 (surface_type, contrast, edge_density 등) + 선택적 directive
- directive가 없으면 prompt에 "None" 리터럴 미포함

### AgentResult data 필드 (성공 시)
| 필드 | 타입 | 설명 |
|------|------|------|
| `plan` | `dict` | `InspectionPlan.asdict()` — items 리스트 + inspection_purpose + total_items |
| `raw_response` | `str` | LLM 원문 출력 |

### InspectionItem 필드 매핑
| LLM JSON 필드 | InspectionItem 필드 | 타입 | 비고 |
|--------------|---------------------|------|------|
| `item_id` | `item_id` | `int` | 1부터 시작 |
| `name` | `name` | `str` | 검사 항목 이름 |
| `category` | `category` | `str` | AlgorithmCategory value 중 하나 |
| `depends_on` | `depends_on` | `list[int]` | 선행 item_id 목록 |
| `safety_role` | `safety_role` | `bool` | 비bool 값은 bool()로 강제 변환 |
| `success_criteria` | `success_criteria` | `dict` | 문자열이면 {"metric": str, "threshold": 0}으로 래핑 |

### 에러 처리
| 조건 | status | error_message |
|------|--------|---------------|
| `purpose`가 빈 문자열 | `"error"` | `"Inspection purpose is required"` |
| `scene_context is None` | `"error"` | `"SceneContext is required"` |
| `algorithm_category is None` | `"error"` | `"AlgorithmCategory is required"` |
| 어댑터 예외 | `"error"` | 어댑터 예외 메시지 |
| JSON 파싱 실패 | `"error"` | `"Failed to parse inspection plan from LLM response"` |
| LLM이 빈 배열 반환 | `"error"` | `"LLM returned empty inspection plan"` |

### depends_on 검증
- 참조된 item_id가 계획 내에 없으면 해당 항목만 제거, 경고 로그 기록 후 계속 진행
- 유효한 참조는 그대로 보존

### Directive 처리
- 생성자 directive: 기본값으로 사용
- `run(directive=...)`: 생성자 directive를 override
- `run(directive=None)`: 생성자 directive로 fallback
- directive가 있으면 user_prompt 끝에 `"Additional directive: {directive}"` 추가

### 테스트 커버리지
| 카테고리 | 테스트 수 |
|----------|----------|
| Instantiation | 6 |
| AgentResult structure | 6 |
| InspectionPlan/Item fields | 9 |
| depends_on validation | 4 |
| Different purposes | 3 |
| Error handling | 13 |
| Directive handling | 4 |
| AlgorithmCategory in prompt | 4 |
| JSON parsing robustness | 2 |
| Prompt builder | 9 |
| **합계** | **64** |

### pytest 결과
- 신규 테스트: 64개 (모두 통과)
- 전체 테스트: 946개 (887 → 946, regressions 없음, 5 skipped)
- 실행 시간: ~6초

### 특이사항
- `InspectionItem.safety_role`은 `bool` 타입 (기존 모델 기준); LLM에서 비bool 반환 시 `bool()` 강제 변환
- `InspectionItem.success_criteria`는 `dict` 타입; LLM에서 문자열 반환 시 자동 래핑
- `_strip_fences` 패턴을 SpecAgent와 동일하게 적용하여 markdown fence 처리
- 타공(hole/perforation) 결함 유형은 system_prompt에 misdetection-prevention 항목 자동 포함 지시 포함

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

---

## Step 31 완료 내역

### 생성된 파일
- `agents/feedback_controller.py` (신규)
- `tests/test_feedback_controller.py` (신규)
- `PROGRESS.md` (업데이트)

### FeedbackController 인터페이스

**생성자**
```python
FeedbackController(directive: str = "")
```

**run 시그니처**
```python
async def run(
    self,
    evaluation_result: AgentResult,
    pipeline: ProcessingPipeline | None = None,
    vision_judge_result: JudgementResult | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### FeedbackContext 데이터클래스 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `iteration` | `int` | 현재 재시도 횟수 (run() 호출마다 +1) |
| `history` | `list[dict]` | 과거 재시도 기록 (iteration, failure_reason, strategy, vision_judge_suggestion) |
| `tried_strategies` | `set[str]` | 이미 시도된 전략 이름 집합 |
| `failed_pipelines` | `list[str]` | 실패한 pipeline_id 목록 (중복 없음) |
| `constraints` | `list[str]` | 다음 시도를 위해 누적된 제약 조건 |

`to_dict()`: set을 list로 변환하여 JSON 직렬화 보장.

### RetryStrategy 매핑 테이블

| FailureReason | strategy | severity |
|---------------|----------|----------|
| `pipeline_bad_fit` | `replace_pipeline` | high |
| `algorithm_wrong_category` | `change_category` | high |
| `runtime_error` | `retry_pipeline` | medium |
| `inspection_plan_issue` | `revise_plan` | medium |
| `pipeline_bad_params` | `retry_params` | low |
| `spec_issue` | `relax_spec` | low |

### Severity 우선순위 (dominant strategy 선택)

우선순위 순서 (높은 것 → 낮은 것):
1. `PIPELINE_BAD_FIT` (high)
2. `ALGORITHM_WRONG_CATEGORY` (high)
3. `RUNTIME_ERROR` (medium)
4. `INSPECTION_PLAN_ISSUE` (medium)
5. `PIPELINE_BAD_PARAMS` (low)
6. `SPEC_ISSUE` (low)

같은 severity 내 tie-breaking: 위 목록의 앞 순서 우선 (PIPELINE_BAD_FIT > ALGORITHM_WRONG_CATEGORY 등).

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `strategy` | `str \| None` | 선택된 RetryStrategy 이름 |
| `severity` | `str \| None` | "high" / "medium" / "low" / None |
| `primary_failure_reason` | `str \| None` | dominant FailureReason 값 |
| `context` | `dict` | FeedbackContext.to_dict() |
| `hints` | `list[str]` | 다음 시도를 위한 인간 가독 힌트 |
| `should_continue` | `bool` | 미시도 전략이 남아있는지 여부 |
| `vision_judge_suggestion` | `str \| None` | JudgementResult.next_suggestion |

### 제약 조건 생성 규칙

| FailureReason | 추가 제약 조건 |
|---------------|---------------|
| `pipeline_bad_fit` | `"exclude pipeline block types: {block_types}"` (pipeline 제공 시) |
| `pipeline_bad_params` | `"expand parameter search range or shift distribution"` |
| `algorithm_wrong_category` | `"override algorithm category; avoid previously selected category"` |
| `runtime_error` | `"avoid pipeline variants that caused runtime errors"` |
| `inspection_plan_issue` | `"re-generate inspection plan with corrected dependency ordering"` |
| `spec_issue` | `"relax min_accuracy spec or flag to user as unrealistic"` |

### should_continue 로직

```
should_continue = len(tried_strategies) < 6
```
- 6가지 전략 모두 시도됐을 때 False
- 모든 항목 통과(no failures)인 경우도 tried_strategies 미증가 → True 유지

### Directive 처리

| 호출 방식 | 사용 값 |
|----------|---------|
| `FeedbackController(directive="X")` | 생성자 directive 저장 |
| `run(directive="Y")` | "Y" (runtime 우선) |
| `run(directive=None)` | 생성자 directive fallback |
| `run(directive="")` | 빈 문자열 (override) |

### 에러 처리 케이스

| 조건 | 응답 |
|------|------|
| `evaluation_result.status != "success"` | `status="error"`, `error_message` 전달, iteration 미증가 |
| `item_evaluations` 비어있음 | `status="success"`, `strategy=None`, `primary_failure_reason=None` |
| 모든 항목 통과 (failure_reason 없음) | `status="success"`, `strategy=None` |

### 테스트 커버리지

| 카테고리 | 테스트 수 |
|---------|---------|
| Instantiation | 9 |
| Strategy mapping (all 6 reasons × strategy + severity) | 14 |
| Dominant strategy selection | 7 |
| Vision Judge integration | 4 |
| Context accumulation | 7 |
| Pipeline tracking | 5 |
| Constraint generation | 9 |
| should_continue flag | 4 |
| reset() | 7 |
| Directive handling | 4 |
| Error handling | 8 |
| AgentResult structure | 12 |
| FeedbackContext.to_dict() | 4 |
| **합계** | **95** |

### pytest 결과
```
tests/test_feedback_controller.py: 95 passed in 0.14s
전체: 1459 passed, 0 failed, 5 skipped in 7.17s
```

### 이슈 및 특이사항
- LLM 어댑터 전혀 없음 — 100% 결정론적 규칙 기반 Python 로직
- `FeedbackController`는 `BaseAgent`를 상속하지 않음 (LLM 에이전트가 아닌 컨트롤러이므로 독립 클래스)
- `FeedbackContext.to_dict()`에서 `tried_strategies`(set) → list 변환으로 JSON 직렬화 보장
- `vision_judge_result.next_suggestion`이 빈 문자열이면 `None`으로 처리 (의미 없는 빈 제안 방지)
- `failed_pipelines` 중복 방지: `pipeline_id not in` 체크로 동일 파이프라인 재추가 차단

---

## Step 30 완료 내역

### 생성된 파일
- `agents/evaluation_agent.py` (신규)
- `tests/test_evaluation_agent.py` (신규)

### EvaluationAgent 인터페이스

**생성자**: `EvaluationAgent(directive: str = "")`

**run 시그니처**:
```python
async def run(
    self,
    test_result: AgentResult,
    mode: str = "inspection",
    pipeline: ProcessingPipeline | None = None,
    inspection_plan: InspectionPlan | None = None,
    success_criteria: dict | None = None,
    directive: str | None = None,
    **kwargs,
) -> AgentResult
```

### AgentResult data 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `item_evaluations` | list[dict] | 항목별 평가 결과 (item_id, passed, failure_reason, details) |
| `overall_passed` | bool | 전체 통과 여부 |
| `total_items` | int | 전체 항목 수 |
| `passed_items` | int | 통과 항목 수 |
| `failed_items` | int | 실패 항목 수 |
| `failure_summary` | dict[str, int] | failure_reason 별 카운트 |
| `failure_reason` | str \| None | align 모드 전용: 전체 실패 원인 |

### failure_reason 분류 로직

| 우선순위 | FailureReason | 조건 |
|---------|---------------|------|
| 1 | `runtime_error` | skipped=True, depends_on 없음 (또는 plan 없음) |
| 2 | `inspection_plan_issue` | skipped=True, depends_on 존재 |
| 3 | `spec_issue` | min_accuracy in success_criteria >= 0.95 |
| 4 | `algorithm_wrong_category` | pipeline block 타입이 item category와 불일치 |
| 5 | `pipeline_bad_fit` | accuracy < 0.5 |
| 6 | `pipeline_bad_params` | 0.5 <= accuracy (기본 fallback) |

### 알고리즘 카테고리 불일치 감지 규칙

| item.category | 불일치 조건 |
|---------------|------------|
| EDGE_DETECTION | pipeline에 edge 블록(canny/sobel/laplacian/scharr) 없음 |
| COLOR_FILTER | pipeline에 색상 블록(hsv_s/hsv_v/lab_l/ycrcb_cr) 없음 |
| BLOB | pipeline에 edge 블록만 있고 threshold/morphology 블록 없음 |

### 에러 처리

| 케이스 | 응답 |
|--------|------|
| test_result.status != "success" | status="error", error_message 전달 |
| item_results 비어있음 | status="success", total_items=0 |
| item_result 필드 누락 | 기본값(0.0/"") 사용, 크래시 없음 |

### directive 처리
- `directive=None` → `self.directive` (생성자 값) 사용
- `directive=""` → 빈 문자열 사용 (override)
- `directive="strict"/"lenient"` → 해당 값 사용

### 테스트 커버리지

| 테스트 클래스 | 테스트 수 | 내용 |
|------------|---------|------|
| TestEvaluationAgentInstantiation | 4 | 상속, name, directive |
| TestAgentResultStructure | 13 | status, data 키, item_evaluation 키 |
| TestPassedItems | 3 | 통과 항목 failure_reason=None |
| TestPipelineBadFit | 4 | accuracy < 0.5 경계 조건 |
| TestPipelineBadParams | 6 | 0.5~0.8, 높은 fp/fn rate |
| TestAlgorithmWrongCategory | 4 | EDGE/COLOR/BLOB 불일치 |
| TestRuntimeError | 2 | skipped + no depends_on |
| TestInspectionPlanIssue | 2 | skipped + depends_on |
| TestSpecIssue | 4 | min_accuracy >= 0.95 |
| TestAlignModeEvaluation | 6 | align 모드 전용 |
| TestMixedResults | 2 | 혼합 결과 카운트/summary |
| TestErrorHandling | 4 | 에러 전달, 빈 결과, 필드 누락 |
| TestDirectiveHandling | 4 | 생성자/run/None/빈 문자열 |
| TestOverallEvaluationSummary | 6 | 전체 카운트, summary 일치 |
| **합계** | **64** | |

### pytest 결과
```
tests/test_evaluation_agent.py: 64 passed in 0.14s
전체: 1364 passed, 0 failed, 5 skipped in 5.21s
```

### 이슈 및 특이사항
- `structlog` 패키지가 환경에 없어 별도 설치 (`pip install structlog --break-system-packages`)
- `pytest-asyncio>=0.23.0` 누락으로 async 테스트 미실행 → `requirements.txt`에 추가 후 설치
- `tests/test_models.py` 2개 테스트: Python 3.11에서 `asyncio.get_event_loop()` deprecated → `asyncio.run()`으로 수정
- `frontend/` 디렉토리 누락 → `mkdir frontend` 로 생성 (Step 35 이전 placeholder)
- `ALGORITHM_WRONG_CATEGORY`는 pipeline 파라미터 제공 시에만 감지됨 (pipeline=None이면 accuracy 기반으로 fallback)
- align 모드는 per-image 단위 평가 + 전체 failure_reason 단일 값 반환 (inspection 모드와 다른 구조)
