"""
Intelligent Traffic Management System - YOLOv8 Advanced Detection Module
Sprint H+ (Final): Performance Optimized Detection with Full Feature Set

Features:
=========
1. Two-Stage Detection: Vehicle Tracking → Plate Detection (Zoom)
2. OCR Caching: Only run OCR every 2+ seconds per vehicle
3. Frame Skipping: Run YOLO every 2nd frame, reuse boxes on skipped frames
4. Speed Estimation: Calculate vehicle speed from centroid movement
5. Parking Violation: Warning phase (5s) → Penalty phase (15s) with TTS
6. Signal Automation: Update traffic light every 30 frames based on vehicle count
7. Optimized for Sri Lankan traffic (cars, motorcycles, tuk-tuks, buses, trucks)
"""

import sys
import time
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import cv2
import numpy as np

# Add parent to path for imports when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import get_settings

settings = get_settings()


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Frame skipping - only run YOLO every N frames (1 = every frame, 2 = every 2nd, etc.)
YOLO_DETECTION_INTERVAL: int = 2

# Plate detection interval (only run plate detection every N frames)
PLATE_DETECTION_INTERVAL: int = 3

# OCR cooldown per vehicle (seconds) - don't re-read same plate too often
OCR_COOLDOWN_SECONDS: float = 2.0

# Speed estimation
SPEED_SCALE_FACTOR: float = 0.5  # pixels to km/h conversion (adjust for camera)
SPEEDING_THRESHOLD: float = 80.0  # km/h - above this = speeding

# Parking violation timing
PARKING_WARNING_SECONDS: float = 5.0   # Warning phase starts
PARKING_VIOLATION_SECONDS: float = 15.0  # Violation/penalty phase

# Signal automation - update signal every N frames
SIGNAL_UPDATE_INTERVAL: int = 30  # ~1 second at 30fps

# History cleanup
PLATE_HISTORY_MAX_AGE: int = 30  # frames
TRACKING_HISTORY_MAX_AGE: int = 60  # frames


# ============================================================================
# GLOBAL STATE & CACHING
# ============================================================================

# Model cache to avoid reloading
_model_cache: Dict[str, Any] = {}

# Plate history: track_id -> {"bbox", "text", "timestamp", "frame_count"}
plate_history: Dict[int, Dict[str, Any]] = {}

# OCR cooldown: track_id -> last_ocr_time
ocr_cooldown: Dict[int, float] = {}

# Speed tracking: track_id -> {"prev_centroid", "prev_time", "speed", "is_speeding"}
speed_history: Dict[int, Dict[str, Any]] = {}

# Parking tracking: track_id -> {"entry_time", "zone_id", "warned", "penalized", "plate"}
parking_tracker: Dict[int, Dict[str, Any]] = {}

# Previous frame detections (for frame skipping)
_prev_detections: List[Any] = []
_prev_plate_boxes: List[Tuple[int, int, int, int]] = []

# Frame counter for optimization
_frame_counter: int = 0


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Detection:
    """Container for a single detection result with extended fields."""
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    centroid: Tuple[int, int]
    area: int
    timestamp: float = field(default_factory=time.time)
    has_plate: bool = False
    plate_bbox: Optional[Tuple[int, int, int, int]] = None
    plate_text: Optional[str] = None
    speed_kmh: float = 0.0
    is_speeding: bool = False
    parking_time: float = 0.0  # seconds in parking zone
    parking_status: str = ""   # "", "warning", "violation"
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 3),
            "bbox": self.bbox,
            "centroid": self.centroid,
            "area": self.area,
            "timestamp": self.timestamp,
            "has_plate": self.has_plate,
            "plate_bbox": self.plate_bbox,
            "plate_text": self.plate_text,
            "speed_kmh": round(self.speed_kmh, 1),
            "is_speeding": self.is_speeding,
            "parking_time": round(self.parking_time, 1),
            "parking_status": self.parking_status,
        }


@dataclass 
class FrameResult:
    """Container for detection results from a single frame."""
    frame_id: int
    timestamp: float
    detections: List[Detection]
    inference_time_ms: float
    plate_boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)
    image: Optional[np.ndarray] = None
    vehicle_count: int = 0
    speeding_count: int = 0
    parking_violations: int = 0
    signal_state: Optional[str] = None
    signal_duration: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "detection_count": len(self.detections),
            "plate_count": len(self.plate_boxes),
            "inference_time_ms": round(self.inference_time_ms, 2),
            "vehicle_count": self.vehicle_count,
            "speeding_count": self.speeding_count,
            "parking_violations": self.parking_violations,
            "signal_state": self.signal_state,
            "signal_duration": self.signal_duration,
            "detections": [d.to_dict() for d in self.detections],
        }


