import time
from collections import defaultdict
from fastapi import HTTPException, Request
import os

class RateLimiter:
    """Simple in-memory rate limiter with IP-based tracking"""
    
    def __init__(self, max_requests=100, window_seconds=3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request):
        """Check if client has exceeded rate limit"""
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        return True

rate_limiter = RateLimiter(
    max_requests=int(os.getenv("API_RATE_LIMIT", 100)),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", 3600))
)
