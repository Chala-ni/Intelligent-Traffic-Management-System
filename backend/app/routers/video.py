"""
Intelligent Traffic Management System - Video Streaming Router
MJPEG streaming with real-time YOLOv8 two-stage detection overlay

Sprint G (Revision): Uses "Zoom" detection pipeline:
- Stage 1: Vehicle tracking (wide view)
- Stage 2: Plate detection via cropping each vehicle (zoom view)
"""

import asyncio
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

import cv2
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.detection.yolo_detector import (
    load_vehicle_model,
    load_plate_model,
    detect_and_track,
    draw_detections,
    draw_frame_info,
    FrameResult,
    VEHICLE_CLASSES,
)
from app.routers.parking import get_detector  # import parking detector to overlay zones

settings = get_settings()
router = APIRouter(prefix="/video", tags=["Video"])

# Global state for pipeline control
_pipeline_state = {
    "running": False,
    "video_source": None,
    "model": None,
    "plate_model": None,
    "frames_processed": 0,
    "total_detections": 0,
    "plates_detected": 0,
    "start_time": None,
    "last_frame_time": None,
}


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
        "video_source": None,
        "frames_processed": 0,
        "total_detections": 0,
        "plates_detected": 0,
        "start_time": None,
        "last_frame_time": None,
    })


async def generate_mjpeg_frames(
    video_path: str,
    frame_skip: int = None,
    confidence: float = None,
    show_detections: bool = True,
    max_fps: float = 15.0,
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
    print(f"[STREAM] 🎬 Starting video stream: {video_path}")
    print(f"[STREAM]    frame_skip={frame_skip}, detect_plates={detect_plates_flag}")
    
    frame_skip = frame_skip or settings.frame_skip
    confidence = confidence or settings.detection_confidence
    min_frame_time = 1.0 / max_fps
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[STREAM] ❌ Cannot open video: {video_path}")
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
    
    try:
        while _pipeline_state["running"]:
            frame_start = time.time()
            
            ret, frame = cap.read()
            if not ret:
                # Loop video for continuous demo
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                continue
            
            # Process only every Nth frame for performance
            if frame_idx % frame_skip == 0:
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
                    if frame_idx % log_interval == 0:
                        print(f"[STREAM] Frame {frame_idx}: {len(result.detections)} vehicles, {len(result.plate_boxes)} plates")
                    
                    # Draw parking zones overlay (if available)
                    # Skip parking zones for now to avoid blocking
                    # try:
                    #     parking_detector = await get_detector()
                    #     if parking_detector:
                    #         frame = parking_detector.draw_zones(frame)
                    # except Exception:
                    #     pass

                    # Draw detections using new visualization API
                    frame = draw_detections(frame, result)
                    
                    # Add frame info overlay
                    frame = draw_frame_info(frame, result)
                
                # Resize for streaming (reduce bandwidth)
                scale = 0.75
                frame = cv2.resize(frame, None, fx=scale, fy=scale)
                
                # Encode to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # Yield as multipart MJPEG frame
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + 
                    buffer.tobytes() + 
                    b'\r\n'
                )
            
            frame_idx += 1
            
            # Throttle to max FPS
            elapsed = time.time() - frame_start
            if elapsed < min_frame_time:
                await asyncio.sleep(min_frame_time - elapsed)
                
    finally:
        print(f"[STREAM] 🛑 Stream stopped. Processed {_pipeline_state['frames_processed']} frames, {_pipeline_state['total_detections']} detections")
        cap.release()
        reset_pipeline_state()


@router.get("/stream")
async def stream_video(
    source: str = None,
    skip: int = None,
    confidence: float = None,
    detections: bool = True,
    detect_plates: bool = False,
):
    """
    Stream video with real-time YOLOv8 detection overlay (MJPEG).
    
    Args:
        source: Path to video file (default: sample video)
        skip: Process every Nth frame (default: 3)
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
    
    _pipeline_state["running"] = False
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
