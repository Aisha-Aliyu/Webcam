import os
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

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Cocoa WebCam Studio Pro | Real-Time Filters</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: #f3e7d9;
            color: #544349;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .app {
            max-width: 1600px;
            margin: 0 auto;
            padding: 1.5rem;
            min-height: 100vh;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 2px solid #544349;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .logo svg {
            width: 32px;
            height: 32px;
            stroke: #544349;
        }
        
        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(84, 67, 73, 0.1);
            border-radius: 2rem;
            font-size: 0.875rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27ae60;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }
        
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        @media (max-width: 968px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
        }
        
        .video-wrapper {
            background: #544349;
            border-radius: 1.5rem;
            padding: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .video-container {
            position: relative;
            border-radius: 1rem;
            overflow: hidden;
            background: #2c2428;
        }
        
        #video-canvas {
            width: 100%;
            height: auto;
            display: block;
            transform: scaleX(-1);
        }
        
        .recording-indicator {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(231, 76, 60, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 2rem;
            font-size: 0.875rem;
            font-weight: bold;
            display: none;
            align-items: center;
            gap: 0.5rem;
            z-index: 10;
            pointer-events: none;
        }
        
        .recording-indicator.active {
            display: flex;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .controls-panel {
            background: white;
            border-radius: 1rem;
            padding: 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .panel-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f3e7d9;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.25rem;
            font-size: 0.875rem;
            font-weight: 600;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
        }
        
        .btn-primary {
            background: #544349;
            color: #f3e7d9;
        }
        
        .btn-primary:hover {
            background: #6b5566;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: transparent;
            color: #544349;
            border: 2px solid #544349;
        }
        
        .btn-secondary:hover {
            background: #544349;
            color: #f3e7d9;
        }
        
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c0392b;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #27ae60;
            color: white;
        }
        
        .btn-success:hover {
            background: #229954;
            transform: translateY(-2px);
        }
        
        .filter-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.5rem;
        }
        
        .filter-btn {
            padding: 0.6rem 0.5rem;
            background: #f3e7d9;
            border: 2px solid #544349;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.7rem;
            font-weight: 500;
            transition: all 0.2s;
            text-align: center;
        }
        
        .filter-btn.active {
            background: #544349;
            color: #f3e7d9;
            transform: scale(1.02);
        }
        
        .filter-btn:hover {
            transform: translateY(-2px);
        }
        
        .camera-buttons {
            display: flex;
            gap: 0.75rem;
            margin-top: 0.5rem;
        }
        
        .camera-buttons .btn {
            flex: 1;
            justify-content: center;
        }
        
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        
        .stat-card {
            background: #f3e7d9;
            padding: 0.75rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        
        .stat-number {
            font-size: 1.5rem;
            font-weight: bold;
            color: #544349;
        }
        
        .stat-label {
            font-size: 0.7rem;
            color: #6b5566;
        }
        
        .gallery-section {
            background: white;
            border-radius: 1rem;
            padding: 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .gallery-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 0.75rem;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .gallery-item {
            position: relative;
            border-radius: 0.5rem;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.2s;
            background: #f3e7d9;
        }
        
        .gallery-item:hover {
            transform: translateY(-2px);
        }
        
        .gallery-item img {
            width: 100%;
            height: 100px;
            object-fit: cover;
        }
        
        .gallery-item-info {
            padding: 0.25rem;
            font-size: 0.65rem;
            background: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            background: #544349;
            color: #f3e7d9;
            padding: 0.75rem 1.5rem;
            border-radius: 2rem;
            font-size: 0.875rem;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes flash {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; background: rgba(243, 231, 217, 0.3); }
        }
        
        .flash-animation {
            animation: flash 0.3s ease;
        }
        
        .current-filter-badge {
            background: #544349;
            color: #f3e7d9;
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: normal;
        }
        
        .device-info {
            font-size: 0.7rem;
            color: #6b5566;
            text-align: center;
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid #f3e7d9;
        }
        
        @media (max-width: 768px) {
            .app {
                padding: 1rem;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .btn {
                justify-content: center;
            }
            
            .filter-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <header class="header">
            <div class="logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="4"/>
                    <path d="M5 5L7 7M19 5L17 7"/>
                </svg>
                <span>Cocoa WebCam Studio Pro</span>
            </div>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span id="status-text">Initializing...</span>
            </div>
        </header>

        <div class="main-layout">
            <div class="video-wrapper">
                <div class="video-container">
                    <canvas id="video-canvas"></canvas>
                    <div class="recording-indicator" id="recording-indicator">
                        <span>🔴</span> RECORDING
                    </div>
                </div>
            </div>

            <div class="sidebar">
                <div class="controls-panel">
                    <div class="panel-title">
                        Capture
                        <span id="current-filter-badge" class="current-filter-badge">Normal</span>
                    </div>
                    <div class="button-group">
                        <button id="capture-btn" class="btn btn-primary">Take Photo</button>
                        <button id="record-btn" class="btn btn-danger">Record Video</button>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number" id="capture-count">0</div>
                            <div class="stat-label">Total Captures</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="session-count">0</div>
                            <div class="stat-label">This Session</div>
                        </div>
                    </div>
                </div>

                <div class="controls-panel">
                    <div class="panel-title">Real-Time Filters</div>
                    <div class="filter-grid" id="filter-grid">
                        <button data-filter="none" class="filter-btn active">Normal</button>
                        <button data-filter="grayscale" class="filter-btn">B&W</button>
                        <button data-filter="sepia" class="filter-btn">Sepia</button>
                        <button data-filter="vintage" class="filter-btn">Vintage</button>
                        <button data-filter="cool" class="filter-btn">Cool</button>
                        <button data-filter="warm" class="filter-btn">Warm</button>
                        <button data-filter="invert" class="filter-btn">Invert</button>
                        <button data-filter="sharpen" class="filter-btn">Sharpen</button>
                        <button data-filter="brighten" class="filter-btn">Brighten</button>
                        <button data-filter="darken" class="filter-btn">Darken</button>
                    </div>
                </div>

                <div class="controls-panel">
                    <div class="panel-title">Camera</div>
                    <div class="camera-buttons">
                        <button id="switch-front-btn" class="btn btn-secondary">👤 Front</button>
                        <button id="switch-back-btn" class="btn btn-secondary">📱 Back</button>
                        <button id="cycle-camera-btn" class="btn btn-secondary">🔄 Cycle</button>
                    </div>
                    <div id="camera-info" class="device-info">
                        <span id="current-camera-name">Detecting cameras...</span>
                    </div>
                </div>

                <div class="controls-panel">
                    <div class="panel-title">Export</div>
                    <div class="button-group">
                        <button id="download-all-btn" class="btn btn-secondary">Download All</button>
                        <button id="share-btn" class="btn btn-secondary">Share Latest</button>
                        <button id="clear-btn" class="btn btn-secondary">Clear All</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="gallery-section">
            <div class="gallery-header">
                <div class="panel-title">Capture Gallery</div>
                <div id="gallery-info" style="font-size: 0.75rem; color: #6b5566;"></div>
            </div>
            <div id="gallery" class="gallery-grid">
                <div style="text-align: center; padding: 2rem; color: #6b5566;">
                    No captures yet<br>
                    <small>Click Capture to take photos</small>
                </div>
            </div>
        </div>
    </div>

    <script>
        class FinalWebCam {
            constructor() {
                this.videoCanvas = document.getElementById('video-canvas');
                this.captureBtn = document.getElementById('capture-btn');
                this.recordBtn = document.getElementById('record-btn');
                this.downloadAllBtn = document.getElementById('download-all-btn');
                this.shareBtn = document.getElementById('share-btn');
                this.clearBtn = document.getElementById('clear-btn');
                this.switchFrontBtn = document.getElementById('switch-front-btn');
                this.switchBackBtn = document.getElementById('switch-back-btn');
                this.cycleCameraBtn = document.getElementById('cycle-camera-btn');
                this.galleryDiv = document.getElementById('gallery');
                this.statusSpan = document.getElementById('status-text');
                this.captureCountSpan = document.getElementById('capture-count');
                this.sessionCountSpan = document.getElementById('session-count');
                this.recordingIndicator = document.getElementById('recording-indicator');
                this.currentFilterBadge = document.getElementById('current-filter-badge');
                this.currentCameraNameSpan = document.getElementById('current-camera-name');
                
                this.stream = null;
                this.videoElement = null;
                this.cameras = [];
                this.currentCameraIndex = 0;
                this.captures = [];
                this.sessionCaptures = 0;
                this.currentFilter = 'none';
                this.isRecording = false;
                this.mediaRecorder = null;
                this.recordedChunks = [];
                this.animationId = null;
                
                this.init();
                this.setupFilters();
                this.setupKeyboardShortcuts();
            }
            
            async init() {
                try {
                    await this.loadCameras();
                    await this.startCamera();
                    this.loadCaptures();
                    this.setupEventListeners();
                    this.startRealTimeFilterLoop();
                    this.updateStatus('Camera ready - Real-time filters active', 'success');
                    this.updateStats();
                } catch (error) {
                    console.error('Init error:', error);
                    this.updateStatus('Please allow camera access and refresh', 'error');
                }
            }
            
            async loadCameras() {
                await navigator.mediaDevices.getUserMedia({ video: true });
                
                const devices = await navigator.mediaDevices.enumerateDevices();
                this.cameras = devices.filter(device => device.kind === 'videoinput');
                
                if (this.cameras.length === 0) {
                    throw new Error('No cameras found');
                }
                
                this.cameras.sort((a, b) => {
                    const aLabel = a.label.toLowerCase();
                    const bLabel = b.label.toLowerCase();
                    
                    // Front cameras first
                    if (aLabel.includes('front') && !bLabel.includes('front')) return -1;
                    if (!aLabel.includes('front') && bLabel.includes('front')) return 1;
                    
                    // Then back cameras
                    if (aLabel.includes('back') && !bLabel.includes('back')) return 1;
                    if (!aLabel.includes('back') && bLabel.includes('back')) return -1;
                    
                    return 0;
                });
                
                this.currentCameraIndex = 0;
                this.updateCameraInfo();
            }
            
            updateCameraInfo() {
                if (this.cameras.length > 0 && this.currentCameraIndex < this.cameras.length) {
                    const camera = this.cameras[this.currentCameraIndex];
                    let displayName = camera.label || `Camera ${this.currentCameraIndex + 1}`;
                    
                    if (displayName.toLowerCase().includes('front')) displayName = '📱 Front Camera';
                    else if (displayName.toLowerCase().includes('back')) displayName = '📷 Back Camera';
                    else if (displayName.toLowerCase().includes('user')) displayName = '👤 Front Camera';
                    else if (displayName.toLowerCase().includes('environment')) displayName = '🌄 Back Camera';
                    else displayName = `Camera ${this.currentCameraIndex + 1}`;
                    
                    this.currentCameraNameSpan.textContent = displayName;
                } else {
                    this.currentCameraNameSpan.textContent = 'No camera detected';
                }
            }
            
            async startCamera() {
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                }
                
                if (this.cameras.length === 0) {
                    throw new Error('No cameras available');
                }
                
                const cameraId = this.cameras[this.currentCameraIndex].deviceId;
                
                const constraints = {
                    video: {
                        deviceId: cameraId ? { exact: cameraId } : undefined,
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        frameRate: { ideal: 30 }
                    }
                };
                
                try {
                    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
                    
                    if (!this.videoElement) {
                        this.videoElement = document.createElement('video');
                        this.videoElement.autoplay = true;
                        this.videoElement.playsInline = true;
                        this.videoElement.muted = true;
                    }
                    this.videoElement.srcObject = this.stream;
                    await this.videoElement.play();
                    
                    // Set canvas dimensions
                    this.videoCanvas.width = this.videoElement.videoWidth;
                    this.videoCanvas.height = this.videoElement.videoHeight;
                    
                    this.updateStatus(`Using: ${this.currentCameraNameSpan.textContent}`, 'success');
                } catch (error) {
                    console.error('Camera start error:', error);
                    this.updateStatus('Failed to start camera', 'error');
                    throw error;
                }
            }
            
            async switchToFrontCamera() {
                // Find front camera
                const frontIndex = this.cameras.findIndex(cam => 
                    cam.label.toLowerCase().includes('front') || 
                    cam.label.toLowerCase().includes('user')
                );
                
                if (frontIndex !== -1 && frontIndex !== this.currentCameraIndex) {
                    this.currentCameraIndex = frontIndex;
                    await this.startCamera();
                    this.updateCameraInfo();
                    this.updateStatus('Switched to front camera', 'success');
                } else {
                    // Try cycling to first camera
                    this.currentCameraIndex = 0;
                    await this.startCamera();
                    this.updateCameraInfo();
                    this.updateStatus('Switched to first camera', 'success');
                }
            }
            
            async switchToBackCamera() {
                // Find back camera
                const backIndex = this.cameras.findIndex(cam => 
                    cam.label.toLowerCase().includes('back') || 
                    cam.label.toLowerCase().includes('rear') ||
                    cam.label.toLowerCase().includes('environment')
                );
                
                if (backIndex !== -1 && backIndex !== this.currentCameraIndex) {
                    this.currentCameraIndex = backIndex;
                    await this.startCamera();
                    this.updateCameraInfo();
                    this.updateStatus('Switched to back camera', 'success');
                } else if (this.cameras.length > 1) {
                    // Try the last camera
                    this.currentCameraIndex = this.cameras.length - 1;
                    await this.startCamera();
                    this.updateCameraInfo();
                    this.updateStatus('Switched to alternate camera', 'success');
                } else {
                    this.updateStatus('Only one camera available', 'info');
                }
            }
            
            async cycleCamera() {
                if (this.cameras.length <= 1) {
                    this.updateStatus('Only one camera available', 'info');
                    return;
                }
                
                this.currentCameraIndex = (this.currentCameraIndex + 1) % this.cameras.length;
                await this.startCamera();
                this.updateCameraInfo();
                this.updateStatus(`Switched to ${this.currentCameraNameSpan.textContent}`, 'success');
            }
            
            startRealTimeFilterLoop() {
                const applyFiltersToFrame = () => {
                    if (!this.videoElement || !this.videoCanvas || this.videoElement.paused || !this.videoElement.videoWidth) {
                        this.animationId = requestAnimationFrame(applyFiltersToFrame);
                        return;
                    }
                    
                    if (this.videoCanvas.width !== this.videoElement.videoWidth || 
                        this.videoCanvas.height !== this.videoElement.videoHeight) {
                        this.videoCanvas.width = this.videoElement.videoWidth;
                        this.videoCanvas.height = this.videoElement.videoHeight;
                    }
                    
                    const ctx = this.videoCanvas.getContext('2d');
                    ctx.save();
                    ctx.scale(-1, 1);
                    ctx.drawImage(this.videoElement, -this.videoCanvas.width, 0, this.videoCanvas.width, this.videoCanvas.height);
                    ctx.restore();
                    
                    if (this.currentFilter !== 'none') {
                        this.applyFilterToCanvas(ctx, this.videoCanvas.width, this.videoCanvas.height, this.currentFilter);
                    }
                    
                    this.animationId = requestAnimationFrame(applyFiltersToFrame);
                };
                
                applyFiltersToFrame();
            }
            
            applyFilterToCanvas(ctx, width, height, filterType) {
                const imgData = ctx.getImageData(0, 0, width, height);
                const data = imgData.data;
                
                switch(filterType) {
                    case 'grayscale':
                        for (let i = 0; i < data.length; i += 4) {
                            const gray = data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114;
                            data[i] = gray;
                            data[i+1] = gray;
                            data[i+2] = gray;
                        }
                        break;
                    case 'sepia':
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i], g = data[i+1], b = data[i+2];
                            data[i] = Math.min(255, (r * 0.393) + (g * 0.769) + (b * 0.189));
                            data[i+1] = Math.min(255, (r * 0.349) + (g * 0.686) + (b * 0.168));
                            data[i+2] = Math.min(255, (r * 0.272) + (g * 0.534) + (b * 0.131));
                        }
                        break;
                    case 'vintage':
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i], g = data[i+1], b = data[i+2];
                            data[i] = Math.min(255, r * 0.9 + g * 0.3);
                            data[i+1] = Math.min(255, r * 0.2 + g * 0.7 + b * 0.1);
                            data[i+2] = Math.min(255, r * 0.1 + g * 0.2 + b * 0.8);
                        }
                        break;
                    case 'cool':
                        for (let i = 0; i < data.length; i += 4) {
                            data[i] = Math.min(255, data[i] * 0.8);
                            data[i+2] = Math.min(255, data[i+2] * 1.2);
                        }
                        break;
                    case 'warm':
                        for (let i = 0; i < data.length; i += 4) {
                            data[i] = Math.min(255, data[i] * 1.2);
                            data[i+2] = Math.min(255, data[i+2] * 0.8);
                        }
                        break;
                    case 'invert':
                        for (let i = 0; i < data.length; i += 4) {
                            data[i] = 255 - data[i];
                            data[i+1] = 255 - data[i+1];
                            data[i+2] = 255 - data[i+2];
                        }
                        break;
                    case 'brighten':
                        for (let i = 0; i < data.length; i += 4) {
                            data[i] = Math.min(255, data[i] * 1.3);
                            data[i+1] = Math.min(255, data[i+1] * 1.3);
                            data[i+2] = Math.min(255, data[i+2] * 1.3);
                        }
                        break;
                    case 'darken':
                        for (let i = 0; i < data.length; i += 4) {
                            data[i] = data[i] * 0.7;
                            data[i+1] = data[i+1] * 0.7;
                            data[i+2] = data[i+2] * 0.7;
                        }
                        break;
                    case 'sharpen':
                        const sharpenWidth = width;
                        const sharpenHeight = height;
                        const sharpenTemp = new Uint8ClampedArray(data);
                        for (let y = 1; y < sharpenHeight - 1; y++) {
                            for (let x = 1; x < sharpenWidth - 1; x++) {
                                const idx = (y * sharpenWidth + x) * 4;
                                for (let c = 0; c < 3; c++) {
                                    let val = sharpenTemp[idx + c] * 5;
                                    val -= sharpenTemp[((y-1) * sharpenWidth + x) * 4 + c];
                                    val -= sharpenTemp[((y+1) * sharpenWidth + x) * 4 + c];
                                    val -= sharpenTemp[(y * sharpenWidth + (x-1)) * 4 + c];
                                    val -= sharpenTemp[(y * sharpenWidth + (x+1)) * 4 + c];
                                    data[idx + c] = Math.min(255, Math.max(0, val));
                                }
                            }
                        }
                        break;
                }
                
                ctx.putImageData(imgData, 0, 0);
            }
            
            capture() {
                try {
                    const captureCanvas = document.createElement('canvas');
                    captureCanvas.width = this.videoCanvas.width;
                    captureCanvas.height = this.videoCanvas.height;
                    const captureCtx = captureCanvas.getContext('2d');
                    captureCtx.drawImage(this.videoCanvas, 0, 0);
                    
                    const dataUrl = captureCanvas.toDataURL('image/jpeg', 0.92);
                    
                    const capture = {
                        id: Date.now(),
                        dataUrl: dataUrl,
                        timestamp: new Date().toISOString(),
                        filter: this.currentFilter,
                        timestampFormatted: new Date().toLocaleString()
                    };
                    
                    this.captures.unshift(capture);
                    this.sessionCaptures++;
                    
                    if (this.captures.length > 50) {
                        this.captures = this.captures.slice(0, 50);
                    }
                    
                    this.saveCaptures();
                    this.displayGallery();
                    this.updateStats();
                    this.updateStatus('Photo captured!', 'success');
                    this.animateCapture();
                } catch (error) {
                    console.error('Capture error:', error);
                    this.updateStatus('Capture failed', 'error');
                }
            }
            
            async startRecording() {
                if (!this.stream) {
                    this.showToast('No camera stream available');
                    return;
                }
                
                this.recordedChunks = [];
                
                try {
                    this.mediaRecorder = new MediaRecorder(this.stream, {
                        mimeType: 'video/webm;codecs=vp9,opus',
                        videoBitsPerSecond: 2500000
                    });
                    
                    this.mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            this.recordedChunks.push(event.data);
                        }
                    };
                    
                    this.mediaRecorder.onstop = () => {
                        const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `cocoa-video-${Date.now()}.webm`;
                        a.click();
                        URL.revokeObjectURL(url);
                        this.isRecording = false;
                        this.recordBtn.innerHTML = '🔴 Record Video';
                        this.recordBtn.classList.remove('btn-success');
                        this.recordBtn.classList.add('btn-danger');
                        this.recordingIndicator.classList.remove('active');
                        this.showToast('Video saved!');
                    };
                    
                    this.mediaRecorder.start(1000);
                    this.isRecording = true;
                    this.recordBtn.innerHTML = '⏹️ Stop Recording';
                    this.recordBtn.classList.remove('btn-danger');
                    this.recordBtn.classList.add('btn-success');
                    this.recordingIndicator.classList.add('active');
                    this.showToast('Recording started...');
                } catch (error) {
                    console.error('Recording error:', error);
                    this.showToast('Recording failed');
                }
            }
            
            stopRecording() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                }
            }
            
            toggleRecording() {
                if (this.isRecording) {
                    this.stopRecording();
                } else {
                    this.startRecording();
                }
            }
            
            setupFilters() {
                const filterBtns = document.querySelectorAll('.filter-btn');
                filterBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        filterBtns.forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        this.currentFilter = btn.dataset.filter;
                        this.currentFilterBadge.textContent = btn.textContent;
                        this.showToast(`Filter: ${btn.textContent} (real-time)`);
                    });
                });
            }
            
            animateCapture() {
                const videoContainer = document.querySelector('.video-container');
                videoContainer.classList.add('flash-animation');
                setTimeout(() => videoContainer.classList.remove('flash-animation'), 300);
            }
            
            deleteCapture(id) {
                this.captures = this.captures.filter(cap => cap.id !== id);
                this.saveCaptures();
                this.displayGallery();
                this.updateStats();
                this.showToast('Photo deleted');
            }
            
            clearAllCaptures() {
                if (this.captures.length === 0) return;
                if (confirm(`Delete all ${this.captures.length} photos?`)) {
                    this.captures = [];
                    this.saveCaptures();
                    this.displayGallery();
                    this.updateStats();
                    this.showToast('All photos cleared');
                }
            }
            
            displayGallery() {
                if (this.captures.length === 0) {
                    this.galleryDiv.innerHTML = '<div style="text-align: center; padding: 2rem; color: #6b5566;">No captures yet<br><small>Click Capture to take photos</small></div>';
                    document.getElementById('gallery-info').textContent = '0 photos';
                    return;
                }
                
                this.galleryDiv.innerHTML = '';
                document.getElementById('gallery-info').textContent = `${this.captures.length} photos`;
                
                this.captures.forEach(capture => {
                    const item = document.createElement('div');
                    item.className = 'gallery-item';
                    
                    const img = document.createElement('img');
                    img.src = capture.dataUrl;
                    
                    const info = document.createElement('div');
                    info.className = 'gallery-item-info';
                    
                    const timeSpan = document.createElement('span');
                    timeSpan.textContent = new Date(capture.timestamp).toLocaleTimeString();
                    
                    const filterIcon = document.createElement('span');
                    const icons = {
                        'none': '📷',
                        'grayscale': '⚫',
                        'sepia': '🟤',
                        'vintage': '📻',
                        'cool': '❄️',
                        'warm': '🔥',
                        'invert': '🔄',
                        'sharpen': '✨',
                        'brighten': '☀️',
                        'darken': '🌙'
                    };
                    filterIcon.textContent = icons[capture.filter] || '📷';
                    filterIcon.style.marginRight = '0.25rem';
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '×';
                    deleteBtn.style.cssText = 'background: #e74c3c; color: white; border: none; padding: 2px 6px; border-radius: 3px; cursor: pointer;';
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        this.deleteCapture(capture.id);
                    };
                    
                    const leftGroup = document.createElement('div');
                    leftGroup.style.display = 'flex';
                    leftGroup.style.alignItems = 'center';
                    leftGroup.style.gap = '0.25rem';
                    leftGroup.appendChild(filterIcon);
                    leftGroup.appendChild(timeSpan);
                    
                    info.appendChild(leftGroup);
                    info.appendChild(deleteBtn);
                    
                    item.appendChild(img);
                    item.appendChild(info);
                    
                    item.onclick = () => {
                        const modal = window.open();
                        modal.document.write(`
                            <html>
                            <head><title>Cocoa Capture</title></head>
                            <body style="margin:0; background:black; display:flex; justify-content:center; align-items:center; min-height:100vh;">
                                <img src="${capture.dataUrl}" style="max-width:100%; max-height:100vh;">
                            </body>
                            </html>
                        `);
                    };
                    
                    this.galleryDiv.appendChild(item);
                });
            }
            
            downloadAll() {
                if (this.captures.length === 0) {
                    this.showToast('No photos to download');
                    return;
                }
                
                this.captures.forEach((capture, index) => {
                    setTimeout(() => {
                        const link = document.createElement('a');
                        link.download = `cocoa-capture-${capture.id}.jpg`;
                        link.href = capture.dataUrl;
                        link.click();
                    }, index * 100);
                });
                
                this.showToast(`Downloading ${this.captures.length} photos...`);
            }
            
            async shareLatest() {
                if (this.captures.length === 0) {
                    this.showToast('No photos to share');
                    return;
                }
                
                const latestCapture = this.captures[0];
                
                if (navigator.share) {
                    try {
                        const response = await fetch(latestCapture.dataUrl);
                        const blob = await response.blob();
                        const file = new File([blob], `cocoa-capture-${Date.now()}.jpg`, { type: 'image/jpeg' });
                        
                        await navigator.share({
                            title: 'Cocoa WebCam Studio',
                            text: `Captured with ${latestCapture.filter || 'Normal'} filter!`,
                            files: [file]
                        });
                        this.showToast('Shared successfully!');
                    } catch (error) {
                        this.showToast('Share cancelled');
                    }
                } else {
                    this.showToast('Share not supported on this device');
                }
            }
            
            setupKeyboardShortcuts() {
                document.addEventListener('keydown', (e) => {
                    if (e.code === 'Space' && !e.target.matches('input, textarea, button')) {
                        e.preventDefault();
                        this.capture();
                    }
                    else if (e.code === 'KeyR' && !e.target.matches('input, textarea')) {
                        e.preventDefault();
                        this.toggleRecording();
                    }
                    else if (e.code === 'KeyC' && !e.target.matches('input, textarea')) {
                        e.preventDefault();
                        this.cycleCamera();
                    }
                    else if (e.code === 'KeyF' && !e.target.matches('input, textarea')) {
                        e.preventDefault();
                        this.switchToFrontCamera();
                    }
                    else if (e.code === 'KeyB' && !e.target.matches('input, textarea')) {
                        e.preventDefault();
                        this.switchToBackCamera();
                    }
                    else if (e.code === 'Delete') {
                        e.preventDefault();
                        this.clearAllCaptures();
                    }
                    else if (e.code === 'KeyD' && !e.target.matches('input, textarea')) {
                        e.preventDefault();
                        this.downloadAll();
                    }
                });
            }
            
            saveCaptures() {
                localStorage.setItem('cocoa_webcam_captures_final', JSON.stringify(this.captures));
            }
            
            loadCaptures() {
                const saved = localStorage.getItem('cocoa_webcam_captures_final');
                if (saved) {
                    this.captures = JSON.parse(saved);
                    this.displayGallery();
                    this.updateStats();
                }
            }
            
            updateStats() {
                this.captureCountSpan.textContent = this.captures.length;
                this.sessionCountSpan.textContent = this.sessionCaptures;
            }
            
            updateStatus(message, type = 'info') {
                this.statusSpan.textContent = message;
                const dot = document.querySelector('.status-dot');
                if (type === 'error') dot.style.background = '#e74c3c';
                else if (type === 'success') dot.style.background = '#27ae60';
                else dot.style.background = '#f39c12';
                
                if (type !== 'error') {
                    setTimeout(() => {
                        if (this.statusSpan.textContent === message) {
                            this.statusSpan.textContent = 'Ready';
                            dot.style.background = '#27ae60';
                        }
                    }, 3000);
                }
            }
            
            showToast(message) {
                const toast = document.createElement('div');
                toast.className = 'toast';
                toast.textContent = message;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 2000);
            }
            
            setupEventListeners() {
                this.captureBtn.addEventListener('click', () => this.capture());
                this.recordBtn.addEventListener('click', () => this.toggleRecording());
                this.downloadAllBtn.addEventListener('click', () => this.downloadAll());
                this.shareBtn.addEventListener('click', () => this.shareLatest());
                this.clearBtn.addEventListener('click', () => this.clearAllCaptures());
                this.switchFrontBtn.addEventListener('click', () => this.switchToFrontCamera());
                this.switchBackBtn.addEventListener('click', () => this.switchToBackCamera());
                this.cycleCameraBtn.addEventListener('click', () => this.cycleCamera());
            }
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            window.app = new FinalWebCam();
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=HTML)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["real_time_filters", "camera_cycling", "video_recording"]
    }
