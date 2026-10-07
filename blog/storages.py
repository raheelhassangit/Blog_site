import io
import os
import posixpath
import uuid

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify


@deconstructible
class CloudinaryStorage(Storage):
    """Stores images on Cloudinary. The DB keeps '<public_id>.<ext>'; URLs are served as auto format/quality."""

    def _save(self, name, content):
        folder, filename = posixpath.split(name)
        stem = slugify(os.path.splitext(filename)[0])[:40] or "image"
        public_id = posixpath.join(folder, f"{stem}-{uuid.uuid4().hex[:8]}")
        content.seek(0)
        result = cloudinary.uploader.upload(
            io.BytesIO(content.read()), public_id=public_id, resource_type="image", overwrite=False
        )
        return f"{result['public_id']}.{result['format']}"

    def exists(self, name):
        return False  # every upload gets a unique id, so there are never collisions

    def url(self, name):
        public_id = os.path.splitext(name)[0]  # extension omitted so f_auto can pick WebP/AVIF
        url, _ = cloudinary.utils.cloudinary_url(public_id, secure=True, fetch_format="auto", quality="auto")
        return url

    def delete(self, name):
        cloudinary.uploader.destroy(os.path.splitext(name)[0], resource_type="image")