# ============================================================================
# CLASS DEFINITIONS
# ============================================================================

# Vehicle class IDs from COCO dataset (used by YOLOv8)
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle", 
    5: "bus",
    7: "truck",
}

TRAFFIC_CLASSES = {
    **VEHICLE_CLASSES,
    0: "person",
    1: "bicycle",
}

VEHICLE_CLASS_IDS = [2, 3, 5, 7]


# ============================================================================
# LAZY IMPORTS - Avoid circular imports and improve startup time
# ============================================================================

_ocr_service = None
_scoring_engine = None
_traffic_controller = None


def get_ocr_service():
    """Lazy load OCR service."""
    global _ocr_service
    if _ocr_service is None:
        try:
            from app.services.ocr_service import read_plate
            _ocr_service = read_plate
            print("✅ OCR service loaded")
        except ImportError as e:
            print(f"⚠️ OCR service not available: {e}")
            _ocr_service = lambda x: None
    return _ocr_service


def get_scoring_engine():
    """Lazy load scoring engine."""
    global _scoring_engine
    if _scoring_engine is None:
        try:
            from app.scoring import get_scoring_engine as _get_engine, ViolationType
            _scoring_engine = {"engine": _get_engine(), "ViolationType": ViolationType}
            print("✅ Scoring engine loaded")
        except ImportError as e:
            print(f"⚠️ Scoring engine not available: {e}")
            _scoring_engine = {"engine": None, "ViolationType": None}
    return _scoring_engine


def get_traffic_controller():
    """Lazy load traffic signal controller."""
    global _traffic_controller
    if _traffic_controller is None:
        try:
            from app.fuzzy.traffic_controller import get_signal
            _traffic_controller = get_signal()
            print("✅ Traffic controller loaded")
        except ImportError as e:
            print(f"⚠️ Traffic controller not available: {e}")
            _traffic_controller = None
    return _traffic_controller


# ============================================================================
# TEXT-TO-SPEECH WARNING SYSTEM
# ============================================================================

def speak_warning(message: str, use_tts: bool = False):
    """
    Speak a warning message or print if TTS not available.
    
    Args:
        message: Warning message to speak
        use_tts: Whether to attempt TTS (requires edge-tts)
    """
    # Always log to console
    print(f"[AUDIO] 🔊 {message}")
    
    if use_tts:
        try:
            import asyncio
            import edge_tts
            
            async def _speak():
                communicate = edge_tts.Communicate(message, "en-US-AriaNeural")
                await communicate.save("warning.mp3")
                # Play the audio (platform-specific)
                import os
                if sys.platform == "win32":
                    os.system("start /min warning.mp3")
                elif sys.platform == "darwin":
                    os.system("afplay warning.mp3 &")
                else:
                    os.system("mpg123 -q warning.mp3 &")
            
            asyncio.run(_speak())
        except Exception as e:
            print(f"⚠️ TTS failed: {e}")


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model(model_path: str, device: str = "cpu") -> Any:
    """Load a YOLOv8 model with caching."""
    global _model_cache
    
    cache_key = f"{model_path}_{device}"
    
    if cache_key not in _model_cache:
        from ultralytics import YOLO
        
        print(f"🔄 Loading model: {model_path} on {device}...")
        start = time.time()
        
        model = YOLO(model_path)
        model.to(device)
        
        load_time = time.time() - start
        print(f"✅ Model loaded in {load_time:.2f}s")
        
        _model_cache[cache_key] = model
    
    return _model_cache[cache_key]


def load_vehicle_model(device: str = "cpu") -> Any:
    """Load the YOLOv8 vehicle detection model."""
    return load_model("yolov8n.pt", device)


def load_plate_model(device: str = "cpu") -> Any:
    """Load the custom license plate detection model."""
    possible_paths = [
        Path("models") / "best_plate.pt",
        Path(__file__).parent.parent.parent.parent / "models" / "best_plate.pt",
        Path(settings.plate_model) if settings.plate_model else None,
    ]
    
    for path in possible_paths:
        if path and path.exists():
            print(f"📋 Found plate model at: {path}")
            return load_model(str(path), device)
    
    print(f"⚠️ Plate model not found, tried: {[str(p) for p in possible_paths if p]}")
    return None


