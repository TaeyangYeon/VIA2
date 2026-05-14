# VIA2 모델 설정 가이드

> **Note**: 이 문서의 모든 SOTA 비전 모델은 Intel Mac 로컬에서 실행 불가합니다.
> Google Colab T4 GPU (16GB VRAM)에서 실행하고, FastAPI Remote Adapter를 통해 연동합니다.

---

## 목차

1. [Colab 노트북 설정 가이드](#1-colab-노트북-설정-가이드)
2. [모델 동적 로딩 전략](#2-모델-동적-로딩-전략)
3. [Florence-2](#3-florence-2)
4. [Grounding DINO](#4-grounding-dino)
5. [SAM 2](#5-sam-2)
6. [DINOv2](#6-dinov2)
7. [Depth-Anything-V2](#7-depth-anything-v2)
8. [Remote Adapter 연동 패턴](#8-remote-adapter-연동-패턴)
9. [검증 스크립트 실행 방법](#9-검증-스크립트-실행-방법)

---

## 1. Colab 노트북 설정 가이드

VIA2의 SOTA 비전 모델은 모두 Google Colab T4 GPU 환경에서 실행됩니다.
아래 절차를 따라 Colab 환경을 준비하세요.

### 런타임 설정

1. Google Colab (https://colab.research.google.com) 에서 새 노트북을 엽니다.
2. 상단 메뉴에서 **런타임 → 런타임 유형 변경** 을 클릭합니다.
3. **하드웨어 가속기** 드롭다운에서 **T4 GPU** 를 선택합니다.
4. **저장** 버튼을 클릭해 설정을 적용합니다.

### Google Drive 마운트 (선택사항)

모델 가중치를 Drive에 캐시하면 재시작 시 재다운로드를 줄일 수 있습니다.

```python
from google.colab import drive
drive.mount('/content/drive')
```

### GPU 확인

런타임 연결 후 다음 명령어로 T4 GPU 할당을 확인합니다.

```bash
!nvidia-smi
```

출력 예시에서 `Tesla T4` 와 `16160MiB` (약 16GB) VRAM이 표시되면 정상입니다.

### 세션 유지 주의사항

- Colab 무료 티어는 **90분 idle** 상태가 지속되면 런타임이 자동 종료됩니다.
- 런타임 종료 시 로드된 모델, 환경 변수, 설치된 패키지가 모두 초기화됩니다.
- 장시간 추론이 필요한 경우 Colab Pro/Pro+를 사용하거나, 주기적으로 셀을 실행해 idle 타임아웃을 방지하세요.
- `ngrok` 또는 `localtunnel` 을 사용해 Colab 노트북을 FastAPI Remote Adapter의 엔드포인트로 노출할 때는, 런타임 재시작 후 URL이 변경되므로 FastAPI 서버의 `COLAB_BASE_URL` 환경 변수를 함께 업데이트해야 합니다.

---

## 2. 모델 동적 로딩 전략

### T4 VRAM 16GB 제약

T4 GPU의 VRAM은 16GB로, 5개 모델을 동시에 로드하는 것은 불가능합니다.
VIA2는 **순차 로드/언로드 전략**을 사용합니다: 한 번에 하나의 모델만 GPU에 올리고, 추론이 끝나면 즉시 메모리를 해제합니다.

### 메모리 해제 패턴

추론 완료 후 반드시 아래 패턴으로 메모리를 해제하세요.

```python
import gc
import torch

# 모델 사용 완료 후
del model
del processor  # processor/feature_extractor가 있을 경우
torch.cuda.empty_cache()
gc.collect()
```

### 예상 메모리 사용량

아래 수치는 추정값이며, Colab T4 환경 검증 후 실측값으로 업데이트될 예정입니다.

| 모델 | 예상 VRAM | 비고 |
|------|-----------|------|
| Florence-2-base | ~3GB | float16 |
| Grounding DINO-base | ~1GB | float16 |
| SAM 2 hiera-small | ~2GB | |
| DINOv2-base | ~0.5GB | |
| Depth-Anything-V2-Small | ~1GB | |

---

## 3. Florence-2

### 개요

- **HuggingFace**: `microsoft/Florence-2-base`
- **VIA2 역할**: Material Agent — 소재 분류 및 이미지 캡셔닝 (Step 16)

### Colab 설치

```bash
!pip install transformers accelerate timm einops
```

### 코드 스니펫

```python
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-base",
    torch_dtype=torch.float16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base")

# 캡셔닝 추론
inputs = processor(text="<CAPTION>", images=image, return_tensors="pt").to("cuda")
output = model.generate(**inputs, max_new_tokens=50)
result = processor.decode(output[0], skip_special_tokens=True)
```

### 예상 GPU 메모리

~3GB (T4 float16 기준, Colab 검증 후 업데이트 예정)

### FastAPI 연동

Remote Adapter를 통해 아래 엔드포인트로 호출합니다.

- **엔드포인트**: `POST /colab/florence2/caption`
- **요청 바디**:
  ```json
  {
    "image_base64": "...",
    "task": "<CAPTION>"
  }
  ```

---

## 4. Grounding DINO

### 개요

- **HuggingFace**: `IDEA-Research/grounding-dino-base`
- **VIA2 역할**: ROI Agent — 텍스트 프롬프트로 결함/부품 영역 검출 (Step 17)

### Colab 설치

```bash
!pip install transformers
```

### 코드 스니펫

```python
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
import torch

processor = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-base")
model = AutoModelForZeroShotObjectDetection.from_pretrained(
    "IDEA-Research/grounding-dino-base",
    torch_dtype=torch.float16
).to("cuda")

# 텍스트 프롬프트 기반 객체 검출
text_prompt = "defect. crack. hole."
inputs = processor(images=image, text=text_prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model(**inputs)

results = processor.post_process_grounded_object_detection(
    outputs,
    inputs.input_ids,
    box_threshold=0.4,
    text_threshold=0.3,
    target_sizes=[image.size[::-1]]
)
```

### 예상 GPU 메모리

~1GB (T4 float16 기준, Colab 검증 후 업데이트 예정)

### FastAPI 연동

- **엔드포인트**: `POST /colab/grounding_dino/detect`
- **요청 바디**:
  ```json
  {
    "image_base64": "...",
    "text_prompt": "defect. crack. hole."
  }
  ```

---

## 5. SAM 2

### 개요

- **HuggingFace**: `facebook/sam2-hiera-small`
- **VIA2 역할**: ROI Agent — 결함 영역 정밀 세그멘테이션 (Step 17)

### Colab 설치

```bash
!pip install transformers sam2
```

### 코드 스니펫

```python
from transformers import AutoModelForUniversalSegmentation, AutoProcessor
import torch

# transformers 지원 버전을 우선 시도
try:
    processor = AutoProcessor.from_pretrained("facebook/sam2-hiera-small")
    model = AutoModelForUniversalSegmentation.from_pretrained(
        "facebook/sam2-hiera-small"
    ).to("cuda")

    inputs = processor(images=image, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = model(**inputs)
    masks = processor.post_process_semantic_segmentation(outputs)

except Exception:
    # pipeline fallback
    from transformers import pipeline
    pipe = pipeline(
        "mask-generation",
        model="facebook/sam2-hiera-small",
        device="cuda"
    )
    result = pipe(image, points_per_batch=64)
    masks = result["masks"]
```

### 예상 GPU 메모리

~2GB (Colab 검증 후 업데이트 예정)

### FastAPI 연동

- **엔드포인트**: `POST /colab/sam2/segment`
- **요청 바디**:
  ```json
  {
    "image_base64": "...",
    "point": [x, y]
  }
  ```

---

## 6. DINOv2

### 개요

- **HuggingFace**: `facebook/dinov2-base`
- **VIA2 역할**: Material Agent + Decision Agent — 특징 벡터 기반 소재 유사도 비교 (Step 16, 32)

### Colab 설치

```bash
!pip install transformers
```

### 코드 스니펫

```python
from transformers import AutoImageProcessor, AutoModel
import torch

processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
model = AutoModel.from_pretrained(
    "facebook/dinov2-base",
    torch_dtype=torch.float16
).to("cuda")

# [CLS] 토큰 특징 벡터 추출
inputs = processor(images=image, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model(**inputs)

# last_hidden_state[:, 0] = [CLS] token embedding
cls_embedding = outputs.last_hidden_state[:, 0, :]  # shape: (1, 768)
```

### 예상 GPU 메모리

~0.5GB (T4 float16 기준, Colab 검증 후 업데이트 예정)

### FastAPI 연동

- **엔드포인트**: `POST /colab/dinov2/embed`
- **요청 바디**:
  ```json
  {
    "image_base64": "..."
  }
  ```

---

## 7. Depth-Anything-V2

### 개요

- **HuggingFace**: `depth-anything/Depth-Anything-V2-Small-hf`
- **VIA2 역할**: Depth Agent — 소재 표면 깊이 맵 추정 (Step 15)

### Colab 설치

```bash
!pip install transformers
```

### 코드 스니펫

```python
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
import torch
import numpy as np

processor = AutoImageProcessor.from_pretrained(
    "depth-anything/Depth-Anything-V2-Small-hf"
)
model = AutoModelForDepthEstimation.from_pretrained(
    "depth-anything/Depth-Anything-V2-Small-hf",
    torch_dtype=torch.float16
).to("cuda")

# 깊이 맵 추정
inputs = processor(images=image, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model(**inputs)

# 원본 이미지 크기로 보간
predicted_depth = outputs.predicted_depth  # shape: (1, H, W)
depth_map = torch.nn.functional.interpolate(
    predicted_depth.unsqueeze(1),
    size=image.size[::-1],
    mode="bicubic",
    align_corners=False
).squeeze().cpu().numpy()

# 0-255 정규화
depth_normalized = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min()) * 255
depth_uint8 = depth_normalized.astype(np.uint8)
```

### 예상 GPU 메모리

~1GB (T4 float16 기준, Colab 검증 후 업데이트 예정)

### FastAPI 연동

- **엔드포인트**: `POST /colab/depth/estimate`
- **요청 바디**:
  ```json
  {
    "image_base64": "..."
  }
  ```

---

## 8. Remote Adapter 연동 패턴

FastAPI 백엔드는 Colab에서 실행 중인 모델 서버를 **Remote Adapter** 패턴으로 HTTP 호출합니다.
Intel Mac 로컬에서는 모델을 직접 실행하지 않으며, 모든 SOTA 비전 모델 호출은 이 어댑터를 통해 이루어집니다.

```python
# backend/adapters/remote_adapter.py (예시)
import httpx, base64

async def call_colab_model(endpoint: str, image_bytes: bytes, **kwargs):
    image_b64 = base64.b64encode(image_bytes).decode()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{COLAB_BASE_URL}{endpoint}",
            json={"image_base64": image_b64, **kwargs}
        )
    return resp.json()
```

### 사용 예시

```python
# Florence-2 캡셔닝 호출
result = await call_colab_model(
    endpoint="/colab/florence2/caption",
    image_bytes=raw_image_bytes,
    task="<CAPTION>"
)

# Grounding DINO 검출 호출
result = await call_colab_model(
    endpoint="/colab/grounding_dino/detect",
    image_bytes=raw_image_bytes,
    text_prompt="defect. crack. hole."
)
```

### 환경 변수

`COLAB_BASE_URL` 은 FastAPI 서버 환경 변수로 관리합니다.
Colab 런타임 재시작 시 ngrok/localtunnel URL이 변경되면 이 값을 업데이트해야 합니다.

```bash
# .env 또는 환경 변수 설정 예시
COLAB_BASE_URL=https://xxxx-xx-xx-xxx-xx.ngrok-free.app
```

---

## 9. 검증 스크립트 실행 방법

VIA2는 `scripts/verify_vision_models.py` 스크립트를 통해 5개 모델의 로드 및 추론을 검증합니다.

### Colab에서 실행

1. Colab 노트북에서 VIA2 리포지토리를 클론하거나, 스크립트 파일을 업로드합니다.

   ```bash
   !git clone https://github.com/<your-org>/VIA2.git
   %cd VIA2
   ```

2. 필요한 패키지를 설치합니다.

   ```bash
   !pip install transformers accelerate timm einops sam2 httpx
   ```

3. 검증 스크립트를 실행합니다.

   ```bash
   !python scripts/verify_vision_models.py
   ```

4. 각 모델의 로드 성공 여부, 추론 결과, 실제 VRAM 사용량이 출력됩니다.
   출력 결과를 바탕으로 [섹션 2](#2-모델-동적-로딩-전략)의 예상 메모리 사용량 표를 업데이트하세요.

### 로컬(Intel Mac)에서 부분 검증

SOTA 비전 모델은 로컬에서 실행할 수 없지만, Remote Adapter의 HTTP 호출 경로는 로컬에서 검증 가능합니다.
Colab이 실행 중인 상태에서 `COLAB_BASE_URL` 을 설정한 뒤 FastAPI 서버를 통해 엔드포인트를 호출하세요.
