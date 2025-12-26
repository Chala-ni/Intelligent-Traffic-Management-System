"""
Intelligent Traffic Management System - Video Streaming Router
MJPEG streaming with real-time YOLOv8 two-stage detection overlay

Sprint G (Revision): Uses "Zoom" detection pipeline:
- Stage 1: Vehicle tracking (wide view)
- Stage 2: Plate detection via cropping each vehicle (zoom view)

Client disconnect detection: Properly stops stream when frontend disconnects.
WebSocket streaming: Alternative to MJPEG for better browser compatibility.
"""

import asyncio
import time
import json
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime

import cv2
import aiosqlite
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.config import get_settings
from app.detection.yolo_detector import (
    load_vehicle_model,
    load_plate_model,
    detect_and_track,
    draw_detections,
    draw_frame_info,
    FrameResult,
    VEHICLE_CLASSES,
    set_parking_zones,
)
from app.routers.parking import get_detector  # import parking detector to overlay zones
from app.tts.tts_service import set_tts_paused  # Control TTS based on stream state

settings = get_settings()
router = APIRouter(prefix="/video", tags=["Video"])

# Database path
DB_PATH = settings.data_dir.parent / "backend" / "traffic.db"

# Active stream connections counter
_active_connections = 0
_connections_lock = asyncio.Lock()

# Global state for pipeline control
_pipeline_state = {
    "running": False,
    "stop_requested": False,
    "video_source": None,
    "model": None,
    "plate_model": None,
    "frames_processed": 0,
    "total_detections": 0,
    "plates_detected": 0,
    "start_time": None,
    "last_frame_time": None,
}


async def load_zones_from_db():
    """Load parking zones from admin dashboard DB and update detector."""
    try:
        if not DB_PATH.exists():
            print(f"[ZONES] DB not found at {DB_PATH}, using default zones")
            return
        
        async with aiosqlite.connect(str(DB_PATH)) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM parking_zones WHERE active = 1 ORDER BY id"
            )
            rows = await cursor.fetchall()
            
            if not rows:
                # No zones in DB - clear default zones so no violations are issued
                print("[ZONES] No active zones in DB, disabling violation detection")
                set_parking_zones([])
                return
            
            # Convert to detector format
            zones = []
            for row in rows:
                coords = json.loads(row["coordinates"])
                # Convert [[x,y], [x,y]...] to [(x,y), (x,y)...]
                polygon = [(int(p[0]), int(p[1])) for p in coords]
                
                # Map zone_type to color
                zone_type = row["zone_type"]
                if zone_type in ("red", "no_parking"):
                    color = (0, 0, 255)  # Red
                elif zone_type in ("yellow", "loading"):
                    color = (0, 255, 255)  # Yellow
                elif zone_type in ("blue", "handicap"):
                    color = (255, 0, 0)  # Blue
                else:
                    color = (0, 0, 255)  # Default red
                
                zones.append({
                    "id": f"zone_{row['id']}",
                    "name": row["label"] or f"Zone {row['id']}",
                    "polygon": polygon,
                    "color": color,
                })
            
            set_parking_zones(zones)
            print(f"[ZONES] ✅ Loaded {len(zones)} zones from admin dashboard DB")
            
    except Exception as e:
        print(f"[ZONES] ❌ Error loading zones: {e}")


def get_pipeline_state() -> dict:
    """Get current pipeline state."""
    state = _pipeline_state.copy()
    if state["start_time"]:
        state["uptime_seconds"] = time.time() - state["start_time"]
    return state


def reset_pipeline_state():
    """Reset pipeline state."""
    _pipeline_state.update({
        "running": False,
        "stop_requested": False,
        "video_source": None,
        "frames_processed": 0,
        "total_detections": 0,
        "plates_detected": 0,
        "start_time": None,
        "last_frame_time": None,
    })


# Initialize with TTS paused (no active streams yet)
set_tts_paused(True)


@router.post("/stop")
async def stop_stream():
    """
    Stop the current video stream and pause TTS.
    Called when frontend logs out or navigates away.
    """
    global _active_connections
    
    _pipeline_state["stop_requested"] = True
    _pipeline_state["running"] = False
    
    async with _connections_lock:
        _active_connections = 0
    
    set_tts_paused(True)
    
    print("[STREAM] ⏹️ Stop requested via API")
    return {"status": "stopped", "message": "Stream stopped and TTS paused"}


