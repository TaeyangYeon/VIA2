import pytest
import httpx
from pathlib import Path
from backend.main import app


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_image_store(tmp_path):
    from backend.services import image_store
    image_store.configure_upload_dir(tmp_path / "uploads")
    image_store.clear_all()
    yield
    image_store.clear_all()


# ── ImageValidator: filename validation ──────────────────────────────────────

def test_validate_ok_1_png_returns_valid_with_label_ok_index_1():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1.png")
    assert result.is_valid
    assert result.label == "OK"
    assert result.index == 1


def test_validate_ok_2_jpg_returns_valid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_2.jpg")
    assert result.is_valid
    assert result.label == "OK"
    assert result.index == 2


def test_validate_ng_1_jpeg_returns_valid_with_label_ng():
    from backend.services.image_validator import validate_filename
    result = validate_filename("NG_1.jpeg")
    assert result.is_valid
    assert result.label == "NG"
    assert result.index == 1


def test_validate_lowercase_prefix_normalized_to_uppercase():
    from backend.services.image_validator import validate_filename
    result = validate_filename("ok_2.JPG")
    assert result.is_valid
    assert result.label == "OK"


def test_validate_lowercase_ng_with_large_index():
    from backend.services.image_validator import validate_filename
    result = validate_filename("ng_10.TIFF")
    assert result.is_valid
    assert result.label == "NG"
    assert result.index == 10


def test_validate_uppercase_extension_is_valid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1.PNG")
    assert result.is_valid


def test_validate_bmp_extension_is_valid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1.bmp")
    assert result.is_valid


def test_validate_tiff_extension_with_index():
    from backend.services.image_validator import validate_filename
    result = validate_filename("NG_5.tiff")
    assert result.is_valid
    assert result.index == 5


def test_validate_multi_digit_index_is_valid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_100.png")
    assert result.is_valid
    assert result.index == 100


def test_validate_arbitrary_name_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("test.png")
    assert not result.is_valid


def test_validate_ok_without_underscore_number_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK.png")
    assert not result.is_valid


def test_validate_zero_index_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_0.png")
    assert not result.is_valid


def test_validate_negative_index_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_-1.png")
    assert not result.is_valid


def test_validate_empty_number_after_underscore_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("NG_.png")
    assert not result.is_valid


def test_validate_gif_extension_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1.gif")
    assert not result.is_valid


def test_validate_filename_without_extension_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1")
    assert not result.is_valid


def test_validate_double_extension_is_invalid():
    from backend.services.image_validator import validate_filename
    result = validate_filename("OK_1.png.exe")
    assert not result.is_valid


# ── ImageValidator: content type validation ──────────────────────────────────

def test_content_type_image_png_is_valid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("image/png") is True


def test_content_type_image_jpeg_is_valid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("image/jpeg") is True


def test_content_type_image_bmp_is_valid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("image/bmp") is True


def test_content_type_image_tiff_is_valid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("image/tiff") is True


def test_content_type_application_pdf_is_invalid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("application/pdf") is False


def test_content_type_text_plain_is_invalid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type("text/plain") is False


def test_content_type_none_is_invalid():
    from backend.services.image_validator import validate_content_type
    assert validate_content_type(None) is False


# ── ImageStore: CRUD ─────────────────────────────────────────────────────────

def test_image_store_add_returns_metadata_with_all_fields():
    from backend.services import image_store
    metadata = image_store.add(
        file_content=b"fake_image",
        filename="OK_1.png",
        label="OK",
        index=1,
    )
    assert metadata.id
    assert metadata.original_filename == "OK_1.png"
    assert metadata.label == "OK"
    assert metadata.index == 1
    assert metadata.file_size == len(b"fake_image")
    assert metadata.upload_timestamp is not None
    assert metadata.file_path


def test_image_store_file_is_written_to_disk(tmp_path):
    from backend.services import image_store
    metadata = image_store.add(b"fake_image", "OK_1.png", "OK", 1)
    assert Path(metadata.file_path).exists()


