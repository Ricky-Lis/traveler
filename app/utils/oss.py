import uuid
from io import BytesIO

import oss2
from PIL import Image

from app.config import get_settings

_bucket: oss2.Bucket | None = None


def _get_bucket() -> oss2.Bucket:
    global _bucket
    if _bucket is None:
        settings = get_settings()
        auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        _bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
    return _bucket


def build_url(key: str) -> str:
    settings = get_settings()
    if settings.OSS_CDN_DOMAIN:
        return f"https://{settings.OSS_CDN_DOMAIN}/{key}"
    return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{key}"


def upload_bytes(key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    bucket = _get_bucket()
    bucket.put_object(key, data, headers={"Content-Type": content_type})
    return build_url(key)


def upload_image(folder: str, data: bytes, content_type: str = "image/jpeg") -> str:
    ext = "jpg"
    if "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"
    key = f"{folder}/{uuid.uuid4().hex}.{ext}"
    return upload_bytes(key, data, content_type)


def generate_thumbnail(data: bytes, max_size: tuple[int, int] = (400, 400)) -> bytes:
    img = Image.open(BytesIO(data))
    img.thumbnail(max_size, Image.LANCZOS)
    buf = BytesIO()
    fmt = img.format or "JPEG"
    img.save(buf, format=fmt, quality=85)
    return buf.getvalue()


def delete_object(key: str) -> None:
    bucket = _get_bucket()
    bucket.delete_object(key)


def url_to_key(url: str) -> str | None:
    """从完整 URL 提取 OSS key"""
    settings = get_settings()
    for prefix in (
        f"https://{settings.OSS_CDN_DOMAIN}/",
        f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/",
    ):
        if prefix and url.startswith(prefix):
            return url[len(prefix):]
    return None
