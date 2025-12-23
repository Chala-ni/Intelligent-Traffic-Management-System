"""
Intelligent Traffic Management System - FastAPI Application
Main entry point with health checks, SSE endpoints, and API routing
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.routers import video_router, parking_router
from app.routers.scoring import router as scoring_router
from app.routers.signal import router as signal_router
from app.routers.junction import router as junction_router
from app.db.database import init_db

settings = get_settings()

# --- Event Queue for SSE ---
# Simple in-memory queue for broadcasting events to connected clients
event_queue: asyncio.Queue = asyncio.Queue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    print(f"🚦 {settings.app_name} v{settings.app_version} starting...")
    print(f"📁 Data directory: {settings.data_dir}")
    print(f"🎯 Vehicle model: {settings.vehicle_model}")
    print(f"🔖 Plate model: {settings.plate_model}")
    # Initialize database tables
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init failed: {e}")
    yield
    # Shutdown
    print("🛑 Shutting down...")


# --- FastAPI App ---
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered traffic management with violation detection, driver scoring, and adaptive signals",
    lifespan=lifespan,
)

# --- CORS Middleware (allow Flutter web app) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Flutter app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(video_router)
app.include_router(parking_router)
app.include_router(scoring_router)
app.include_router(signal_router)
app.include_router(junction_router)  # Member 2 & 4: Junction Safety, Behavior, Risk

# --- Static Files (for simulation UI and videos) ---
from pathlib import Path
static_dir = Path(__file__).parent / "wokwi"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount videos directory for serving annotated videos
videos_dir = Path(settings.data_dir) / "videos"
if videos_dir.exists():
    app.mount("/videos", StaticFiles(directory=str(videos_dir)), name="videos")


@app.get("/simulation", tags=["Simulation"])
async def simulation_page():
    """Serve the traffic signal simulation page."""
    html_path = static_dir / "simulation.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Simulation page not found"}


@app.get("/detect", tags=["Detection"])
async def detection_page():
    """Serve the live vehicle and plate detection video player page."""
    html_path = static_dir / "video_player.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"error": "Detection page not found"}


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["Status"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
    }


@app.get("/version", tags=["Status"])
async def version_info():
    """Get detailed version and configuration info."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "models": {
            "vehicle_detection": settings.vehicle_model,
            "plate_detection": settings.plate_model,
        },
        "settings": {
            "detection_confidence": settings.detection_confidence,
            "frame_skip": settings.frame_skip,
            "parking_duration_threshold": settings.parking_duration_threshold,
        },
    }


# =============================================================================
# SSE (Server-Sent Events) Endpoint for Real-time Updates
# =============================================================================

async def event_generator(request: Request) -> AsyncGenerator[dict, None]:
    """Generate SSE events from the event queue."""
    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            try:
                # Wait for events with timeout to allow disconnect checks
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                yield {
                    "event": event.get("type", "message"),
                    "data": event.get("data", {}),
                    "retry": settings.sse_retry_timeout,
                }
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield {
                    "event": "ping",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                }
    except asyncio.CancelledError:
        print("SSE client disconnected")


@app.get("/events", tags=["Real-time"])
async def sse_events(request: Request):
    """
    Server-Sent Events endpoint for real-time updates.
    
    Event types:
    - detection: New vehicle/object detected
    - violation: Parking or traffic violation detected  
    - score_update: Driver score changed
    - signal_change: Traffic signal state changed
    - ping: Keepalive heartbeat
    """
    return EventSourceResponse(event_generator(request))


async def broadcast_event(event_type: str, data: dict):
    """Broadcast an event to all connected SSE clients."""
    await event_queue.put({
        "type": event_type,
        "data": {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    })


# =============================================================================
# Pipeline Control Endpoints (Now using video router)
# =============================================================================

@app.post("/pipeline/start", tags=["Pipeline"])
async def start_pipeline(video_source: str = None):
    """
    Start the detection pipeline with optional video source.
    
    Note: Use /video/stream endpoint directly for MJPEG streaming.
    This endpoint is for programmatic control.
    """
    await broadcast_event("pipeline", {"status": "started", "source": video_source})
    return {
        "status": "started", 
        "message": "Use /video/stream?source=<path> for MJPEG streaming",
        "stream_url": f"/video/stream?source={video_source}" if video_source else "/video/stream",
    }


@app.post("/pipeline/stop", tags=["Pipeline"])
async def stop_pipeline():
    """Stop the detection pipeline."""
    from app.routers.video import _pipeline_state
    _pipeline_state["running"] = False
    await broadcast_event("pipeline", {"status": "stopped"})
    return {"status": "stopped", "message": "Pipeline stop requested"}


@app.get("/pipeline/status", tags=["Pipeline"])
async def pipeline_status():
    """Get current pipeline status."""
    from app.routers.video import get_pipeline_state
    state = get_pipeline_state()
    return {
        "running": state["running"],
        "video_source": state["video_source"],
        "frames_processed": state["frames_processed"],
        "detections": state["total_detections"],
        "uptime_seconds": state.get("uptime_seconds", 0),
    }


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
        },
    )


# =============================================================================
# Development entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