def get_models(device: str = "cpu") -> Tuple[Any, Any]:
    """Initialize and return both models."""
    vehicle_model = load_vehicle_model(device)
    plate_model = load_plate_model(device)
    return vehicle_model, plate_model


# ============================================================================
# SPEED ESTIMATION
# ============================================================================

def calculate_speed(track_id: int, centroid: Tuple[int, int], current_time: float) -> Tuple[float, bool]:
    """
    Calculate vehicle speed from centroid movement between frames.
    
    Args:
        track_id: Vehicle tracking ID
        centroid: Current (x, y) centroid position
        current_time: Current timestamp
    
    Returns:
        Tuple of (speed_kmh, is_speeding)
    """
    global speed_history
    
    if track_id not in speed_history:
        # First sighting - initialize tracking
        speed_history[track_id] = {
            "prev_centroid": centroid,
            "prev_time": current_time,
            "speed": 0.0,
            "is_speeding": False,
            "frame_count": 0,
        }
        return 0.0, False
    
    history = speed_history[track_id]
    history["frame_count"] += 1
    
    # Calculate time delta
    time_delta = current_time - history["prev_time"]
    
    if time_delta < 0.01:  # Less than 10ms, skip
        return history["speed"], history["is_speeding"]
    
    # Calculate distance in pixels
    prev_x, prev_y = history["prev_centroid"]
    curr_x, curr_y = centroid
    
    distance_pixels = np.sqrt((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2)
    
    # Convert to speed: pixels/second → km/h (using scale factor)
    speed_pixels_per_sec = distance_pixels / time_delta
    speed_kmh = speed_pixels_per_sec * SPEED_SCALE_FACTOR
    
    # Smooth speed with exponential moving average
    alpha = 0.3  # Smoothing factor
    smoothed_speed = alpha * speed_kmh + (1 - alpha) * history["speed"]
    
    # Check if speeding
    is_speeding = smoothed_speed > SPEEDING_THRESHOLD
    
    # Update history
    history["prev_centroid"] = centroid
    history["prev_time"] = current_time
    history["speed"] = smoothed_speed
    history["is_speeding"] = is_speeding
    
    return smoothed_speed, is_speeding


def cleanup_speed_history(active_track_ids: set):
    """Remove speed history for vehicles no longer tracked."""
    global speed_history
    to_remove = [tid for tid in speed_history if tid not in active_track_ids]
    for tid in to_remove:
        if speed_history[tid]["frame_count"] > TRACKING_HISTORY_MAX_AGE:
            del speed_history[tid]


# ============================================================================
# PARKING VIOLATION DETECTION
# ============================================================================

def check_parking_violation(
    det: Detection,
    parking_zones: List[Any] = None,
    current_time: float = None,
) -> Tuple[float, str]:
    """
    Check if a vehicle is in a parking violation zone.
    
    Args:
        det: Detection object
        parking_zones: List of ParkingZone objects (optional)
        current_time: Current timestamp
    
    Returns:
        Tuple of (time_in_zone_seconds, status: "", "warning", "violation")
    """
    global parking_tracker
    
    if current_time is None:
        current_time = time.time()
    
    track_id = det.track_id
    
    # Simple zone check - for demo, use frame center as "no parking zone"
    # In production, this would use actual parking_zones from parking_detector
    in_zone = False
    zone_id = "demo_zone"
    
    # Demo: Check if vehicle is in bottom half of frame (simulated no-parking zone)
    # Replace with actual zone polygon checks in production
    _, y1, _, y2 = det.bbox
    centroid_y = det.centroid[1]
    
    # Simulate a "no parking zone" for demo purposes
    # In production: for zone in parking_zones: if zone.contains_centroid(det): ...
    # For now, we'll skip actual zone checking and use track-based simulation
    
    if track_id in parking_tracker:
        # Vehicle was already being tracked in zone
        entry = parking_tracker[track_id]
        time_in_zone = current_time - entry["entry_time"]
        
        # Determine status based on time
        if time_in_zone >= PARKING_VIOLATION_SECONDS:
            status = "violation"
            
            # Apply penalty if not already penalized
            if not entry.get("penalized", False):
                _apply_parking_penalty(
                    track_id=track_id,
                    plate_text=det.plate_text or entry.get("plate"),
                    zone_id=entry.get("zone_id", "unknown"),
                )
                entry["penalized"] = True
                
        elif time_in_zone >= PARKING_WARNING_SECONDS:
            status = "warning"
            
            # Speak warning if not already warned
            if not entry.get("warned", False):
                plate_display = det.plate_text or f"ID-{track_id}"
                speak_warning(f"Vehicle {plate_display}, please move. You are in a no parking zone.")
                entry["warned"] = True
        else:
            status = ""
        
        # Update plate if we have a new reading
        if det.plate_text and not entry.get("plate"):
            entry["plate"] = det.plate_text
        
        return time_in_zone, status
    else:
        # Vehicle just entered (or we're simulating for demo)
        # In demo mode, only start tracking after vehicle is "stationary" (speed < 5 km/h)
        if det.speed_kmh < 5.0 and det.speed_kmh >= 0:
            parking_tracker[track_id] = {
                "entry_time": current_time,
                "zone_id": zone_id,
                "warned": False,
                "penalized": False,
                "plate": det.plate_text,
            }
        return 0.0, ""


def _apply_parking_penalty(track_id: int, plate_text: str, zone_id: str):
    """Apply parking violation penalty to scoring system."""
    scoring = get_scoring_engine()
    
    if scoring["engine"] is None:
        print(f"[PENALTY] ⚠️ Scoring not available. Would penalize: {plate_text or track_id}")
        return
    
    driver_id = plate_text or f"UNKNOWN-{track_id}"
    ViolationType = scoring["ViolationType"]
    
    try:
        driver, violation = scoring["engine"].record_violation(
            driver_id=driver_id,
            violation_type=ViolationType.PARKING_NO_PARKING,
            location=f"Zone: {zone_id}",
            license_plate=plate_text,
            notes="Automated detection - illegal parking",
        )
        print(f"[PENALTY] 🚨 Violation recorded: {driver_id} | Score: {driver.current_score} | Fine: ${violation.fine_amount}")
        
        # Speak violation notice
        speak_warning(f"Violation recorded for vehicle {driver_id}. Fine issued.")
        
    except Exception as e:
        print(f"[PENALTY] Error recording violation: {e}")


def cleanup_parking_tracker(active_track_ids: set):
    """Remove parking entries for vehicles no longer tracked."""
    global parking_tracker
    to_remove = [tid for tid in parking_tracker if tid not in active_track_ids]
    for tid in to_remove:
        del parking_tracker[tid]


# ============================================================================
# SIGNAL AUTOMATION
# ============================================================================

def update_traffic_signal(vehicle_count: int, frame_id: int) -> Tuple[Optional[str], Optional[int]]:
    """
    Update traffic signal based on vehicle count.
    
    Called every SIGNAL_UPDATE_INTERVAL frames.
    
    Args:
        vehicle_count: Number of vehicles detected
        frame_id: Current frame number
    
    Returns:
        Tuple of (signal_state, green_duration) or (None, None) if not updated
    """
    if frame_id % SIGNAL_UPDATE_INTERVAL != 0:
        return None, None
    
    controller = get_traffic_controller()
    
    if controller is None:
        return None, None
    
    try:
        # Update timing based on vehicle count
        recommendation = controller.update_timing(vehicle_count)
        
        state = controller.state
        duration = controller.green_duration
        
        print(f"[SIGNAL] 🚦 Count={vehicle_count} | State={state} | Green={duration}s | Level={recommendation.get('traffic_level', 'unknown')}")
        
        return state, duration
        
    except Exception as e:
        print(f"[SIGNAL] Error updating: {e}")
        return None, None


# ============================================================================
# STAGE 1: VEHICLE TRACKING (WITH FRAME SKIPPING)
# ============================================================================

def track_vehicles(
    model: Any,
    frame: np.ndarray,
    confidence: float = 0.5,
    frame_id: int = 0,
) -> Tuple[List[Detection], bool]:
    """
    Stage 1: Run vehicle detection with tracking and frame skipping.
    
    Uses YOLOv8's built-in tracker with persist=True.
    Optimization: Only runs YOLO every YOLO_DETECTION_INTERVAL frames.
    
    Args:
        model: Loaded YOLO vehicle model
        frame: Input image (BGR format)
        confidence: Minimum confidence threshold
        frame_id: Current frame number
    
    Returns:
        Tuple of (detections, was_detection_run)
    """
    global _prev_detections
    
    # Frame skipping optimization
    run_detection = (frame_id % YOLO_DETECTION_INTERVAL == 0)
    
    if not run_detection and _prev_detections:
        # Return cached detections from previous frame
        return _prev_detections, False
    
    # Run tracking on vehicle classes
    results = model.track(
        source=frame,
        conf=confidence,
        classes=VEHICLE_CLASS_IDS,
        persist=True,
        verbose=False,
    )
    
    detections = []
    current_time = time.time()
    
    if results and len(results) > 0:
        result = results[0]
        
        if result.boxes is not None:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                
                if boxes.id is not None:
                    track_id = int(boxes.id[i].cpu().numpy())
                else:
                    track_id = -1
                
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                area = (x2 - x1) * (y2 - y1)
                class_name = VEHICLE_CLASSES.get(cls_id, f"class_{cls_id}")
                
                # Calculate speed for this vehicle
                speed, is_speeding = calculate_speed(track_id, centroid, current_time)
                
                detection = Detection(
                    track_id=track_id,
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    centroid=centroid,
                    area=area,
                    timestamp=current_time,
                    speed_kmh=speed,
                    is_speeding=is_speeding,
                )
                detections.append(detection)
    
    # Cache detections
    _prev_detections = detections
    
    # Cleanup old tracking data
    active_ids = {d.track_id for d in detections}
    cleanup_speed_history(active_ids)
    cleanup_parking_tracker(active_ids)
    
    return detections, True


# ============================================================================
# STAGE 2: PLATE DETECTION WITH OCR CACHING
# ============================================================================

def detect_plates_in_crops(
    plate_model: Any,
    frame: np.ndarray,
    vehicle_detections: List[Detection],
    confidence: float = 0.2,
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, Dict[str, Any]]]:
    """
    Stage 2: Detect plates with OCR caching.
    
    Features:
    - Geometric filter: Ignore plates in top 30% of vehicle
    - OCR cooldown: Only run OCR every 2+ seconds per vehicle
    - Text caching: Remember plate text for tracked vehicles
    
    Args:
        plate_model: Loaded plate detection model
        frame: Full input image
        vehicle_detections: List of vehicle detections from Stage 1
        confidence: Detection confidence threshold
    
    Returns:
        Tuple of (all_plate_boxes, vehicle_plate_map)
    """
    global plate_history, ocr_cooldown
    
    if plate_model is None:
        return [], {}
    
    all_plates = []
    vehicle_plate_map = {}
    
    read_plate = get_ocr_service()
    current_time = time.time()
    
    for det in vehicle_detections:
        vx1, vy1, vx2, vy2 = det.bbox
        
        # Ensure valid crop coordinates
        h, w = frame.shape[:2]
        vx1 = max(0, vx1)
        vy1 = max(0, vy1)
        vx2 = min(w, vx2)
        vy2 = min(h, vy2)
        
        crop_w = vx2 - vx1
        crop_h = vy2 - vy1
        if crop_w < 50 or crop_h < 50:
            continue
        
        vehicle_crop = frame[vy1:vy2, vx1:vx2]
        
        # Run plate detection
        results = plate_model.predict(
            source=vehicle_crop,
            conf=confidence,
            verbose=False,
        )
        
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                px1, py1, px2, py2 = map(int, xyxy)
                
                # GEOMETRIC FILTER: Ignore plates in top 30%
                plate_center_y = (py1 + py2) // 2
                if plate_center_y < (crop_h * 0.3):
                    continue
                
                # Convert to real frame coordinates
                real_px1 = vx1 + px1
                real_py1 = vy1 + py1
                real_px2 = vx1 + px2
                real_py2 = vy1 + py2
                
                plate_bbox = (real_px1, real_py1, real_px2, real_py2)
                
                # OCR CACHING: Check cooldown
                plate_text = None
                should_run_ocr = True
                
                track_id = det.track_id
                
                # Check if we have a cached plate text
                if track_id in plate_history and plate_history[track_id].get("text"):
                    # We have cached text
                    plate_text = plate_history[track_id]["text"]
                    
                    # Check if cooldown expired
                    last_ocr_time = ocr_cooldown.get(track_id, 0)
                    if (current_time - last_ocr_time) < OCR_COOLDOWN_SECONDS:
                        should_run_ocr = False  # Use cached text
                
                # Run OCR if needed
                if should_run_ocr:
                    plate_crop = vehicle_crop[py1:py2, px1:px2]
                    if plate_crop.size > 0:
                        new_text = read_plate(plate_crop)
                        if new_text:
                            plate_text = new_text
                            ocr_cooldown[track_id] = current_time
                
                all_plates.append(plate_bbox)
                
                vehicle_plate_map[track_id] = {
                    "bbox": plate_bbox,
                    "text": plate_text,
                }
                
                # Update plate history
                plate_history[track_id] = {
                    "bbox": plate_bbox,
                    "text": plate_text,
                    "timestamp": current_time,
                    "frame_count": 0,
                }
                
                break  # One plate per vehicle
    
    return all_plates, vehicle_plate_map


