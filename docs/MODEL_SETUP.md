# VIA2 AI Model Setup Guide

> **Overview**: All deep learning inference in VIA2 runs on a remote GPU (Google Colab T4), not on your local Intel Mac. Local mode supports only Qwen2.5-Coder:7b via Ollama (CPU).

---

## Section A — Local Mode (Ollama)

Local mode runs Qwen2.5-Coder:7b on your Mac CPU via Ollama. Depth, Material, and ROI agents will return mock/fallback results without a Colab connection.

### Install Ollama

```bash
brew install ollama
```

### Pull the model

```bash
ollama pull qwen2.5-coder:7b
```

### Start the Ollama server

```bash
ollama serve
```

### Verify

```bash
curl http://localhost:11434/api/tags
```

Expected response includes `"qwen2.5-coder:7b"` in the model list.

### Configure VIA2

In `.env`:

```
ENGINE_MODE=local
OLLAMA_URL=http://localhost:11434
```

In the VIA2 app: open **Engine Settings**, select **Local**, confirm the Ollama status indicator is green.

---

## Section B — Remote Mode via Google Colab (Recommended)

All SOTA vision models run on a Colab T4 GPU and are accessed through a Cloudflare tunnel.

### Setup

1. Open `colab/VIA2_Setup.ipynb` in Google Colab.
2. In the top menu: **Runtime → Change runtime type → T4 GPU → Save**.
3. Run all cells (`Runtime → Run all`).
4. Wait for the tunnel URL to appear in the output — it looks like:
   ```
   https://xxxx.trycloudflare.com
   ```
5. Copy that URL.
6. In the VIA2 app: open **Engine Settings**, select **Remote**, paste the URL into the **Remote URL** field, click **Test Connection**.
7. The status indicator should turn green.

### Models loaded on demand

VIA2 loads and unloads models per agent step to stay within T4's 16 GB VRAM:

| Agent Step | Model | Approx. VRAM |
|------------|-------|-------------|
| Image Analysis | OpenCV (CPU) | 0 |
| Depth | Depth-Anything-V2-Small | ~2 GB |
| Material | Florence-2-base + DINOv2-base | ~3 GB |
| ROI | Grounding DINO-base + SAM 2 hiera-small | ~4 GB |
| Vision Judge | Qwen2.5-VL-7B | ~8 GB |
| Decision | InternVL-2-8B | ~8 GB |
| Blueprint / Spec | Qwen2.5-Coder:7b (via Ollama) | ~5 GB |

> The T4 (16 GB) cannot hold all models simultaneously. Each agent loads its model, runs inference, then releases GPU memory with `torch.cuda.empty_cache()` before the next agent runs.

### Colab session notes

- Free Colab sessions disconnect after approximately 90 minutes of inactivity. Save any presets before the session ends.
- After reconnecting, a new tunnel URL is generated. Update the Remote URL in Engine Settings and click **Test Connection** again.

---

## Section C — Engine Settings UI Reference

| Setting | Description |
|---------|-------------|
| **Local** toggle | Activates Ollama mode. Ollama must be running at `OLLAMA_URL`. |
| **Remote** toggle | Activates remote Colab/Azure mode. |
| **Remote URL** field | Paste the Cloudflare tunnel URL here (e.g., `https://xxxx.trycloudflare.com`). |
| **Test Connection** | Sends a health check to the configured endpoint. Status turns green on success. |
| **Save** | Persists the settings to `~/.via2/engine_config.json`. |

---

## Advanced: Using Azure or a Custom GPU Server

Set `ENGINE_MODE=remote` and point `REMOTE_AI_URL` in `.env` to any server that implements the VIA2 Colab API contract (`POST /colab/<model>/infer`). Authentication token can be passed via `REMOTE_AUTH_TOKEN` in Engine Settings.
