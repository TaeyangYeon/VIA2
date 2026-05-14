# ==============================================================================
# COLAB SETUP: Uncomment and run the following pip installs before executing
# ==============================================================================
# !pip install transformers accelerate timm einops
# !pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# !pip install Pillow requests
# !pip install sam2  # for SAM 2 (if transformers version insufficient)
# ==============================================================================

import gc
import torch
import requests
from PIL import Image
from io import BytesIO
from transformers import (
    AutoProcessor,
    AutoModelForCausalLM,
    AutoModelForZeroShotObjectDetection,
    AutoModelForUniversalSegmentation,
    AutoImageProcessor,
    AutoModel,
    AutoModelForDepthEstimation,
    pipeline,
)


# ── Helper: GPU memory usage ──────────────────────────────────────────────────
def get_gpu_mem() -> float:
    """Return current GPU memory allocated in GB, or 0.0 if CUDA unavailable."""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024**3
    return 0.0


# ── Download sample image once ────────────────────────────────────────────────
IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/"
    "Cute_dog.jpg/320px-Cute_dog.jpg"
)
print("Downloading sample image...")
_resp = requests.get(IMAGE_URL, timeout=30)
_resp.raise_for_status()
sample_image = Image.open(BytesIO(_resp.content)).convert("RGB")
print(f"Image downloaded: {sample_image.size} (width x height)")

# ── Results container ─────────────────────────────────────────────────────────
results = {}


# ── Section 1: Florence-2 ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Section 1: Florence-2")
print("=" * 60)

result_florence2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}

