import base64
import os
import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image

from lombik.constants import ALLOWED_IMAGE_EXTENSIONS, COMPRESS_IF_OVER_BYTES


def save_image(
    image_bytes: bytes,
    upload_folder: str,
    extension: str,
    *,
    compress: bool = True,
) -> str:
    """Save image bytes and return the full file path."""

    extension = extension.lower().lstrip(".")

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image type: {extension}")

    if not image_bytes:
        raise ValueError("Image is empty")

    final_bytes = image_bytes

    if compress and len(image_bytes) > COMPRESS_IF_OVER_BYTES:
        final_bytes = compress_image_bytes(image_bytes)
        extension = "jpg"

    Path(upload_folder).mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(upload_folder, file_name)

    with open(file_path, "wb") as f:
        f.write(final_bytes)

    return file_path


def save_base64_image(
    base64_string: str,
    upload_folder: str,
) -> str:
    """Decode and save a Base64 image."""

    if "," not in base64_string:
        raise ValueError("Invalid base64 image format")

    header, data = base64_string.split(",", 1)

    try:
        extension = header.split("/")[1].split(";")[0].lower()
    except (IndexError, AttributeError):
        raise ValueError("Invalid image MIME type")

    try:
        image_bytes = base64.b64decode(data, validate=True)
    except ValueError:
        raise ValueError("Invalid base64 data")

    return save_image(
        image_bytes,
        upload_folder,
        extension,
    )


def save_uploaded_image(
    file,
    upload_folder: str,
) -> str:
    """Save an uploaded image."""

    if not file or not file.filename:
        raise ValueError("No file selected")

    if "." not in file.filename:
        raise ValueError("File has no extension")

    extension = file.filename.rsplit(".", 1)[1].lower()

    image_bytes = file.read()

    return save_image(
        image_bytes,
        upload_folder,
        extension,
    )


def compress_image_bytes(
    raw_bytes: bytes,
    max_width: int = 1920,
    max_height: int = 1920,
    jpeg_quality: int = 85,
) -> bytes:
    """Resize and convert an image to optimized JPEG."""

    try:
        img = Image.open(BytesIO(raw_bytes))

        img.thumbnail(
            (max_width, max_height),
            Image.Resampling.LANCZOS,
        )

        if img.mode != "RGB":
            img = img.convert("RGB")

        output = BytesIO()

        img.save(
            output,
            format="JPEG",
            quality=jpeg_quality,
            optimize=True,
        )

        return output.getvalue()

    except Exception:
        return raw_bytes