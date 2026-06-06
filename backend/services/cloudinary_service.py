"""Cloudinary upload helpers for exercise videos and thumbnails."""

import cloudinary
import cloudinary.uploader
from settings import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_video(local_path: str, folder: str = "rehab/videos") -> str:
    """Upload a video file to Cloudinary. Returns the secure URL."""
    result = cloudinary.uploader.upload(
        local_path,
        resource_type="video",
        folder=folder,
        overwrite=False,
    )
    return result["secure_url"]


def upload_image(local_path: str, folder: str = "rehab/thumbnails") -> str:
    """Upload an image file to Cloudinary. Returns the secure URL."""
    result = cloudinary.uploader.upload(
        local_path,
        resource_type="image",
        folder=folder,
        overwrite=False,
    )
    return result["secure_url"]


def is_configured() -> bool:
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)