async def generate_mjpeg_frames(
    video_path: str,
    frame_skip: int = None,
    confidence: float = None,
    show_detections: bool = True,
    max_fps: float = 30.0,  # Increased for smoother playback
    detect_plates_flag: bool = False,
):
    """
    Generator that yields MJPEG frames with two-stage detection overlay.
    
    Sprint G (Revision): Uses "Zoom" detection pipeline:
    - Stage 1: Vehicle tracking (every frame)
    - Stage 2: Plate detection via cropping (every 3rd frame, optimized)
    
    Args:
        video_path: Path to video file
        frame_skip: Process every Nth frame (default from settings)
        confidence: Detection confidence threshold
        show_detections: Whether to draw detection boxes
        max_fps: Maximum output FPS (throttle for browser)
        detect_plates_flag: Whether to run plate detection on detected vehicles
    """
    global _active_connections
    
    # Track active connections and enable TTS
    async with _connections_lock:
        _active_connections += 1
        if _active_connections == 1:
            set_tts_paused(False)  # Resume TTS when first stream starts
    
    print(f"[STREAM] 📡 Client connected (active: {_active_connections})")
    
    # Load parking zones from admin dashboard DB
    await load_zones_from_db()
    
    print(f"[STREAM] 🎬 Starting video stream: {video_path}")
    print(f"[STREAM]    frame_skip={frame_skip}, detect_plates={detect_plates_flag}")
    
    frame_skip = frame_skip or settings.frame_skip
    confidence = confidence or settings.detection_confidence
    min_frame_time = 1.0 / max_fps
    
    # Reset stop flag
    _pipeline_state["stop_requested"] = False
    
    # Open video with optimized buffering
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Reduce buffer for smoother playback
    if not cap.isOpened():
        print(f"[STREAM] ❌ Cannot open video: {video_path}")
        # Decrement connection count on error
        async with _connections_lock:
            _active_connections = max(0, _active_connections - 1)
            if _active_connections == 0:
                set_tts_paused(True)
        raise HTTPException(status_code=404, detail=f"Cannot open video: {video_path}")
    
    # Load models using new two-stage API
    vehicle_model = load_vehicle_model("cpu")
    _pipeline_state["model"] = settings.vehicle_model
    
    # Load plate model if requested
    plate_model = None
    if detect_plates_flag:
        plate_model = load_plate_model("cpu")
        _pipeline_state["plate_model"] = settings.plate_model
    
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[STREAM] ✅ Video opened: {total_frames} frames @ {video_fps:.1f} fps")
    
    _pipeline_state["running"] = True
    _pipeline_state["video_source"] = video_path
    _pipeline_state["start_time"] = time.time()
    
    frame_idx = 0
    log_interval = 50  # Log every 50 frames
    output_frame_count = 0  # Count frames actually sent to browser
    
    try:
        while _pipeline_state["running"] and not _pipeline_state["stop_requested"]:
            frame_start = time.time()
            
            # Skip frames in the video file itself for smooth playback
            # This avoids reading every frame which causes stuttering
            if frame_skip > 1:
                # Jump ahead by frame_skip frames
                current_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos + frame_skip - 1)
            
            ret, frame = cap.read()
            if not ret:
                # Loop video for continuous demo
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                output_frame_count = 0
                continue
            
            frame_idx += frame_skip  # Track actual frame position
            
            # Check if stop was requested
            if _pipeline_state["stop_requested"]:
                print("[STREAM] ⏹️ Stop requested, ending stream")
                break
            
            # Process every frame we read (since we already skipped in the video)
            if show_detections:
                # Use new two-stage detect_and_track API
                # This handles both vehicle tracking AND plate detection internally
                result = detect_and_track(
                    vehicle_model=vehicle_model,
                    frame=frame,
                    frame_id=frame_idx,
                    confidence=confidence,
                    plate_model=plate_model,
                    run_plate_detection=detect_plates_flag,
                )
                
                _pipeline_state["frames_processed"] += 1
                _pipeline_state["total_detections"] += len(result.detections)
                _pipeline_state["plates_detected"] += len(result.plate_boxes)
                _pipeline_state["last_frame_time"] = time.time()
                
                # Log progress periodically
                if output_frame_count % log_interval == 0:
                    print(f"[STREAM] Frame {frame_idx}: {len(result.detections)} vehicles, {len(result.plate_boxes)} plates")
                
                # Draw detections using new visualization API
                frame = draw_detections(frame, result)
                
                # Add frame info overlay
                frame = draw_frame_info(frame, result)
            
            # Resize for streaming (reduce bandwidth)
            scale = 0.75
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
            
            # Encode to JPEG with good quality
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            output_frame_count += 1
            
            # Yield as multipart MJPEG frame
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + 
                buffer.tobytes() + 
                b'\r\n'
            )
            
            # Throttle for consistent frame rate
            elapsed = time.time() - frame_start
            if elapsed < min_frame_time:
                await asyncio.sleep(max(0.001, min_frame_time - elapsed))
            
            # CRITICAL: Yield CPU to allow API requests (zones, logs) to be processed
            await asyncio.sleep(0.01)
    
    except (asyncio.CancelledError, GeneratorExit):
        # Client disconnected (browser closed, navigation, logout, etc.)
        print(f"[STREAM] 📴 Client disconnected (cancelled)")
    
    except Exception as e:
        print(f"[STREAM] ❌ Stream error: {e}")
                
    finally:
        # Decrement connection count and pause TTS if no active streams
        async with _connections_lock:
            _active_connections = max(0, _active_connections - 1)
            print(f"[STREAM] 📡 Client disconnected (remaining: {_active_connections})")
            if _active_connections == 0:
                set_tts_paused(True)  # Pause TTS when no streams active
        
        print(f"[STREAM] 🛑 Stream stopped. Processed {_pipeline_state['frames_processed']} frames, {_pipeline_state['total_detections']} detections")
        cap.release()
        reset_pipeline_state()


