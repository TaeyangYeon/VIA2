"""
Generate verify_vision_models.ipynb for VIA2 SOTA model verification on Google Colab T4.
"""
from pathlib import Path
import nbformat

nb = nbformat.v4.new_notebook()

# Cell 1 — Markdown: title
cell1 = nbformat.v4.new_markdown_cell(
    "# VIA2 SOTA Vision Model Verification\n\n"
    "Google Colab T4 GPU에서 5개 SOTA 비전 모델의 로드/추론/메모리를 검증합니다.\n\n"
    "모델 목록:\n"
    "1. Florence-2 (microsoft/Florence-2-base)\n"
    "2. Grounding DINO (IDEA-Research/grounding-dino-base)\n"
    "3. SAM 2 (facebook/sam2-hiera-small)\n"
    "4. DINOv2 (facebook/dinov2-base)\n"
    "5. Depth-Anything-V2 (depth-anything/Depth-Anything-V2-Small-hf)"
)

# Cell 2 — Code: pip install
cell2 = nbformat.v4.new_code_cell(
    "# Install required packages\n"
    "!pip install -q transformers accelerate timm einops\n"
    "!pip install -q torch torchvision\n"
    "!pip install -q Pillow requests supervision\n"
    'print("Installation complete.")'
)

# Cell 3 — Code: common utilities
cell3 = nbformat.v4.new_code_cell(
    "import torch\n"
    "import gc\n"
    "import requests\n"
    "from PIL import Image\n"
    "from io import BytesIO\n"
    "\n"
    "# GPU memory helper\n"
    "def get_gpu_mem():\n"
    "    if torch.cuda.is_available():\n"
    "        return torch.cuda.memory_allocated() / 1024**3\n"
    "    return 0.0\n"
    "\n"
    "# Download sample image once\n"
    'IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/320px-Cute_dog.jpg"\n'
    "try:\n"
    "    response = requests.get(IMAGE_URL, timeout=10)\n"
    "    sample_image = Image.open(BytesIO(response.content)).convert(\"RGB\")\n"
    '    print(f"Sample image loaded: {sample_image.size}")\n'
    "except Exception as e:\n"
    '    print(f"Image download failed: {e}. Using fallback solid color image.")\n'
    "    sample_image = Image.new(\"RGB\", (320, 320), color=(128, 128, 128))\n"
    '    print(f"Fallback image created: {sample_image.size}")\n'
    "\n"
    "# Results collection\n"
    "results = {}\n"
    'print(f"CUDA available: {torch.cuda.is_available()}")\n'
    "if torch.cuda.is_available():\n"
    '    print(f"GPU: {torch.cuda.get_device_name(0)}")\n'
    '    print(f"VRAM total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")'
)

# Cell 4 — Markdown: Florence-2
cell4 = nbformat.v4.new_markdown_cell(
    "## 1. Florence-2\n\n"
    "- **HuggingFace**: `florence-community/Florence-2-base` (transformers 5.x native) / "
    "`microsoft/Florence-2-base` (transformers 4.x fallback)\n"
    "- **VIA2 역할**: Material Agent — 소재 분류 및 이미지 캡셔닝 (Step 16)"
)