def test_image_store_get_by_id_returns_correct_metadata():
    from backend.services import image_store
    added = image_store.add(b"img", "OK_1.png", "OK", 1)
    fetched = image_store.get_by_id(added.id)
    assert fetched is not None
    assert fetched.id == added.id


def test_image_store_get_by_id_returns_none_for_unknown():
    from backend.services import image_store
    assert image_store.get_by_id("does-not-exist") is None


def test_image_store_get_all_returns_all_uploaded_images():
    from backend.services import image_store
    image_store.add(b"img", "OK_1.png", "OK", 1)
    image_store.add(b"img", "NG_1.png", "NG", 1)
    image_store.add(b"img", "OK_2.png", "OK", 2)
    assert len(image_store.get_all()) == 3


def test_image_store_delete_removes_metadata():
    from backend.services import image_store
    metadata = image_store.add(b"img", "OK_1.png", "OK", 1)
    result = image_store.delete_by_id(metadata.id)
    assert result is True
    assert image_store.get_by_id(metadata.id) is None


def test_image_store_delete_removes_file_from_disk(tmp_path):
    from backend.services import image_store
    metadata = image_store.add(b"img", "OK_1.png", "OK", 1)
    file_path = Path(metadata.file_path)
    assert file_path.exists()
    image_store.delete_by_id(metadata.id)
    assert not file_path.exists()


def test_image_store_delete_returns_false_for_unknown_id():
    from backend.services import image_store
    assert image_store.delete_by_id("no-such-id") is False


def test_image_store_clear_all_empties_store():
    from backend.services import image_store
    image_store.add(b"img", "OK_1.png", "OK", 1)
    image_store.add(b"img", "NG_1.png", "NG", 1)
    image_store.clear_all()
    assert image_store.get_all() == []


# ── ImageStore: classification logic ─────────────────────────────────────────

def test_ok1_is_classified_as_analysis_group():
    from backend.services import image_store
    metadata = image_store.add(b"img", "OK_1.png", "OK", 1)
    assert metadata.group == "analysis"


def test_ng1_is_classified_as_analysis_group():
    from backend.services import image_store
    metadata = image_store.add(b"img", "NG_1.png", "NG", 1)
    assert metadata.group == "analysis"


def test_ok2_is_classified_as_test_group():
    from backend.services import image_store
    metadata = image_store.add(b"img", "OK_2.png", "OK", 2)
    assert metadata.group == "test"


def test_ng2_is_classified_as_test_group():
    from backend.services import image_store
    metadata = image_store.add(b"img", "NG_2.png", "NG", 2)
    assert metadata.group == "test"


def test_ok10_is_classified_as_test_group():
    from backend.services import image_store
    metadata = image_store.add(b"img", "OK_10.png", "OK", 10)
    assert metadata.group == "test"


def test_get_by_group_analysis_contains_exactly_ok1_and_ng1():
    from backend.services import image_store
    image_store.add(b"img", "OK_1.png", "OK", 1)
    image_store.add(b"img", "NG_1.png", "NG", 1)
    image_store.add(b"img", "OK_2.png", "OK", 2)
    analysis = image_store.get_by_group("analysis")
    assert len(analysis) == 2
    assert {(m.label, m.index) for m in analysis} == {("OK", 1), ("NG", 1)}


def test_get_by_group_test_excludes_ok1_and_ng1():
    from backend.services import image_store
    image_store.add(b"img", "OK_1.png", "OK", 1)
    image_store.add(b"img", "OK_2.png", "OK", 2)
    image_store.add(b"img", "NG_2.png", "NG", 2)
    test_group = image_store.get_by_group("test")
    assert len(test_group) == 2
    assert {(m.label, m.index) for m in test_group} == {("OK", 2), ("NG", 2)}


def test_ok1_overwrite_keeps_only_one_ok1():
    from backend.services import image_store
    first = image_store.add(b"first_content", "OK_1.png", "OK", 1)
    second = image_store.add(b"second_content", "OK_1.png", "OK", 1)
    ok1_images = [m for m in image_store.get_all() if m.label == "OK" and m.index == 1]
    assert len(ok1_images) == 1
    assert ok1_images[0].id == second.id


