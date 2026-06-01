# VIA2 Installation Guide

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| Hardware | Intel Mac (x86_64) |
| macOS | 12 Monterey or later |
| Python | 3.11 |
| Node.js | 18 LTS or later |
| Git | Any recent version |
| Disk space | ~2 GB (excluding model weights) |

> **Apple Silicon (M1/M2/M3)**: The packaged DMG targets x86_64. You can run VIA2 under Rosetta 2, or build from source. See [LIMITATIONS.md](LIMITATIONS.md).

---

## Step-by-Step Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd VIA2
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

Verify Python version:

```bash
python --version  # should print Python 3.11.x
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, uvicorn, OpenCV, NumPy, httpx, and all other backend packages. PyTorch is included for local CPU inference; GPU-accelerated models run on Colab.

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set the values appropriate for your setup. At minimum:

- `ENGINE_MODE=local` — use local Ollama (default)
- `ENGINE_MODE=remote` — use a Colab tunnel URL (see [MODEL_SETUP.md](MODEL_SETUP.md))

---

## Running in Development Mode

Open two terminal windows.

**Terminal 1 — Backend:**

```bash
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`.

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

This launches Electron in development mode with hot reload.

---

## Running the Packaged App

1. Download or build the DMG (`npm run dist` in the `frontend/` directory).
2. Open the `.dmg` file.
3. Drag **VIA2** to your Applications folder.
4. Launch VIA2 from Applications or Spotlight.

The packaged app auto-starts the FastAPI backend on launch. If the engine health check fails, the **Engine Setup Guide** modal will appear.

---

## Troubleshooting

### Port 8000 already in use

```bash
lsof -i :8000
kill -9 <PID>
```

Or change the port in `.env` (`BACKEND_PORT=8001`) and restart.

### Python path issues

Make sure the virtual environment is activated before running pytest or uvicorn:

```bash
which python  # should point to venv/bin/python
source venv/bin/activate
```

### Electron shows a blank screen

This usually means the backend did not start in time or the frontend build is missing.

1. Confirm `http://127.0.0.1:8000/health` returns `{"status": "ok"}`.
2. In development mode, wait for the webpack dev server to finish compiling before the window loads.
3. In packaged mode, check the Electron DevTools console (`Cmd+Option+I`) for errors.

### npm install fails on Node version mismatch

```bash
node --version  # must be 18.x or 20.x
nvm use 18      # if using nvm
```
