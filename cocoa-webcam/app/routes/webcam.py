from fastapi import APIRouter, HTTPException, Request, UploadFile, File
import base64
import logging
from datetime import datetime
from PIL import Image
import io

router = APIRouter()
logger = logging.getLogger(__name__)

rate_limit_cache = {}

async def check_rate_limit(request: Request, max_requests=100, window_seconds=3600):
    """Simple rate limiter"""
    client_ip = request.client.host
    current_time = datetime.utcnow().timestamp()
    
    if client_ip not in rate_limit_cache:
        rate_limit_cache[client_ip] = []
    
    # Clean old requests
    rate_limit_cache[client_ip] = [
        req_time for req_time in rate_limit_cache[client_ip]
        if current_time - req_time < window_seconds
    ]
    
    if len(rate_limit_cache[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per hour."
        )
    
    rate_limit_cache[client_ip].append(current_time)
    return True

@router.post("/capture")
async def capture_frame(request: Request, file: UploadFile = File(...)):
    """Process captured frame from webcam"""
    
    # Apply rate limiting
    await check_rate_limit(request)
    
    try:
        contents = await file.read()
        
        img = Image.open(io.BytesIO(contents))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        max_size = 720
        if img.width > max_size or img.height > max_size:
            ratio = max_size / max(img.width, img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "success": True,
            "image": img_base64,
            "dimensions": f"{img.width}x{img.height}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Frame capture error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process frame: {str(e)}")

@router.get("/devices")
async def get_devices(request: Request):
    """Get available webcam devices info"""
    await check_rate_limit(request)
    
    return {
        "devices": [
            {"id": 0, "name": "Default Camera", "resolution": "1280x720"}
        ]
    }