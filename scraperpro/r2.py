"""Cloudflare R2 upload (S3-compatible) for re-hosting Oakley images.

Config comes from `.env` (see .env.example). Requires `boto3` and `Pillow`.

Typical use is via tools/rehost_images.py, which:
  1. reads a scraped CSV,
  2. for each image row finds the matching downloaded PNG
     (output/<brand>_images/<handle>/NN.png from OakleySIScraper.download_images),
  3. converts PNG -> flattened JPEG,
  4. uploads to R2 at <prefix>/<handle>/NN.jpg,
  5. rewrites the row's Image Src / Variant Image to the public bucket URL.
"""
from __future__ import annotations

import io
import os


def load_env(path: str = ".env") -> dict:
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k.startswith("R2_")})
    return env


class R2:
    def __init__(self, env: dict | None = None) -> None:
        import boto3  # lazy

        e = env or load_env()
        missing = [k for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID",
                               "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_BASE")
                   if not e.get(k)]
        if missing:
            raise RuntimeError(f".env missing: {', '.join(missing)}")
        self.bucket = e["R2_BUCKET"]
        self.public_base = e["R2_PUBLIC_BASE"].rstrip("/")
        self._s3 = boto3.client(
            "s3",
            endpoint_url=e["R2_ENDPOINT"],
            aws_access_key_id=e["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=e["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )

    def put_jpeg(self, key: str, data: bytes) -> str:
        """Upload bytes as image/jpeg at `key`; return the public URL."""
        self._s3.put_object(Bucket=self.bucket, Key=key, Body=data,
                            ContentType="image/jpeg", CacheControl="public, max-age=31536000")
        return f"{self.public_base}/{key}"

    def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:  # noqa: BLE001
            return False

    def delete_prefix(self, prefix: str) -> int:
        """Delete every object under `prefix` (teardown after the client's import)."""
        paginator = self._s3.get_paginator("list_objects_v2")
        n = 0
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if objs:
                self._s3.delete_objects(Bucket=self.bucket, Delete={"Objects": objs})
                n += len(objs)
        return n


def png_to_jpeg(png_bytes: bytes, max_px: int = 1600, quality: int = 85) -> bytes:
    """Flatten transparency onto white, downscale, encode JPEG."""
    from PIL import Image

    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if max(im.size) > max_px:
        im.thumbnail((max_px, max_px), Image.LANCZOS)
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    out = io.BytesIO()
    bg.save(out, "JPEG", quality=quality, optimize=True)
    return out.getvalue()