def update_plate_history(vehicle_detections: List[Detection]) -> Dict[int, Dict[str, Any]]:
    """Update plate history and return plates from memory."""
    global plate_history
    
    current_track_ids = {det.track_id for det in vehicle_detections}
    remembered_plates = {}
    
    to_remove = []
    for track_id, info in plate_history.items():
        info["frame_count"] += 1
        
        if track_id in current_track_ids and info["frame_count"] < PLATE_HISTORY_MAX_AGE:
            remembered_plates[track_id] = {
                "bbox": info["bbox"],
                "text": info.get("text"),
            }
        
        if info["frame_count"] >= PLATE_HISTORY_MAX_AGE:
            to_remove.append(track_id)
    
    for track_id in to_remove:
        del plate_history[track_id]
        if track_id in ocr_cooldown:
            del ocr_cooldown[track_id]
    
    return remembered_plates


# ============================================================================
# TWO-STAGE DETECTION PIPELINE (MAIN)
# ============================================================================

def detect_and_track(
    vehicle_model: Any,
    frame: np.ndarray,
    frame_id: int = 0,
    confidence: float = 0.5,
    plate_model: Any = None,
    run_plate_detection: bool = True,
    parking_zones: List[Any] = None,
) -> FrameResult:
    """
    Run the complete optimized two-stage detection pipeline.
    
    Features:
    - Frame skipping for YOLO (every 2nd frame)
    - OCR caching (2s cooldown per vehicle)
    - Speed estimation
    - Parking violation detection
    - Signal automation
    
    Args:
        vehicle_model: Loaded YOLO vehicle model
        frame: Input image (BGR format)
        frame_id: Frame identifier
        confidence: Vehicle detection confidence
        plate_model: Loaded plate detection model
        run_plate_detection: Enable plate detection
        parking_zones: List of parking zones
    
    Returns:
        FrameResult with all detection info
    """
    global _frame_counter, _prev_plate_boxes
    
    timestamp = time.time()
    start_time = time.time()
    
    # ========== STAGE 1: VEHICLE TRACKING ==========
    detections, detection_ran = track_vehicles(
        vehicle_model, frame, confidence, _frame_counter
    )
    
    # ========== STAGE 2: PLATE DETECTION ==========
    all_plates = []
    vehicle_plate_map = {}
    
    if run_plate_detection and plate_model is not None:
        # Only run plate detection every N frames
        if _frame_counter % PLATE_DETECTION_INTERVAL == 0:
            all_plates, vehicle_plate_map = detect_plates_in_crops(
                plate_model, frame, detections, confidence=0.2
            )
            _prev_plate_boxes = all_plates
        else:
            # Use cached plate boxes
            all_plates = _prev_plate_boxes
        
        # Get remembered plates
        remembered_plates = update_plate_history(detections)
        
        # Merge: current takes priority
        for track_id, plate_info in remembered_plates.items():
            if track_id not in vehicle_plate_map:
                vehicle_plate_map[track_id] = plate_info
                if plate_info["bbox"] not in all_plates:
                    all_plates.append(plate_info["bbox"])
    
    # ========== ENRICH DETECTIONS ==========
    speeding_count = 0
    parking_violations = 0
    
    for det in detections:
        # Add plate info
        if det.track_id in vehicle_plate_map:
            plate_info = vehicle_plate_map[det.track_id]
            det.has_plate = True
            det.plate_bbox = plate_info["bbox"]
            det.plate_text = plate_info.get("text")
        
        # Count speeders
        if det.is_speeding:
            speeding_count += 1
        
        # Check parking violations
        parking_time, parking_status = check_parking_violation(det, parking_zones, timestamp)
        det.parking_time = parking_time
        det.parking_status = parking_status
        
        if parking_status == "violation":
            parking_violations += 1
    
    # ========== SIGNAL AUTOMATION ==========
    vehicle_count = len(detections)
    signal_state, signal_duration = update_traffic_signal(vehicle_count, _frame_counter)
    
    _frame_counter += 1
    inference_time = (time.time() - start_time) * 1000
    
    return FrameResult(
        frame_id=frame_id,
        timestamp=timestamp,
        detections=detections,
        inference_time_ms=inference_time,
        plate_boxes=all_plates,
        image=frame,
        vehicle_count=vehicle_count,
        speeding_count=speeding_count,
        parking_violations=parking_violations,
        signal_state=signal_state,
        signal_duration=signal_duration,
    )


