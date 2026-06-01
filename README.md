# VIA2 — Vision Intelligence Agent v3.0

Multi-agent AI desktop application for automated computer vision algorithm design.

---

## Architecture Overview

```
[Desktop UI: Electron + React + Redux]
  ┌─────────────────┐    ┌──────────────────┐
  │ Main Workspace  │    │ Light Test Window│ ← fully isolated
  │ - ROI Setup     │    │ - Front + Top View│
  │ - Directives    │    │ - Virtual Lighting│
  │ - Blueprint     │    │ - Polarization   │
  └────────┬────────┘    └──────────────────┘
           ↓
   [FastAPI Local Server :8000]
           ↓
    [AI Engine Adapter]
   (Local Ollama / Remote Colab URL)
           ↓
  ┌────────────────────────────────────────┐
  │  Multi-Agent Orchestration             │
  │  ├ Spec Agent          (Qwen2.5-Coder) │
  │  ├ Image Analysis      (OpenCV)        │
  │  ├ Depth Agent         (Depth-V2)      │
  │  ├ Material Agent      (Florence-2)    │
  │  ├ ROI Agent           (DINO + SAM 2)  │
  │  ├ Pipeline Composer   (Rule-based)    │
  │  ├ Vision Judge        (Qwen2.5-VL)    │
  │  ├ Inspection Plan     (Qwen2.5-Coder) │
  │  ├ Blueprint Agent     (SVG output)    │
  │  └ Decision Agent      (InternVL)      │
  └────────────────────────────────────────┘
```

---

## Features

### Inspection Mode
Designs a binary OK/NG classification algorithm from uploaded sample images.
- Multi-agent analysis: depth, material, ROI, preprocessing pipeline selection
- SVG Blueprint output with per-node parameters
- Inspection metrics: Accuracy, FP Rate, FN Rate
- Decision recommendation: Rule-Based / Edge Learning / Deep Learning

### Align Mode
Designs an X/Y coordinate extraction algorithm for fiducial-based alignment.
- Coordinate error (px) and success rate metrics
- Hardware Improvement recommendation (no EL/DL for alignment tasks)

### Light Test Window
Standalone virtual lighting simulation tool, fully isolated from the main pipeline.
- PBR rendering engine (Cook-Torrance BRDF with shadow ray marching)
- 6 light shapes: Ring, Bar, Spot, Coaxial, Dome, Low-Angle Ring
- Color lighting (RGB) + polarization simulation (Malus's Law)
- Real-time histogram and depth/material analysis
- Preset save/load

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd VIA2

# 2. Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env to set ENGINE_MODE and URLs

# 6. Run backend
uvicorn backend.main:app --reload --port 8000

# 7. Run frontend (separate terminal)
cd frontend && npm run dev
```

See [docs/INSTALL.md](docs/INSTALL.md) for full installation instructions and [docs/MODEL_SETUP.md](docs/MODEL_SETUP.md) for AI model configuration.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, uvicorn |
| Frontend | Electron, React 18, TypeScript, TailwindCSS, Redux Toolkit |
| Computer Vision | OpenCV, NumPy, PyTorch |
| AI Models (Remote) | Depth-Anything-V2, Florence-2, DINOv2, Grounding DINO, SAM 2, Qwen2.5-VL, InternVL |
| AI Models (Local) | Ollama + Qwen2.5-Coder:7b |
| Rendering | Canvas 2D, PBR renderer (custom NumPy) |
| Testing | pytest, Jest, React Testing Library |
| Packaging | electron-builder (macOS DMG, x86_64) |

---

## Development Commands

| Command | Description |
|---------|-------------|
| `pytest --ignore=tests/e2e -q` | Run backend unit tests |
| `pytest tests/e2e -q` | Run backend E2E tests |
| `cd frontend && npm test -- --watchAll=false` | Run frontend tests |
| `cd frontend && npx tsc --noEmit` | TypeScript type check |
| `cd frontend && npm run build` | Production build |
| `cd frontend && npm run dist` | Build macOS DMG |

---

## Known Limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for a full list of known limitations and design decisions.

---

## License

MIT