@router.get("/stream")
async def stream_video(
    source: str = None,
    skip: int = 3,
    confidence: float = None,
    detections: bool = True,
    detect_plates: bool = False,
):
    """
    Stream video with real-time YOLOv8 detection overlay (MJPEG).
    
    Args:
        source: Path to video file (default: sample video)
        skip: Process every Nth frame (default: 3, higher = smoother)
        confidence: Detection confidence threshold (default: 0.5)
        detections: Show detection boxes (default: true)
        detect_plates: Run license plate detection on vehicles (default: false)
    
    Returns:
        MJPEG stream for browser <img> tag or video player
    """
    # Default to sample video if no source specified
    if not source:
        source = str(settings.data_dir / "videos" / "SriLankan_Traffic_Video.mp4")
    
    if not Path(source).exists():
        # Try fallback to any video in the directory
        videos_dir = Path(settings.data_dir) / "videos"
        if videos_dir.exists():
            video_files = list(videos_dir.glob("*.mp4"))
            if video_files:
                source = str(video_files[0])
            else:
                raise HTTPException(status_code=404, detail=f"No video files found in {videos_dir}")
        else:
            raise HTTPException(status_code=404, detail=f"Video not found: {source}")
    
    return StreamingResponse(
        generate_mjpeg_frames(
            source,
            frame_skip=skip,
            confidence=confidence,
            show_detections=detections,
            detect_plates_flag=detect_plates,
        ),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/status")
async def get_stream_status():
    """Get current video streaming status."""
    state = get_pipeline_state()
    
    return {
        "running": state["running"],
        "video_source": state["video_source"],
        "model": state["model"],
        "frames_processed": state["frames_processed"],
        "total_detections": state["total_detections"],
        "uptime_seconds": state.get("uptime_seconds", 0),
        "avg_detections_per_frame": (
            state["total_detections"] / max(state["frames_processed"], 1)
        ),
    }


@router.post("/stop")
async def stop_stream():
    """Stop the current video stream."""
    if not _pipeline_state["running"]:
        return {"status": "not_running", "message": "No stream is currently active"}
    
    _pipeline_state["stop_requested"] = True
    _pipeline_state["running"] = False
    print("[STREAM] ⏹️ Stop requested via API")
    return {"status": "stopping", "message": "Stream stop requested"}


@router.get("/list")
async def list_videos():
    """List available video files in the data directory."""
    video_dir = settings.data_dir / "videos"
    
    if not video_dir.exists():
        return {"videos": []}
    
    videos = []
    for ext in ["*.mp4", "*.avi", "*.mkv", "*.webm"]:
        for f in video_dir.glob(ext):
            cap = cv2.VideoCapture(str(f))
            videos.append({
                "name": f.name,
                "path": str(f),
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            })
            cap.release()
    
    return {"videos": videos}


@router.websocket("/ws")
async def websocket_video_stream(websocket: WebSocket):
    """
    WebSocket endpoint for video streaming.
    Sends Base64-encoded JPEG frames to bypass browser connection limits.
    """
    global _active_connections
    
    await websocket.accept()
    print("[WS-STREAM] 📡 WebSocket client connected")
    
    # Load zones from database
    await load_zones_from_db()
    
    # Increment connection count and enable TTS
    async with _connections_lock:
        _active_connections += 1
        set_tts_paused(False)
    
    # Default video source
    video_path = str(settings.data_dir / "videos" / "SriLankan_Traffic_Video.mp4")
    if not Path(video_path).exists():
        videos_dir = Path(settings.data_dir) / "videos"
        if videos_dir.exists():
            video_files = list(videos_dir.glob("*.mp4"))
            if video_files:
                video_path = str(video_files[0])
            else:
                await websocket.close(code=1003, reason="No video files found")
                return
    
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    
    if not cap.isOpened():
        await websocket.close(code=1003, reason="Cannot open video")
        async with _connections_lock:
            _active_connections = max(0, _active_connections - 1)
            if _active_connections == 0:
                set_tts_paused(True)
        return
    
    # Load models
    vehicle_model = load_vehicle_model("cpu")
    plate_model = load_plate_model("cpu")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[WS-STREAM] ✅ Video opened: {total_frames} frames")
    
    _pipeline_state["running"] = True
    _pipeline_state["video_source"] = video_path
    _pipeline_state["start_time"] = time.time()
    
    frame_idx = 0
    frame_skip = 3
    target_fps = 20
    min_frame_time = 1.0 / target_fps
    
    try:
        while True:
            frame_start = time.time()
            
            # Skip frames for performance
            if frame_skip > 1:
                current_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos + frame_skip - 1)
            
            ret, frame = cap.read()
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue
            
            frame_idx += frame_skip
            
            # Detect and track
            result = detect_and_track(
                vehicle_model=vehicle_model,
                frame=frame,
                frame_id=frame_idx,
                confidence=0.5,
                plate_model=plate_model,
                run_plate_detection=True,
            )
            
            _pipeline_state["frames_processed"] += 1
            _pipeline_state["total_detections"] += len(result.detections)
            _pipeline_state["plates_detected"] += len(result.plate_boxes)
            
            # Draw detections
            frame = draw_detections(frame, result)
            frame = draw_frame_info(frame, result)
            
            # Resize for bandwidth
            scale = 0.75
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
            
            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            # Convert to Base64 and send
            base64_frame = base64.b64encode(buffer.tobytes()).decode('utf-8')
            await websocket.send_text(base64_frame)
            
            # Throttle to target FPS
            elapsed = time.time() - frame_start
            if elapsed < min_frame_time:
                await asyncio.sleep(min_frame_time - elapsed)
            
            # CRITICAL: Yield CPU to allow API requests (zones, logs) to be processed
            await asyncio.sleep(0.01)
    
    except WebSocketDisconnect:
        print("[WS-STREAM] 📴 WebSocket client disconnected")
    
    except Exception as e:
        print(f"[WS-STREAM] ❌ Error: {e}")
    
    finally:
        cap.release()
        async with _connections_lock:
            _active_connections = max(0, _active_connections - 1)
            print(f"[WS-STREAM] 📡 Client disconnected (remaining: {_active_connections})")
            if _active_connections == 0:
                set_tts_paused(True)
        reset_pipeline_state()
        print(f"[WS-STREAM] 🛑 Stream stopped. Processed {_pipeline_state['frames_processed']} frames")
