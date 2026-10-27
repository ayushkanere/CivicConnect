import os
import uuid
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageOps
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


class UploadValidationError(Exception):
    """Custom exception raised when upload validation fails."""
    pass


def validate_and_save_photo(file: FileStorage, upload_folder: str) -> str:
    """
    Validates an uploaded photo:
    - Verifies file size <= 2MB
    - Checks filename extension against whitelist
    - Checks MIME type
    - Verifies file integrity using Pillow
    - Strips EXIF and GPS metadata to protect user privacy
    - Generates a cryptographically random, sanitized filename (UUID4)
    - Saves image to target folder and returns the generated filename

    :param file: FileStorage object from form submission
    :param upload_folder: Absolute directory path to store uploads
    :return: Unique filename saved
    :raises UploadValidationError: If validation fails
    """
    if not file or not file.filename:
        raise UploadValidationError("No file selected.")

    # 1. Check extension
    filename = file.filename.lower()
    if "." not in filename:
        raise UploadValidationError("File must have an image extension (.jpg, .jpeg, .png, .webp).")
    
    ext = filename.rsplit(".", 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Invalid file extension '.{ext}'. Allowed types are: JPG, JPEG, PNG, WEBP."
        )

    # 2. Check MIME type if provided
    if file.mimetype and file.mimetype.lower() not in ALLOWED_MIME_TYPES:
        raise UploadValidationError(
            f"Unsupported file format ({file.mimetype}). Allowed types are JPEG, PNG, and WEBP."
        )

    # 3. Read stream and verify size limit
    file_bytes = file.read()
    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise UploadValidationError("Photo exceeds the maximum allowed size of 2 MB.")
    if len(file_bytes) == 0:
        raise UploadValidationError("Uploaded file is empty.")

    # 4. Verify image using Pillow
    try:
        stream = BytesIO(file_bytes)
        img = Image.open(stream)
        img.verify()  # Verifies file integrity
    except Exception as e:
        raise UploadValidationError("Invalid or corrupted image file.") from e

    # Re-open image for processing (verify closes/invalidates the stream)
    try:
        stream.seek(0)
        img = Image.open(stream)
        detected_format = img.format or "JPEG"
        
        # Normalize orientation using EXIF if present before stripping
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Determine target format
        fmt = detected_format if detected_format in ("JPEG", "PNG", "WEBP") else "JPEG"
        save_ext = "png" if fmt == "PNG" else ("webp" if fmt == "WEBP" else "jpg")

        # Generate unique sanitized filename
        secure_filename = f"{uuid.uuid4().hex}.{save_ext}"
        destination_dir = Path(upload_folder)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / secure_filename

        # Strip all EXIF metadata by writing pure image pixel data
        if fmt == "JPEG":
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(destination_path, format="JPEG", quality=85, optimize=True)
        elif fmt == "PNG":
            img.save(destination_path, format="PNG", optimize=True)
        elif fmt == "WEBP":
            img.save(destination_path, format="WEBP", quality=85)
        else:
            img.convert("RGB").save(destination_path, format="JPEG", quality=85)

        return secure_filename

    except Exception as e:
        raise UploadValidationError(f"Failed to process and store image: {str(e)}") from e
