"""
Intelligent Traffic Management System - YOLOv8 Two-Stage Detection Module
Sprint G (Revision): "Zoom" Detection Pipeline

Stage 1: Vehicle Tracking (Wide View) - Detect and track vehicles
Stage 2: Plate Detection (Zoom View) - Crop each vehicle and detect plates

Optimized for Sri Lankan traffic with support for cars, motorcycles/tuk-tuks, buses, trucks.
"""

import sys
import time
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import cv2
import numpy as np
import os

# Add parent to path for imports when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import get_settings

settings = get_settings()

# ============================================================================
# GLOBAL STATE & CACHING
# ============================================================================

# Model cache to avoid reloading
_model_cache: Dict[str, Any] = {}

# Plate history: track_id -> {"bbox": (x1,y1,x2,y2), "timestamp": float, "frame_count": int}
# This remembers which vehicles have plates even when we skip detection frames
plate_history: Dict[int, Dict[str, Any]] = {}

# Frame counter for optimization (only run plate detection every N frames)
_frame_counter: int = 0
PLATE_DETECTION_INTERVAL: int = 3  # Run plate detection every 3 frames

# History cleanup: remove entries older than this many frames
PLATE_HISTORY_MAX_AGE: int = 30


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Detection:
    """Container for a single detection result."""
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    centroid: Tuple[int, int]
    area: int
    timestamp: float = field(default_factory=time.time)
    has_plate: bool = False  # True if a plate was detected for this vehicle
    plate_bbox: Optional[Tuple[int, int, int, int]] = None  # Plate bounding box (real coords)
    
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
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "detection_count": len(self.detections),
            "plate_count": len(self.plate_boxes),
            "inference_time_ms": round(self.inference_time_ms, 2),
            "detections": [d.to_dict() for d in self.detections],
        }


# ============================================================================
# CLASS DEFINITIONS
# ============================================================================

# Vehicle class IDs from COCO dataset (used by YOLOv8)
# Classes for Sri Lankan traffic:
# 2 = Car
# 3 = Motorcycle (Tuk-tuks often detected as this)
# 5 = Bus
# 7 = Truck
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle", 
    5: "bus",
    7: "truck",
}

# All relevant classes for traffic monitoring
TRAFFIC_CLASSES = {
    **VEHICLE_CLASSES,
    0: "person",
    1: "bicycle",
}

# Class IDs list for vehicle tracking
VEHICLE_CLASS_IDS = [2, 3, 5, 7]


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model(model_path: str, device: str = "cpu") -> Any:
    """
    Load a YOLOv8 model with caching.
    
    Args:
        model_path: Path to model weights or model name (e.g., "yolov8n.pt")
        device: Device to run on ("cpu", "cuda", "mps")
    
    Returns:
        Loaded YOLO model
    """
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
    # Check multiple locations for the model
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
    """
    Initialize and return both models.
    
    Returns:
        Tuple of (vehicle_model, plate_model)
    """
    vehicle_model = load_vehicle_model(device)
    plate_model = load_plate_model(device)
    return vehicle_model, plate_model


# ============================================================================
# STAGE 1: VEHICLE TRACKING (WIDE VIEW)
# ============================================================================

def track_vehicles(
    model: Any,
    frame: np.ndarray,
    confidence: float = 0.5,
) -> List[Detection]:
    """
    Stage 1: Run vehicle detection with tracking.
    
    Uses YOLOv8's built-in tracker with persist=True to maintain
    consistent track IDs across frames.
    
    Args:
        model: Loaded YOLO vehicle model
        frame: Input image (BGR format from OpenCV)
        confidence: Minimum confidence threshold
    
    Returns:
        List of Detection objects with track IDs
    """
    # Run tracking on vehicle classes only
    results = model.track(
        source=frame,
        conf=confidence,
        classes=VEHICLE_CLASS_IDS,  # [2, 3, 5, 7] = car, motorcycle, bus, truck
        persist=True,  # Maintain track IDs across frames
        verbose=False,
    )
    
    detections = []
    
    if results and len(results) > 0:
        result = results[0]
        
        if result.boxes is not None:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                # Get bounding box
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                
                # Get confidence and class
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                
                # Get track ID
                if boxes.id is not None:
                    track_id = int(boxes.id[i].cpu().numpy())
                else:
                    track_id = -1
                
                # Calculate centroid and area
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                area = (x2 - x1) * (y2 - y1)
                
                # Get class name
                class_name = VEHICLE_CLASSES.get(cls_id, f"class_{cls_id}")
                
                detection = Detection(
                    track_id=track_id,
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    centroid=centroid,
                    area=area,
                )
                detections.append(detection)
    
    return detections