# Cell 5 — Code: Florence-2
cell5 = nbformat.v4.new_code_cell(
    'result_florence2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}\n'
    "try:\n"
    "    torch.cuda.empty_cache()\n"
    "    mem_before = get_gpu_mem()\n"
    "    \n"
    '    device = "cuda" if torch.cuda.is_available() else "cpu"\n'
    "    from transformers import AutoProcessor\n"
    "    try:\n"
    "        # transformers 5.x: native Florence-2 support\n"
    "        from transformers import Florence2ForConditionalGeneration\n"
    "        model = Florence2ForConditionalGeneration.from_pretrained(\n"
    '            "florence-community/Florence-2-base",\n'
    "            dtype=torch.float16,\n"
    '            device_map="auto"\n'
    "        )\n"
    '        processor = AutoProcessor.from_pretrained("florence-community/Florence-2-base")\n'
    '        print("Florence-2: using native checkpoint (transformers 5.x)")\n'
    "    except (ImportError, Exception) as load_e:\n"
    '        print(f"Native checkpoint failed: {load_e}\\nFalling back to microsoft/Florence-2-base...")\n'
    "        from transformers import AutoModelForCausalLM\n"
    "        model = AutoModelForCausalLM.from_pretrained(\n"
    '            "microsoft/Florence-2-base",\n'
    "            torch_dtype=torch.float16,\n"
    '            device_map="auto",\n'
    "            trust_remote_code=True,\n"
    '            attn_implementation="eager"\n'
    "        )\n"
    '        processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base", trust_remote_code=True)\n'
    '        print("Florence-2: using microsoft checkpoint (trust_remote_code)")\n'
    '    result_florence2["loaded"] = True\n'
    "    mem_after = get_gpu_mem()\n"
    '    print(f"Florence-2 loaded. GPU mem: {mem_after:.2f} GB")\n'
    "    \n"
    '    inputs = processor(text="<CAPTION>", images=sample_image, return_tensors="pt").to(model.device, torch.float16)\n'
    "    output = model.generate(**inputs, max_new_tokens=50)\n"
    '    caption = processor.decode(output[0], skip_special_tokens=True)\n'
    '    print(f"Caption: {caption}")\n'
    '    result_florence2["inferred"] = True\n'
    '    result_florence2["gpu_mem_gb"] = mem_after - mem_before\n'
    "except Exception as e:\n"
    '    print(f"Florence-2 ERROR: {e}")\n'
    "    import traceback; traceback.print_exc()\n"
    "finally:\n"
    "    try:\n"
    "        del model, processor\n"
    "    except: pass\n"
    "    torch.cuda.empty_cache(); gc.collect()\n"
    "\n"
    'results["Florence-2"] = result_florence2\n'
    'print(f"Florence-2 result: {result_florence2}")'
)

# Cell 6 — Markdown: Grounding DINO
cell6 = nbformat.v4.new_markdown_cell(
    "## 2. Grounding DINO\n\n"
    "- **HuggingFace**: `IDEA-Research/grounding-dino-base`\n"
    "- **VIA2 역할**: ROI Agent — 텍스트 프롬프트로 결함/부품 영역 검출 (Step 17)"
)

# Cell 7 — Code: Grounding DINO
cell7 = nbformat.v4.new_code_cell(
    'result_grounding_dino = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}\n'
    "try:\n"
    "    torch.cuda.empty_cache()\n"
    "    mem_before = get_gpu_mem()\n"
    "    \n"
    "    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection\n"
    '    processor = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")\n'
    '    model = AutoModelForZeroShotObjectDetection.from_pretrained("IDEA-Research/grounding-dino-base")\n'
    '    device = "cuda" if torch.cuda.is_available() else "cpu"\n'
    "    model = model.to(device)\n"
    '    result_grounding_dino["loaded"] = True\n'
    "    mem_after = get_gpu_mem()\n"
    '    print(f"Grounding DINO loaded. GPU mem: {mem_after:.2f} GB")\n'
    "    \n"
    '    text_prompt = "a dog. a cat. a person."\n'
    '    inputs = processor(images=sample_image, text=text_prompt, return_tensors="pt").to(device)\n'
    "    with torch.no_grad():\n"
    "        outputs = model(**inputs)\n"
    "    target_sizes = torch.tensor([sample_image.size[::-1]])\n"
    "    results_det = processor.post_process_grounded_object_detection(\n"
    "        outputs, inputs.input_ids, threshold=0.3, text_threshold=0.3, target_sizes=target_sizes\n"
    "    )\n"
    "    print(f\"Detections: {len(results_det[0]['boxes'])} boxes\")\n"
    '    result_grounding_dino["inferred"] = True\n'
    '    result_grounding_dino["gpu_mem_gb"] = mem_after - mem_before\n'
    "except Exception as e:\n"
    '    print(f"Grounding DINO ERROR: {e}")\n'
    "    import traceback; traceback.print_exc()\n"
    "finally:\n"
    "    try:\n"
    "        del model, processor\n"
    "    except: pass\n"
    "    torch.cuda.empty_cache(); gc.collect()\n"
    "\n"
    'results["Grounding DINO"] = result_grounding_dino\n'
    'print(f"Grounding DINO result: {result_grounding_dino}")'
)

