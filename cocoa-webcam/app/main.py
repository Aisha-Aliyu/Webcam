import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cocoa WebCam Studio Pro",
    description="Professional webcam application with real-time filters",
    version="3.2.0"
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directories
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/static/css", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rate limiter
class ProductionRateLimiter:
    def __init__(self, max_requests=100, window_seconds=3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check(self, client_ip):
        current_time = datetime.utcnow().timestamp()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False, f"Rate limit exceeded. Maximum {self.max_requests} requests per hour."
        
        self.requests[client_ip].append(current_time)
        return True, "OK"

rate_limiter = ProductionRateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if request.url.path.startswith("/static"):
        return await call_next(request)
    
    allowed, message = await rate_limiter.check(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": message, "status": "rate_limited"}
        )
    
    response = await call_next(request)
    return response

# The whole app runs in the browser. Its page lives in static/index.html, so the same
# file is hosted on its own (GitHub Pages) and served from here for local runs.
INDEX_FILE = Path(__file__).resolve().parent / "static" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=INDEX_FILE.read_text(encoding="utf-8"))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["real_time_filters", "camera_cycling", "video_recording"]
    }