# ============================================================================
# STAGE 2: PLATE DETECTION (ZOOM VIEW)
# ============================================================================

def detect_plates_in_crops(
    plate_model: Any,
    frame: np.ndarray,
    vehicle_detections: List[Detection],
    confidence: float = 0.2,  # Low confidence to catch more plates
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, Tuple[int, int, int, int]]]:
    """
    Stage 2: Detect plates by cropping each vehicle and running plate detection.
    
    This "zoom" approach gives the plate model a closer view of each vehicle,
    significantly improving detection accuracy for smaller plates.
    
    Args:
        plate_model: Loaded plate detection model
        frame: Full input image
        vehicle_detections: List of vehicle detections from Stage 1
        confidence: Detection confidence threshold (lower = more detections)
    
    Returns:
        Tuple of (all_plate_boxes, vehicle_plate_map)
        - all_plate_boxes: List of plate bboxes in REAL frame coordinates
        - vehicle_plate_map: Dict mapping track_id to plate bbox
    """
    global plate_history
    
    if plate_model is None:
        return [], {}
    
    all_plates = []
    vehicle_plate_map = {}
    
    for det in vehicle_detections:
        vx1, vy1, vx2, vy2 = det.bbox
        
        # Ensure valid crop coordinates
        h, w = frame.shape[:2]
        vx1 = max(0, vx1)
        vy1 = max(0, vy1)
        vx2 = min(w, vx2)
        vy2 = min(h, vy2)
        
        # Skip if crop is too small
        crop_w = vx2 - vx1
        crop_h = vy2 - vy1
        if crop_w < 50 or crop_h < 50:
            continue
        
        # Crop the vehicle from the frame
        vehicle_crop = frame[vy1:vy2, vx1:vx2]
        # DEBUG: Save the crop to see if it's correct
        os.makedirs("debug_crops", exist_ok=True)
        cv2.imwrite(f"debug_crops/crop_{det.track_id}.jpg", vehicle_crop)
        
        # Run plate detection on the cropped vehicle image
        results = plate_model.predict(
            source=vehicle_crop,
            conf=confidence,
            verbose=False,
        )
        
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            for i in range(len(boxes)):
                # Get plate bbox in CROP coordinates
                xyxy = boxes.xyxy[i].cpu().numpy()
                px1, py1, px2, py2 = map(int, xyxy)
                
                # COORDINATE MAPPING: Convert crop coords to real frame coords
                # Plate_Real = Vehicle_Origin + Plate_Crop
                real_px1 = vx1 + px1
                real_py1 = vy1 + py1
                real_px2 = vx1 + px2
                real_py2 = vy1 + py2
                
                plate_bbox = (real_px1, real_py1, real_px2, real_py2)
                all_plates.append(plate_bbox)
                
                # Associate plate with this vehicle
                vehicle_plate_map[det.track_id] = plate_bbox
                
                # Update plate history for this vehicle
                plate_history[det.track_id] = {
                    "bbox": plate_bbox,
                    "timestamp": time.time(),
                    "frame_count": 0,  # Reset frame count
                }
                
                # Only take the first plate per vehicle
                break
    
    return all_plates, vehicle_plate_map


def update_plate_history(vehicle_detections: List[Detection]) -> Dict[int, Tuple[int, int, int, int]]:
    """
    Update plate history and return plates from memory for vehicles we're still tracking.
    
    This allows us to show "Plate Detected" even on frames where we skip plate detection.
    
    Args:
        vehicle_detections: Current frame's vehicle detections
    
    Returns:
        Dict mapping track_id to plate bbox from history
    """
    global plate_history
    
    current_track_ids = {det.track_id for det in vehicle_detections}
    remembered_plates = {}
    
    # Increment frame count and collect remembered plates
    to_remove = []
    for track_id, info in plate_history.items():
        info["frame_count"] += 1
        
        # If vehicle is still visible and history is fresh, use remembered plate
        if track_id in current_track_ids and info["frame_count"] < PLATE_HISTORY_MAX_AGE:
            remembered_plates[track_id] = info["bbox"]
        
        # Mark old entries for removal
        if info["frame_count"] >= PLATE_HISTORY_MAX_AGE:
            to_remove.append(track_id)
    
    # Clean up old entries
    for track_id in to_remove:
        del plate_history[track_id]
    
    return remembered_plates


