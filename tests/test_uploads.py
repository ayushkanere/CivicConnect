import io
import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage
from app.services.uploads import validate_and_save_photo, UploadValidationError
from app.models import Report
from app.services.reports import create_report


def create_test_image(format="JPEG", size=(100, 100), color="blue"):
    """Helper to generate an in-memory test image."""
    img_byte_arr = io.BytesIO()
    image = Image.new("RGB", size, color=color)
    image.save(img_byte_arr, format=format)
    img_byte_arr.seek(0)
    return img_byte_arr


def test_valid_image_upload(app):
    """Verifies that a valid image is verified, sanitized, and saved with a randomized filename."""
    img_bytes = create_test_image(format="PNG")
    file_storage = FileStorage(
        stream=img_bytes,
        filename="test_pothole.png",
        content_type="image/png"
    )

    saved_filename = validate_and_save_photo(file_storage, app.config["UPLOAD_FOLDER"])
    assert saved_filename is not None
    assert saved_filename.endswith(".png")
    assert saved_filename != "test_pothole.png"  # Filename was randomized


def test_oversized_image_rejected(app):
    """Verifies that images exceeding 2 MB are rejected."""
    # Create fake oversized byte stream (> 2MB)
    oversized_data = b"0" * (2 * 1024 * 1024 + 500)
    file_storage = FileStorage(
        stream=io.BytesIO(oversized_data),
        filename="huge_image.jpg",
        content_type="image/jpeg"
    )

    with pytest.raises(UploadValidationError, match="exceeds the maximum allowed size of 2 MB"):
        validate_and_save_photo(file_storage, app.config["UPLOAD_FOLDER"])


def test_corrupted_image_rejected(app):
    """Verifies that corrupted files or spoofed non-image files are rejected by Pillow."""
    bad_bytes = io.BytesIO(b"This is not a real image file content.")
    file_storage = FileStorage(
        stream=bad_bytes,
        filename="fake_image.jpg",
        content_type="image/jpeg"
    )

    with pytest.raises(UploadValidationError, match="Invalid or corrupted image file"):
        validate_and_save_photo(file_storage, app.config["UPLOAD_FOLDER"])


def test_invalid_extension_rejected(app):
    """Verifies that non-whitelisted extensions are rejected."""
    img_bytes = create_test_image()
    file_storage = FileStorage(
        stream=img_bytes,
        filename="exploit.exe",
        content_type="application/octet-stream"
    )

    with pytest.raises(UploadValidationError, match="Invalid file extension"):
        validate_and_save_photo(file_storage, app.config["UPLOAD_FOLDER"])


def test_photo_privacy_unapproved(client, db_session):
    """Verifies that uploaded photos are NOT served publicly until approved by an administrator."""
    report = create_report("Garbage/Waste", "Report with photo pending approval.", "Campus Block C")
    report.photo_path = "sample_test_photo.jpg"
    report.is_public = True
    report.photo_approved = False  # Not approved!
    db_session.commit()

    # Public user attempts to access file directly
    response = client.get(f"/uploads/{report.photo_path}")
    assert response.status_code == 403  # Forbidden
