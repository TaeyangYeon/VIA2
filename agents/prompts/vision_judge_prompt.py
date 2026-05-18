"""Prompt builder for VisionJudgeAgent — evaluation guidance for Qwen2.5-VL."""


def build_vision_judge_prompt(purpose: str, directive: str = "") -> str:
    """Build the text prompt sent alongside the two images to the Colab endpoint.

    Instructs the VLM to compare original vs processed image, score three
    quality dimensions, list problems, and suggest the next improvement.
    Returns a single prompt string; directive is appended if non-empty.
    """
    prompt = f"""\
You are a machine vision quality evaluator. Two images are provided:
- Image 1: the ORIGINAL image (before processing)
- Image 2: the PROCESSED image (after processing)

Inspection purpose: {purpose}

Evaluate how well the processing serves the inspection purpose by scoring three dimensions:

1. visibility_score (0.0-1.0): How clearly can defects or target features be seen in the processed image?
   0.0 = features completely invisible, 1.0 = features perfectly clear

2. separability_score (0.0-1.0): How well can the target be distinguished from the background?
   0.0 = no contrast, 1.0 = perfect separation

3. measurability_score (0.0-1.0): How precisely can measurements be taken on the processed image?
   0.0 = impossible to measure, 1.0 = pixel-accurate measurement possible

Also identify:
- problems: a list of specific issues with the current processing (empty list if none)
- next_suggestion: one concrete recommendation to improve the processing for this purpose

Output ONLY valid JSON with this exact schema — no markdown fences, no explanation:
{{
  "visibility_score": <float 0.0-1.0>,
  "separability_score": <float 0.0-1.0>,
  "measurability_score": <float 0.0-1.0>,
  "problems": [<string>, ...],
  "next_suggestion": "<string>"
}}"""

    if directive:
        prompt += f"\n\nAdditional evaluation guidance: {directive}"

    return prompt
