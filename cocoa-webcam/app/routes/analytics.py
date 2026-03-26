from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
from collections import defaultdict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

analytics_data = defaultdict(lambda: {"captures": 0, "last_active": None})

@router.post("/track")
async def track_activity(request: Request):
    """Track user activity"""
    try:
        client_ip = request.client.host
        analytics_data[client_ip]["captures"] += 1
        analytics_data[client_ip]["last_active"] = datetime.utcnow()
        
        return {"success": True, "captures": analytics_data[client_ip]["captures"]}
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/stats")
async def get_stats(request: Request):
    """Get analytics statistics"""
    try:
        total_captures = sum(data["captures"] for data in analytics_data.values())
        active_users = sum(1 for data in analytics_data.values() 
                           if data["last_active"] and 
                           datetime.utcnow() - data["last_active"] < timedelta(minutes=5))
        
        return {
            "total_captures": total_captures,
            "active_users": active_users,
            "unique_users": len(analytics_data),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "total_captures": 0,
            "active_users": 0,
            "unique_users": 0,
            "error": str(e)
        }