# ============================================================================
# TWO-STAGE DETECTION PIPELINE
# ============================================================================

def detect_and_track(
    vehicle_model: Any,
    frame: np.ndarray,
    frame_id: int = 0,
    confidence: float = 0.5,
    plate_model: Any = None,
    run_plate_detection: bool = True,
) -> FrameResult:
    """
    Run the complete two-stage detection pipeline.
    
    Stage 1: Vehicle tracking (every frame)
    Stage 2: Plate detection via cropping (every N frames for optimization)
    
    Args:
        vehicle_model: Loaded YOLO vehicle model
        frame: Input image (BGR format from OpenCV)
        frame_id: Frame identifier
        confidence: Vehicle detection confidence threshold
        plate_model: Loaded plate detection model (optional)
        run_plate_detection: Whether to enable plate detection
    
    Returns:
        FrameResult with detections and plate information
    """
    global _frame_counter
    
    timestamp = time.time()
    start_time = time.time()
    
    # ========== STAGE 1: VEHICLE TRACKING ==========
    detections = track_vehicles(vehicle_model, frame, confidence)
    
    # ========== STAGE 2: PLATE DETECTION (ZOOM) ==========
    all_plates = []
    vehicle_plate_map = {}
    
    if run_plate_detection and plate_model is not None:
        # Optimization: Only run plate detection every N frames
        if _frame_counter % PLATE_DETECTION_INTERVAL == 0:
            all_plates, vehicle_plate_map = detect_plates_in_crops(
                plate_model, frame, detections, confidence=0.2
            )
        
        # Get remembered plates from history (for frames we skip)
        remembered_plates = update_plate_history(detections)
        
        # Merge: Current detections take priority, then history
        for track_id, bbox in remembered_plates.items():
            if track_id not in vehicle_plate_map:
                vehicle_plate_map[track_id] = bbox
                all_plates.append(bbox)
    
    # Update detections with plate info
    for det in detections:
        if det.track_id in vehicle_plate_map:
            det.has_plate = True
            det.plate_bbox = vehicle_plate_map[det.track_id]
    
    _frame_counter += 1
    inference_time = (time.time() - start_time) * 1000  # ms
    
    return FrameResult(
        frame_id=frame_id,
        timestamp=timestamp,
        detections=detections,
        inference_time_ms=inference_time,
        plate_boxes=all_plates,
        image=frame,
    )


# ============================================================================
# VISUALIZATION
# ============================================================================

def draw_detections(
    frame: np.ndarray,
    result: FrameResult,
    show_labels: bool = True,
    show_track_id: bool = True,
    box_thickness: int = 2,
) -> np.ndarray:
    """
    Draw detection boxes, plate boxes, and labels on a frame.
    
    - Green boxes: Vehicles
    - Cyan boxes: License plates
    - Label format: "ID: X | class_name [Plate!]"
    
    Args:
        frame: Input image
        result: FrameResult from detect_and_track
        show_labels: Whether to show class labels
        show_track_id: Whether to show track IDs
        box_thickness: Line thickness for boxes
    
    Returns:
        Annotated image
    """
    annotated = frame.copy()
    
    # Color palette
    vehicle_color = (0, 255, 0)      # Green for vehicles
    plate_color = (255, 255, 0)       # Cyan for plates
    plate_label_bg = (255, 100, 0)    # Cyan-ish background for "Plate Detected" labels
    
    colors = {
        "car": (0, 255, 0),           # Green
        "motorcycle": (0, 200, 255),  # Orange
        "bus": (255, 100, 0),         # Blue-ish
        "truck": (255, 0, 255),       # Magenta
    }
    
    # Draw plate boxes first (so vehicle boxes can overlay if needed)
    for px1, py1, px2, py2 in result.plate_boxes:
        cv2.rectangle(annotated, (px1, py1), (px2, py2), plate_color, box_thickness)
    
    # Draw vehicle boxes and labels
    for det in result.detections:
        x1, y1, x2, y2 = det.bbox
        color = colors.get(det.class_name, vehicle_color)
        
        # Draw vehicle box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, box_thickness)
        
        # Build label text: "ID: X | class_name [Plate!]"
        if show_labels or show_track_id:
            label_parts = []
            
            if show_track_id and det.track_id >= 0:
                label_parts.append(f"ID:{det.track_id}")
            
            if show_labels:
                label_parts.append(det.class_name)
                label_parts.append(f"{det.confidence:.2f}")
            
            # Add plate indicator
            if det.has_plate:
                label_parts.append("[Plate!]")
            
            label = " | ".join(label_parts[:2])  # "ID:X | car"
            if len(label_parts) > 2:
                label += f" {label_parts[2]}"    # confidence
            if det.has_plate:
                label += " [Plate!]"
            
            # Draw label background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # Use different background color if plate detected
            bg_color = plate_label_bg if det.has_plate else color
            
            cv2.rectangle(annotated, (x1, y1 - text_h - 10), (x1 + text_w + 4, y1), bg_color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 5), font, font_scale, (255, 255, 255), thickness)
    
    return annotated