# ============================================================================
# VISUALIZATION
# ============================================================================

def draw_detections(
    frame: np.ndarray,
    result: FrameResult,
    show_labels: bool = True,
    show_track_id: bool = True,
    show_speed: bool = True,
    box_thickness: int = 2,
) -> np.ndarray:
    """
    Draw detection boxes, plates, speed, and labels on frame.
    
    Visual elements:
    - Green boxes: Normal vehicles
    - Red boxes: Speeding vehicles
    - Orange boxes: Parking warning
    - Magenta boxes: Parking violation
    - Cyan boxes: License plates
    - Speed text above vehicle box
    """
    annotated = frame.copy()
    
    colors = {
        "car": (0, 255, 0),
        "motorcycle": (0, 200, 255),
        "bus": (255, 100, 0),
        "truck": (255, 0, 255),
        "speeding": (0, 0, 255),       # Red
        "warning": (0, 165, 255),      # Orange
        "violation": (255, 0, 255),    # Magenta
    }
    plate_color = (255, 255, 0)  # Cyan
    
    # Draw plate boxes
    for px1, py1, px2, py2 in result.plate_boxes:
        cv2.rectangle(annotated, (px1, py1), (px2, py2), plate_color, box_thickness)
    
    # Draw vehicle boxes and labels
    for det in result.detections:
        x1, y1, x2, y2 = det.bbox
        
        # Choose color based on status
        if det.parking_status == "violation":
            color = colors["violation"]
        elif det.parking_status == "warning":
            color = colors["warning"]
        elif det.is_speeding:
            color = colors["speeding"]
        else:
            color = colors.get(det.class_name, (0, 255, 0))
        
        # Draw vehicle box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, box_thickness)
        
        # Draw speed above box
        if show_speed and det.speed_kmh > 0:
            speed_text = f"{det.speed_kmh:.0f} km/h"
            if det.is_speeding:
                speed_text += " SPEEDING!"
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (tw, th), _ = cv2.getTextSize(speed_text, font, font_scale, thickness)
            
            speed_color = (0, 0, 255) if det.is_speeding else (255, 255, 255)
            cv2.rectangle(annotated, (x1, y1 - th - 25), (x1 + tw + 4, y1 - 15), (0, 0, 0), -1)
            cv2.putText(annotated, speed_text, (x1 + 2, y1 - 18), font, font_scale, speed_color, thickness)
        
        # Build label
        if show_labels or show_track_id:
            label_parts = []
            
            if show_track_id and det.track_id >= 0:
                label_parts.append(f"ID:{det.track_id}")
            
            if show_labels:
                label_parts.append(det.class_name)
            
            label = " | ".join(label_parts)
            
            # Add plate text or parking status
            if det.plate_text:
                label += f" | {det.plate_text}"
            elif det.has_plate:
                label += " [Plate]"
            
            if det.parking_status:
                label += f" | {det.parking_status.upper()}: {det.parking_time:.0f}s"
            
            # Draw label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
            
            bg_color = color
            cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 4, y1), bg_color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 5), font, font_scale, (255, 255, 255), thickness)
    
    return annotated


