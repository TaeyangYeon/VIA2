"""Synthetic test image generators for VIA2 E2E tests.

All images are generated programmatically using NumPy/OpenCV — no external files.

OK images:  consistent, defect-free patterns (uniform regions, clean geometry)
NG images:  same base pattern with introduced defects (extra/missing blobs, scratches)
Align images: images with clear geometric features for alignment detection
"""
import numpy as np
import cv2


def make_ok_image(h: int = 100, w: int = 100) -> np.ndarray:
    """White BGR image with no blobs — represents a defect-free OK part.

    After any grayscale+threshold pipeline, std < 1 → _count_blobs returns 0.
    """
    return np.full((h, w, 3), 255, dtype=np.uint8)


def make_ng_image(h: int = 100, w: int = 100, n_circles: int = 5) -> np.ndarray:
    """White BGR image with filled black circles — represents a defective NG part.

    After grayscale+threshold, circles are detected as distinct blobs by _count_blobs.
    Circles are spread evenly to avoid merging.
    """
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    radius = max(4, min(h, w) // 20)
    centers = _spread_centers(h, w, n_circles, radius)
    for cx, cy in centers:
        cv2.circle(img, (cx, cy), radius, (0, 0, 0), -1)
    return img


def make_ok_images(count: int = 2, h: int = 100, w: int = 100) -> list[np.ndarray]:
    """Return a list of count OK images."""
    return [make_ok_image(h, w) for _ in range(count)]


def make_ng_images(count: int = 2, h: int = 100, w: int = 100, n_circles: int = 5) -> list[np.ndarray]:
    """Return a list of count NG images, each with n_circles blobs."""
    return [make_ng_image(h, w, n_circles) for _ in range(count)]


def make_align_image(h: int = 120, w: int = 120) -> np.ndarray:
    """BGR image with a dark square in the center — ideal for template matching alignment.

    The central region has sharp edges that allow Template, Edge, or Caliper detection.
    """
    img = np.full((h, w, 3), 200, dtype=np.uint8)
    margin = h // 4
    cv2.rectangle(img, (margin, margin), (w - margin, h - margin), (30, 30, 30), -1)
    return img


def make_align_images(count: int = 3, h: int = 120, w: int = 120) -> list[np.ndarray]:
    """Return a list of count align images."""
    return [make_align_image(h, w) for _ in range(count)]


def make_high_contrast_ok_image(h: int = 100, w: int = 100) -> np.ndarray:
    """Gray image with a single large rectangle — high contrast, single large region.

    Useful when PipelineComposer needs contrast > 0 for block selection.
    """
    img = np.full((h, w, 3), 200, dtype=np.uint8)
    # Large dark region occupying most of the image (1 blob but large → won't interfere)
    cv2.rectangle(img, (10, 10), (w - 10, h - 10), (50, 50, 50), -1)
    return img


# ── internal helpers ──────────────────────────────────────────────────────────

def _spread_centers(
    h: int, w: int, n: int, radius: int
) -> list[tuple[int, int]]:
    """Compute n evenly-spaced circle centers within the image bounds."""
    margin = radius + 5
    if n <= 0:
        return []
    cols = max(1, int(np.ceil(np.sqrt(n))))
    rows = max(1, int(np.ceil(n / cols)))
    step_x = max(1, (w - 2 * margin) // cols)
    step_y = max(1, (h - 2 * margin) // rows)
    centers = []
    for row in range(rows):
        for col in range(cols):
            if len(centers) >= n:
                break
            cx = margin + col * step_x + step_x // 2
            cy = margin + row * step_y + step_y // 2
            cx = min(cx, w - margin - 1)
            cy = min(cy, h - margin - 1)
            centers.append((cx, cy))
    return centers[:n]
