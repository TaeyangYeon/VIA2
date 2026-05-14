import tempfile
import os


def test_opencv_import():
    import cv2
    assert hasattr(cv2, "__version__")
    assert cv2.__version__ != ""


def test_numpy_import():
    import numpy
    assert hasattr(numpy, "__version__")
    assert numpy.__version__ != ""


def test_torch_import():
    import torch
    assert hasattr(torch, "__version__")
    assert torch.__version__ != ""


def test_opencv_image_operations():
    import cv2
    import numpy as np

    original = np.zeros((100, 100, 3), dtype=np.uint8)
    original[10:50, 10:50] = [255, 128, 0]

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name

    try:
        cv2.imwrite(path, original)
        loaded = cv2.imread(path)
        assert loaded is not None
        assert loaded.shape == original.shape
    finally:
        os.unlink(path)


def test_torch_tensor_operations():
    import torch

    a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    b = torch.tensor([[1.0, 0.0], [0.0, 1.0]])

    assert (a + b).shape == (2, 2)
    assert torch.allclose(torch.matmul(a, b), a)
    assert a.device.type == "cpu"


def test_opencv_basic_processing():
    import cv2
    import numpy as np

    img = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    assert gray.shape == (200, 200)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    assert blurred.shape == gray.shape

    edges = cv2.Canny(blurred, 50, 150)
    assert edges.shape == gray.shape
    assert edges.dtype == np.uint8


def test_numpy_opencv_interop():
    import cv2
    import numpy as np

    arr = np.ones((64, 64, 3), dtype=np.uint8) * 127
    resized = cv2.resize(arr, (32, 32))
    assert isinstance(resized, np.ndarray)
    assert resized.shape == (32, 32, 3)

    channel = arr[:, :, 0]
    assert channel.shape == (64, 64)
    assert np.all(channel == 127)