def draw_frame_info(
    frame: np.ndarray,
    result: FrameResult,
    extra_info: str = "",
) -> np.ndarray:
    """
    Draw frame information overlay (frame count, detection counts, timing).
    
    Args:
        frame: Input image (will be modified in place)
        result: FrameResult with detection info
        extra_info: Additional info to display
    
    Returns:
        Frame with info overlay
    """
    vehicle_count = len(result.detections)
    plate_count = len(result.plate_boxes)
    
    info_text = f"Frame: {result.frame_id} | Vehicles: {vehicle_count} | Plates: {plate_count} | {result.inference_time_ms:.0f}ms"
    if extra_info:
        info_text += f" | {extra_info}"
    
    # Draw background for text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(info_text, font, font_scale, thickness)
    
    cv2.rectangle(frame, (5, 5), (text_w + 15, text_h + 15), (0, 0, 0), -1)
    cv2.putText(frame, info_text, (10, text_h + 8), font, font_scale, (0, 255, 0), thickness)
    
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
    """
    Process a video file with two-stage detection.
    
    Args:
        video_path: Path to video file
        vehicle_model: YOLO vehicle model (loaded if None)
        plate_model: YOLO plate model (loaded if None)
        confidence: Detection confidence threshold
        skip_frames: Number of frames to skip between detections
        max_frames: Maximum frames to process (None = all)
        enable_plate_detection: Whether to run plate detection
    
    Yields:
        FrameResult for each processed frame
    """
    global _frame_counter
    _frame_counter = 0  # Reset frame counter
    
    # Load models if not provided
    if vehicle_model is None:
        vehicle_model = load_vehicle_model()
    if plate_model is None and enable_plate_detection:
        plate_model = load_plate_model()
    
    # Open video
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
            
            # Skip frames if requested
            if skip_frames > 0 and frame_id % (skip_frames + 1) != 0:
                frame_id += 1
                continue
            
            # Run detection
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
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

def detect_plates(
    plate_model: Any,
    frame: np.ndarray,
    vehicle_detections: List[Detection],
    confidence: float = 0.3,
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, Tuple[int, int, int, int]]]:
    """
    Legacy function for plate detection (now uses crop-based approach).
    Kept for backwards compatibility with existing code.
    """
    return detect_plates_in_crops(plate_model, frame, vehicle_detections, confidence)


# ============================================================================
# MAIN - For standalone testing
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Two-Stage Vehicle & Plate Detection")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--confidence", type=float, default=0.5, help="Detection confidence")
    parser.add_argument("--no-plates", action="store_true", help="Disable plate detection")
    parser.add_argument("--display", action="store_true", help="Display output window")
    args = parser.parse_args()
    
    # Load models
    print("🚀 Initializing Two-Stage Detection Pipeline...")
    vehicle_model, plate_model = get_models()
    
    if args.video:
        video_path = args.video
    else:
        # Default to traffic sample
        video_path = str(Path(__file__).parent.parent.parent.parent / "data" / "videos" / "traffic_sample.mp4")
    
    print(f"📹 Processing: {video_path}")
    
    # Process video
    for result in process_video(
        video_path,
        vehicle_model=vehicle_model,
        plate_model=plate_model if not args.no_plates else None,
        confidence=args.confidence,
        enable_plate_detection=not args.no_plates,
    ):
        # Draw detections
        annotated = draw_detections(result.image, result)
        annotated = draw_frame_info(annotated, result)
        
        print(f"Frame {result.frame_id}: {len(result.detections)} vehicles, {len(result.plate_boxes)} plates, {result.inference_time_ms:.1f}ms")
        
        if args.display:
            cv2.imshow("Two-Stage Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    if args.display:
        cv2.destroyAllWindows()
    
    print("✅ Processing complete!")
