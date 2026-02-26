import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)

async def upload_image(image_base64: str) -> str:
    """Uploads base64 image string to Cloudinary and returns secure URL."""
    # Cloudinary's python SDK upload is blocking, but it handles base64 natively just like Node.
    result = cloudinary.uploader.upload(image_base64)
    return result.get("secure_url")