def test_ok1_overwrite_deletes_old_file_from_disk(tmp_path):
    from backend.services import image_store
    first = image_store.add(b"first_content", "OK_1.png", "OK", 1)
    old_path = Path(first.file_path)
    image_store.add(b"second_content", "OK_1.png", "OK", 1)
    assert not old_path.exists()


# ── API endpoint tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_valid_image_returns_201():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"fake_image", "image/png")},
        )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_returns_metadata_with_correct_fields():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"fake_image", "image/png")},
        )
    data = response.json()
    assert data["label"] == "OK"
    assert data["index"] == 1
    assert data["group"] == "analysis"
    assert data["original_filename"] == "OK_1.png"
    assert "id" in data
    assert "file_size" in data
    assert "upload_timestamp" in data
    assert "file_path" in data


@pytest.mark.asyncio
async def test_upload_invalid_filename_returns_422():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("invalid_name.png", b"fake_image", "image/png")},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_invalid_content_type_returns_422():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"not_an_image", "application/octet-stream")},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_all_images_returns_200_with_list():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/images")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_all_images_returns_uploaded_images():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        await client.post(
            "/api/images/upload",
            files={"file": ("NG_1.png", b"img", "image/png")},
        )
        response = await client.get("/api/images")
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_images_by_analysis_group_returns_only_ok1_ng1():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_2.png", b"img", "image/png")},
        )
        response = await client.get("/api/images?group=analysis")
    images = response.json()
    assert len(images) == 1
    assert images[0]["label"] == "OK"
    assert images[0]["index"] == 1


@pytest.mark.asyncio
async def test_list_images_by_test_group_excludes_index1():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_2.png", b"img", "image/png")},
        )
        await client.post(
            "/api/images/upload",
            files={"file": ("NG_2.png", b"img", "image/png")},
        )
        response = await client.get("/api/images?group=test")
    images = response.json()
    assert len(images) == 2
    assert all(img["index"] != 1 for img in images)


@pytest.mark.asyncio
async def test_get_image_by_id_returns_200_with_metadata():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        upload = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        image_id = upload.json()["id"]
        response = await client.get(f"/api/images/{image_id}")
    assert response.status_code == 200
    assert response.json()["id"] == image_id


@pytest.mark.asyncio
async def test_get_image_by_unknown_id_returns_404():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/images/no-such-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_image_by_id_returns_200():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        upload = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        image_id = upload.json()["id"]
        response = await client.delete(f"/api/images/{image_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_image_by_id_removes_from_list():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        upload = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        image_id = upload.json()["id"]
        await client.delete(f"/api/images/{image_id}")
        response = await client.get("/api/images")
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_image_by_unknown_id_returns_404():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/images/no-such-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_clear_all_images_returns_200():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        response = await client.delete("/api/images")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_clear_all_images_empties_the_list():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"img", "image/png")},
        )
        await client.post(
            "/api/images/upload",
            files={"file": ("NG_1.png", b"img", "image/png")},
        )
        await client.delete("/api/images")
        response = await client.get("/api/images")
    assert response.json() == []


@pytest.mark.asyncio
async def test_upload_ok1_twice_overwrites_first_upload():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"first_content", "image/png")},
        )
        second = await client.post(
            "/api/images/upload",
            files={"file": ("OK_1.png", b"second_content", "image/png")},
        )
        response = await client.get("/api/images")
    images = response.json()
    ok1_images = [img for img in images if img["label"] == "OK" and img["index"] == 1]
    assert len(ok1_images) == 1
    assert ok1_images[0]["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_upload_ng1_is_in_analysis_group():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("NG_1.png", b"img", "image/png")},
        )
    assert response.json()["group"] == "analysis"


@pytest.mark.asyncio
async def test_upload_ok2_is_in_test_group():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/images/upload",
            files={"file": ("OK_2.png", b"img", "image/png")},
        )
    assert response.json()["group"] == "test"