try:
    torch.cuda.empty_cache()
    mem_before = get_gpu_mem()

    processor = AutoProcessor.from_pretrained(
        "microsoft/Florence-2-base",
        trust_remote_code=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Florence-2-base",
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    result_florence2["loaded"] = True
    mem_after_load = get_gpu_mem()
    print(f"Model loaded. GPU memory: {mem_after_load:.2f} GB")

    task_prompt = "<CAPTION>"
    inputs = processor(text=task_prompt, images=sample_image, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=64,
            num_beams=1,
        )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed = processor.post_process_generation(
        generated_text, task=task_prompt, image_size=sample_image.size
    )
    print(f"Caption: {parsed}")

    result_florence2["inferred"] = True
    result_florence2["gpu_mem_gb"] = mem_after_load - mem_before
    print("Inference success.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    try:
        del model, processor
    except Exception:
        pass
    torch.cuda.empty_cache()
    gc.collect()

results["Florence-2"] = result_florence2


# ── Section 2: Grounding DINO ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Section 2: Grounding DINO")
print("=" * 60)

result_grounding_dino = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}

try:
    torch.cuda.empty_cache()
    mem_before = get_gpu_mem()

    processor = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")
    model = AutoModelForZeroShotObjectDetection.from_pretrained(
        "IDEA-Research/grounding-dino-base"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    result_grounding_dino["loaded"] = True
    mem_after_load = get_gpu_mem()
    print(f"Model loaded. GPU memory: {mem_after_load:.2f} GB")

    text_prompt = "a cat. a dog. a person."
    inputs = processor(images=sample_image, text=text_prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    results_post = processor.post_process_grounded_object_detection(
        outputs,
        inputs["input_ids"],
        box_threshold=0.3,
        text_threshold=0.25,
        target_sizes=[sample_image.size[::-1]],
    )
    detections = results_post[0]
    print(f"Detected {len(detections['boxes'])} boxes.")
    for score, label, box in zip(
        detections["scores"], detections["labels"], detections["boxes"]
    ):
        print(f"  {label}: {score:.3f} @ {[round(v, 1) for v in box.tolist()]}")

    result_grounding_dino["inferred"] = True
    result_grounding_dino["gpu_mem_gb"] = mem_after_load - mem_before
    print("Inference success.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    try:
        del model, processor
    except Exception:
        pass
    torch.cuda.empty_cache()
    gc.collect()

results["Grounding DINO"] = result_grounding_dino


# ── Section 3: SAM 2 ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Section 3: SAM 2")
print("=" * 60)

result_sam2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}

try:
    torch.cuda.empty_cache()
    mem_before = get_gpu_mem()

    # Try transformers AutoModel approach first; fall back to pipeline
    try:
        processor = AutoProcessor.from_pretrained("facebook/sam2-hiera-small")
        model = AutoModelForUniversalSegmentation.from_pretrained(
            "facebook/sam2-hiera-small"
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)

        result_sam2["loaded"] = True
        mem_after_load = get_gpu_mem()
        print(f"Model loaded (AutoModel). GPU memory: {mem_after_load:.2f} GB")

        # Center point prompt
        w, h = sample_image.size
        input_points = [[[w // 2, h // 2]]]
        input_labels = [[1]]

        inputs = processor(
            images=sample_image,
            input_points=input_points,
            input_labels=input_labels,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        masks = processor.post_process_masks(
            outputs.pred_masks,
            inputs["original_sizes"],
            inputs["reshaped_input_sizes"],
        )
        print(f"Segmentation masks shape: {masks[0].shape}")

        result_sam2["inferred"] = True
        result_sam2["gpu_mem_gb"] = mem_after_load - mem_before
        print("Inference success.")

    except Exception as inner_e:
        print(f"AutoModel approach failed ({inner_e}), trying pipeline fallback...")
        # Pipeline fallback
        seg_pipeline = pipeline(
            "mask-generation",
            model="facebook/sam2-hiera-small",
            device=0 if torch.cuda.is_available() else -1,
        )
        result_sam2["loaded"] = True
        mem_after_load = get_gpu_mem()
        print(f"Model loaded (pipeline). GPU memory: {mem_after_load:.2f} GB")

        outputs = seg_pipeline(sample_image, points_per_batch=32)
        print(f"Generated {len(outputs['masks'])} masks via pipeline.")
        result_sam2["inferred"] = True
        result_sam2["gpu_mem_gb"] = mem_after_load - mem_before
        print("Inference success.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    try:
        del model, processor
    except Exception:
        pass
    try:
        del seg_pipeline
    except Exception:
        pass
    torch.cuda.empty_cache()
    gc.collect()

results["SAM 2"] = result_sam2


# ── Section 4: DINOv2 ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Section 4: DINOv2")
print("=" * 60)

result_dinov2 = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}

try:
    torch.cuda.empty_cache()
    mem_before = get_gpu_mem()

    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
    model = AutoModel.from_pretrained("facebook/dinov2-base")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    result_dinov2["loaded"] = True
    mem_after_load = get_gpu_mem()
    print(f"Model loaded. GPU memory: {mem_after_load:.2f} GB")

    inputs = processor(images=sample_image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    cls_embedding = outputs.last_hidden_state[:, 0, :]
    print(f"[CLS] token embedding shape: {cls_embedding.shape}")

    result_dinov2["inferred"] = True
    result_dinov2["gpu_mem_gb"] = mem_after_load - mem_before
    print("Inference success.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    try:
        del model, processor
    except Exception:
        pass
    torch.cuda.empty_cache()
    gc.collect()

results["DINOv2"] = result_dinov2


# ── Section 5: Depth-Anything-V2 ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("Section 5: Depth-Anything-V2")
print("=" * 60)

result_depth = {"loaded": False, "inferred": False, "gpu_mem_gb": 0.0}

try:
    torch.cuda.empty_cache()
    mem_before = get_gpu_mem()

    processor = AutoImageProcessor.from_pretrained(
        "depth-anything/Depth-Anything-V2-Small-hf"
    )
    model = AutoModelForDepthEstimation.from_pretrained(
        "depth-anything/Depth-Anything-V2-Small-hf"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    result_depth["loaded"] = True
    mem_after_load = get_gpu_mem()
    print(f"Model loaded. GPU memory: {mem_after_load:.2f} GB")

    inputs = processor(images=sample_image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    depth_map = outputs.predicted_depth
    print(f"Depth map shape: {depth_map.shape}")

    result_depth["inferred"] = True
    result_depth["gpu_mem_gb"] = mem_after_load - mem_before
    print("Inference success.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    try:
        del model, processor
    except Exception:
        pass
    torch.cuda.empty_cache()
    gc.collect()

results["Depth-Anything-V2"] = result_depth


# ── Summary table ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Model':<30} {'Loaded':<10} {'Inferred':<12} {'GPU Mem (GB)':<15}")
print("-" * 67)
for name, res in results.items():
    print(
        f"{name:<30} {str(res['loaded']):<10} {str(res['inferred']):<12} "
        f"{res['gpu_mem_gb']:<15.2f}"
    )