def draw_frame_info(
    frame: np.ndarray,
    result: FrameResult,
    extra_info: str = "",
) -> np.ndarray:
    """Draw frame information overlay."""
    info_parts = [
        f"Frame: {result.frame_id}",
        f"Vehicles: {result.vehicle_count}",
        f"Plates: {len(result.plate_boxes)}",
        f"Speeding: {result.speeding_count}",
        f"Parking: {result.parking_violations}",
        f"{result.inference_time_ms:.0f}ms",
    ]
    
    if result.signal_state:
        info_parts.append(f"Signal: {result.signal_state.upper()}")
    
    if extra_info:
        info_parts.append(extra_info)
    
    info_text = " | ".join(info_parts)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    (tw, th), _ = cv2.getTextSize(info_text, font, font_scale, thickness)
    
    cv2.rectangle(frame, (5, 5), (tw + 15, th + 15), (0, 0, 0), -1)
    cv2.putText(frame, info_text, (10, th + 8), font, font_scale, (0, 255, 0), thickness)
    
    return frame


# ============================================================================
# VIDEO PROCESSING GENERATOR
# ============================================================================

def process_video(
    video_path: str,
    vehicle_model: Any = None,
    plate_model: Any = None,
    confidence: float = 0.5,
    skip_frames: int = 0,
    max_frames: Optional[int] = None,
    enable_plate_detection: bool = True,
) -> Generator[FrameResult, None, None]:
    """Process a video file with optimized two-stage detection."""
    global _frame_counter, _prev_detections, _prev_plate_boxes
    
    # Reset global state
    _frame_counter = 0
    _prev_detections = []
    _prev_plate_boxes = []
    
    if vehicle_model is None:
        vehicle_model = load_vehicle_model()
    if plate_model is None and enable_plate_detection:
        plate_model = load_plate_model()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    frame_id = 0
    processed = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if skip_frames > 0 and frame_id % (skip_frames + 1) != 0:
                frame_id += 1
                continue
            
            result = detect_and_track(
                vehicle_model=vehicle_model,
                frame=frame,
                frame_id=frame_id,
                confidence=confidence,
                plate_model=plate_model,
                run_plate_detection=enable_plate_detection,
            )
            
            yield result
            
            processed += 1
            frame_id += 1
            
            if max_frames and processed >= max_frames:
                break
                
    finally:
        cap.release()


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

