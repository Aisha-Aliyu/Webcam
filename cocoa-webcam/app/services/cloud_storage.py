import httpx
import base64
import os
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CloudinaryStorage:
    """Cloudinary storage service for images"""
    
    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        self.api_key = os.getenv("CLOUDINARY_API_KEY", "")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET", "")
        self.upload_preset = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")
        
    async def upload_image(self, image_base64: str, user_id: str = "anonymous") -> Optional[dict]:
        """Upload image to Cloudinary"""
        if not self.cloud_name:
            logger.warning("Cloudinary not configured, skipping upload")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Upload to Cloudinary
                url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
                
                # Prepare data
                data = {
                    "file": f"data:image/jpeg;base64,{image_base64}",
                    "upload_preset": self.upload_preset,
                    "public_id": f"cocoa_capture_{user_id}_{datetime.utcnow().timestamp()}",
                    "folder": f"cocoa_webcam/{user_id}"
                }
                
                response = await client.post(url, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "url": result.get("secure_url"),
                        "public_id": result.get("public_id"),
                        "width": result.get("width"),
                        "height": result.get("height")
                    }
                else:
                    logger.error(f"Cloudinary upload failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            return None

cloud_storage = CloudinaryStorage()