# Cell 8 — Markdown: SAM 2
cell8 = nbformat.v4.new_markdown_cell(
    "## 3. SAM 2\n\n"
    "- **HuggingFace**: `facebook/sam2-hiera-small`\n"
    "- **VIA2 역할**: ROI Agent — 결함 영역 정밀 세그멘테이션 (Step 17)"
)

# Cell 9 — Code: SAM 2
cell9 = nbformat.v4.new_code_cell(
    'result_sam2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}\n'
    "try:\n"
    "    torch.cuda.empty_cache()\n"
    "    mem_before = get_gpu_mem()\n"
    "    \n"
    "    from transformers import pipeline\n"
    '    pipe = pipeline("mask-generation", model="facebook/sam2-hiera-small", device=0 if torch.cuda.is_available() else -1)\n'
    '    result_sam2["loaded"] = True\n'
    "    mem_after = get_gpu_mem()\n"
    '    print(f"SAM 2 loaded. GPU mem: {mem_after:.2f} GB")\n'
    "    outputs = pipe(sample_image, points_per_batch=64)\n"
    "    print(f\"SAM 2 masks generated: {len(outputs.get('masks', []))}\")\n"
    '    result_sam2["inferred"] = True\n'
    '    result_sam2["gpu_mem_gb"] = mem_after - mem_before\n'
    "except Exception as e:\n"
    '    print(f"SAM 2 ERROR: {e}")\n'
    "    import traceback; traceback.print_exc()\n"
    "finally:\n"
    "    try:\n"
    "        del pipe\n"
    "    except: pass\n"
    "    torch.cuda.empty_cache(); gc.collect()\n"
    "\n"
    'results["SAM 2"] = result_sam2\n'
    'print(f"SAM 2 result: {result_sam2}")'
)

# Cell 10 — Markdown: DINOv2
cell10 = nbformat.v4.new_markdown_cell(
    "## 4. DINOv2\n\n"
    "- **HuggingFace**: `facebook/dinov2-base`\n"
    "- **VIA2 역할**: Material Agent + Decision Agent — 특징 벡터 기반 소재 유사도 비교 (Step 16, 32)"
)

# Cell 11 — Code: DINOv2
cell11 = nbformat.v4.new_code_cell(
    'result_dinov2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}\n'
    "try:\n"
    "    torch.cuda.empty_cache()\n"
    "    mem_before = get_gpu_mem()\n"
    "    \n"
    "    from transformers import AutoImageProcessor, AutoModel\n"
    '    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")\n'
    '    model = AutoModel.from_pretrained("facebook/dinov2-base")\n'
    '    device = "cuda" if torch.cuda.is_available() else "cpu"\n'
    "    model = model.to(device)\n"
    '    result_dinov2["loaded"] = True\n'
    "    mem_after = get_gpu_mem()\n"
    '    print(f"DINOv2 loaded. GPU mem: {mem_after:.2f} GB")\n'
    "    \n"
    '    inputs = processor(images=sample_image, return_tensors="pt").to(device)\n'
    "    with torch.no_grad():\n"
    "        outputs = model(**inputs)\n"
    "    embedding = outputs.last_hidden_state[:, 0, :]\n"
    '    print(f"DINOv2 embedding shape: {embedding.shape}")\n'
    '    result_dinov2["inferred"] = True\n'
    '    result_dinov2["gpu_mem_gb"] = mem_after - mem_before\n'
    "except Exception as e:\n"
    '    print(f"DINOv2 ERROR: {e}")\n'
    "    import traceback; traceback.print_exc()\n"
    "finally:\n"
    "    try:\n"
    "        del model, processor\n"
    "    except: pass\n"
    "    torch.cuda.empty_cache(); gc.collect()\n"
    "\n"
    'results["DINOv2"] = result_dinov2\n'
    'print(f"DINOv2 result: {result_dinov2}")'
)