def detect_plates(
    plate_model: Any,
    frame: np.ndarray,
    vehicle_detections: List[Detection],
    confidence: float = 0.3,
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, Tuple[int, int, int, int]]]:
    """Legacy function for plate detection."""
    plates, plate_map = detect_plates_in_crops(plate_model, frame, vehicle_detections, confidence)
    # Convert to legacy format
    legacy_map = {tid: info["bbox"] for tid, info in plate_map.items()}
    return plates, legacy_map


# ============================================================================
# RESET FUNCTION (for new video sessions)
# ============================================================================

def reset_state():
    """Reset all global tracking state. Call when starting a new video."""
    global _frame_counter, _prev_detections, _prev_plate_boxes
    global plate_history, ocr_cooldown, speed_history, parking_tracker
    
    _frame_counter = 0
    _prev_detections = []
    _prev_plate_boxes = []
    plate_history.clear()
    ocr_cooldown.clear()
    speed_history.clear()
    parking_tracker.clear()
    
    print("🔄 Detection state reset")


# ============================================================================
# MAIN - Standalone testing
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimized Two-Stage Detection")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--no-plates", action="store_true")
    parser.add_argument("--display", action="store_true")
    args = parser.parse_args()
    
    print("🚀 Initializing Optimized Detection Pipeline...")
    print(f"   YOLO Interval: Every {YOLO_DETECTION_INTERVAL} frames")
    print(f"   Plate Interval: Every {PLATE_DETECTION_INTERVAL} frames")
    print(f"   OCR Cooldown: {OCR_COOLDOWN_SECONDS}s")
    print(f"   Speeding Threshold: {SPEEDING_THRESHOLD} km/h")
    
    vehicle_model, plate_model = get_models()
    
    if args.video:
        video_path = args.video
    else:
        video_path = str(Path(__file__).parent.parent.parent.parent / "data" / "videos" / "traffic_sample.mp4")
    
    print(f"📹 Processing: {video_path}")
    
    reset_state()
    
    for result in process_video(
        video_path,
        vehicle_model=vehicle_model,
        plate_model=plate_model if not args.no_plates else None,
        confidence=args.confidence,
        enable_plate_detection=not args.no_plates,
    ):
        annotated = draw_detections(result.image, result)
        annotated = draw_frame_info(annotated, result)
        
        print(f"Frame {result.frame_id}: V={result.vehicle_count} P={len(result.plate_boxes)} S={result.speeding_count} {result.inference_time_ms:.1f}ms")
        
        if args.display:
            cv2.imshow("Optimized Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    if args.display:
        cv2.destroyAllWindows()
    
    print("✅ Processing complete!")
