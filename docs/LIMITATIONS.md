# VIA2 Known Limitations

This document describes known limitations and intentional design decisions in VIA2 v3.0.

---

## AI Model Availability

All deep learning models (Depth-Anything-V2, Florence-2, DINOv2, Grounding DINO, SAM 2, Qwen2.5-VL, InternVL) require a Colab T4 GPU or equivalent. **Local mode only supports Qwen2.5-Coder via Ollama.**

In local mode, the Depth, Material, and ROI agents return mock/fallback results. The pipeline still completes, but analysis quality is significantly reduced.

---

## Colab Session Timeout

Free Google Colab sessions disconnect after approximately **90 minutes of inactivity**. When the session ends:

- All loaded models are unloaded.
- The Cloudflare tunnel URL changes on reconnect.
- Any unsaved presets are lost.

**Mitigation**: Save presets regularly. After reconnecting, update the Remote URL in Engine Settings and click Test Connection.

---

## Light Test Accuracy

The PBR rendering engine uses a Canvas 2D approximation of Cook-Torrance BRDF with simplified shadow ray marching. It is a **visual design aid**, not an optical simulator.

For quantitative optical analysis (illuminance, wavelength-dependent effects, multi-bounce reflections), use dedicated tools such as Zemax OpticStudio or LightTools.

---

## Blueprint as Design Guide

SVG Blueprint output is a **library-agnostic algorithm design guide**. It describes the vision algorithm as a sequence of processing blocks with parameters, but does not produce executable code.

Implementing the Blueprint in OpenCV, Cognex VisionPro, or Halcon requires manual translation by a vision engineer.

---

## Polarization Simulation

Polarization effects are modeled using **Malus's Law** (I = I₀ · cos²θ). The following are **not** modeled:

- Multi-layer polarization stacking
- Wavelength-dependent birefringence
- Elliptical or circular polarization states
- Fresnel reflection polarization

---

## Align Mode Decision

In Align Mode, the Decision Agent only produces **HARDWARE_IMPROVEMENT** recommendations. Edge Learning (EL) and Deep Learning (DL) recommendations are intentionally excluded from alignment tasks by design — coordinate extraction is treated as a classical computer vision problem.

---

## Image Format Support

VIA2 supports **JPEG and PNG** only. The following are not supported:

- 16-bit images (uint16 TIFF)
- RAW camera formats (CR2, ARW, NEF, etc.)
- Multi-channel images beyond RGB (e.g., 4-channel RGBA, multispectral)
- Images larger than 4096 × 4096 pixels (may cause memory issues in the Colab pipeline)

---

## macOS Intel Only (Packaged Build)

The DMG package targets **x86_64 (Intel Mac)**. On Apple Silicon (M1/M2/M3):

- Running under **Rosetta 2** is the simplest option and should work for most features.
- A native arm64 build requires a separate `electron-builder` configuration (`arch: arm64`).
- PyTorch MPS acceleration is not used — the app is designed for CPU-local inference + remote GPU.

---

## Parameter Sheet Data Structure

The ParameterSheet component expects `Record<string, unknown>` (key-based lookup). The backend Orchestrator returns `parameter_sheets` as an array `[{node_id, node_name, parameters}]`. The frontend currently converts this on receipt; if the API schema changes, the ResultPanel connector code must be updated.

---

## Preset Storage

Light Test presets are stored in **process memory** (`_presets` dict in the FastAPI backend). They do not persist across backend restarts. Exporting presets to disk is not yet implemented.