# Cell 12 — Markdown: Depth-Anything-V2
cell12 = nbformat.v4.new_markdown_cell(
    "## 5. Depth-Anything-V2\n\n"
    "- **HuggingFace**: `depth-anything/Depth-Anything-V2-Small-hf`\n"
    "- **VIA2 역할**: Depth Agent — 소재 표면 깊이 맵 추정 (Step 15)"
)

# Cell 13 — Code: Depth-Anything-V2
cell13 = nbformat.v4.new_code_cell(
    'result_depth = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}\n'
    "try:\n"
    "    torch.cuda.empty_cache()\n"
    "    mem_before = get_gpu_mem()\n"
    "    \n"
    "    from transformers import AutoImageProcessor, AutoModelForDepthEstimation\n"
    '    processor = AutoImageProcessor.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")\n'
    '    model = AutoModelForDepthEstimation.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")\n'
    '    device = "cuda" if torch.cuda.is_available() else "cpu"\n'
    "    model = model.to(device)\n"
    '    result_depth["loaded"] = True\n'
    "    mem_after = get_gpu_mem()\n"
    '    print(f"Depth-Anything-V2 loaded. GPU mem: {mem_after:.2f} GB")\n'
    "    \n"
    '    inputs = processor(images=sample_image, return_tensors="pt").to(device)\n'
    "    with torch.no_grad():\n"
    "        outputs = model(**inputs)\n"
    "    depth_map = outputs.predicted_depth\n"
    '    print(f"Depth map shape: {depth_map.shape}")\n'
    '    result_depth["inferred"] = True\n'
    '    result_depth["gpu_mem_gb"] = mem_after - mem_before\n'
    "except Exception as e:\n"
    '    print(f"Depth-Anything-V2 ERROR: {e}")\n'
    "    import traceback; traceback.print_exc()\n"
    "finally:\n"
    "    try:\n"
    "        del model, processor\n"
    "    except: pass\n"
    "    torch.cuda.empty_cache(); gc.collect()\n"
    "\n"
    'results["Depth-Anything-V2"] = result_depth\n'
    'print(f"Depth-Anything-V2 result: {result_depth}")'
)

# Cell 14 — Markdown: Summary header
cell14 = nbformat.v4.new_markdown_cell("## Summary")

# Cell 15 — Code: summary table
cell15 = nbformat.v4.new_code_cell(
    'print("\\n" + "="*60)\n'
    'print("VERIFICATION SUMMARY")\n'
    'print("="*60)\n'
    "print(f\"{'Model':<30} {'Loaded':<10} {'Inferred':<12} {'GPU Mem (GB)':<15}\")\n"
    'print("-"*67)\n'
    "for name, res in results.items():\n"
    "    print(f\"{name:<30} {str(res['loaded']):<10} {str(res['inferred']):<12} {res['gpu_mem_gb']:<15.2f}\")\n"
    'print("="*60)\n'
    'print("\\nNote: GPU Mem shows delta after model load (before inference).")\n'
    'print("Run on Colab T4 to get actual measurements.")'
)

nb.cells = [
    cell1, cell2, cell3,
    cell4, cell5,
    cell6, cell7,
    cell8, cell9,
    cell10, cell11,
    cell12, cell13,
    cell14, cell15,
]

nb.metadata = {
    "colab": {
        "name": "verify_vision_models.ipynb",
        "provenance": [],
        "gpuClass": "standard",
        "accelerator": "GPU"
    },
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.10.0"
    }
}

output_path = Path(__file__).parent / "verify_vision_models.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)
print(f"Notebook written to {output_path}")
