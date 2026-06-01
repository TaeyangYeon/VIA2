# VIA2 Final Integration Test Checklist

## Prerequisites
- [ ] DMG installed and app launches without errors
- [ ] Colab notebook running (tunnel URL ready)
- [ ] Engine Settings → Remote, URL pasted, Test Connection returns green status
- [ ] At least 5 sample images prepared (3 OK + 2 NG for Scenario 1)

---

## Scenario 1: Inspection — Happy Path

**Goal**: Full pipeline produces Blueprint SVG and inspection metrics

- [ ] Upload 3 OK images + 2 NG images via the Input Panel
- [ ] Draw ROI on the canvas (drag a rectangle over the region of interest)
- [ ] Set mode: **Inspection**, `min_accuracy: 0.85`
- [ ] Click **Execute**
- [ ] Agents progress through all steps in the ExecutionPanel (Spec → Image Analysis → Depth → Material → ROI → Pipeline Composer → Vision Judge → Blueprint → Evaluation)
- [ ] Blueprint SVG renders in ResultPanel
- [ ] Click a node in the Blueprint → ParameterSheet side panel opens with node parameters
- [ ] Inspection metrics table shows Accuracy / FP Rate / FN Rate rows
- [ ] Click **Export SVG** → `.svg` file is downloaded
- [ ] Click **Export PDF** → `.pdf` file is downloaded
- [ ] Click **Export Parameters** → `.json` file is downloaded

**Expected**: All checkboxes pass

---

## Scenario 2: Directive Influence

**Goal**: Agent directives change pipeline behavior

- [ ] In DirectivePanel, set **Vision Judge** directive: `"prioritize edge contrast"`
- [ ] Set **Pipeline Composer** directive: `"prefer clahe preprocessing"`
- [ ] Execute with the same images as Scenario 1
- [ ] Verify ExecutionPanel shows the directive was applied (agent step notes or summary text)
- [ ] Compare the resulting Blueprint with Scenario 1 — the preprocessing block should include a CLAHE step

**Expected**: Blueprint differs from Scenario 1 due to directives

---

## Scenario 3: EL/DL Decision

**Goal**: Difficult images trigger Decision Agent recommendation

- [ ] Upload images with high texture variation (complex or noisy surface)
- [ ] Set `min_accuracy: 0.99` (extreme target)
- [ ] Click Execute
- [ ] Observe retry loop in ExecutionPanel (up to `MAX_ITERATIONS = 3` iterations)
- [ ] Decision Agent result appears: **EDGE_LEARNING** or **DEEP_LEARNING**
- [ ] Decision reasoning text is displayed in the Decision card
- [ ] "Light Test로 가서 검증해보세요" button is visible in the LightingSuggestion card

**Expected**: EL or DL recommendation with reasoning text

---

## Scenario 4: Align Mode

**Goal**: Align pipeline produces coordinate metrics only — no Blueprint

- [ ] Switch mode to **Align** in ConfigPanel
- [ ] Upload images with visible fiducial marks
- [ ] Draw ROI around the fiducial area
- [ ] Click Execute
- [ ] Verify **no SVG Blueprint** appears in ResultPanel
- [ ] Coordinate error (px) and success rate are displayed in the metrics section
- [ ] Decision result shows **HARDWARE_IMPROVEMENT** (no EL/DL for Align mode)

**Expected**: Coordinate metrics only, no Blueprint, hardware improvement suggestion

---

## Scenario 5: Light Test Window

**Goal**: Full Light Test workflow — rendering, controls, presets

- [ ] Open Light Test from the **Tools → Light Test** menu (or sidebar)
- [ ] Upload a test image via drag-and-drop or the Browse button
- [ ] Click **Analyze** → Depth Map and Material Map are rendered in the dual-view layout
- [ ] Click **Add Light** in LightController → a new Ring light appears
- [ ] Drag the light icon in FrontView → TopView position syncs on the shared X axis
- [ ] Change light color (R/G/B sliders) → rendered image updates with the new tint
- [ ] Enable the lens polarizer checkbox, rotate the angle dial → metal/glass surface highlights dim
- [ ] Click **Save Preset**, enter name `"ring_test_1"` → preset is saved
- [ ] Change light settings, then reload `"ring_test_1"` → all settings are restored to saved values

**Expected**: All visual changes appear in real-time; preset save/load works correctly
