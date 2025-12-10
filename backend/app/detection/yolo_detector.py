"""
Intelligent Traffic Management System - YOLOv8 Detection Module
Vehicle detection and tracking using YOLOv8 with built-in tracking
Includes license plate detection with dual-model pipeline
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

# Lazy load ultralytics to avoid slow startup
_model_cache: Dict[str, Any] = {}

# Track which vehicles have detected plates (track_id -> plate_info)
_plate_detections: Dict[int, Dict[str, Any]] = {}


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
    has_plate: bool = False  # True if a plate was detected inside this vehicle
    plate_bbox: Optional[Tuple[int, int, int, int]] = None  # Plate bounding box
    
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
    image: Optional[np.ndarray] = None
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "detection_count": len(self.detections),
            "inference_time_ms": round(self.inference_time_ms, 2),
            "detections": [d.to_dict() for d in self.detections],
        }


# Vehicle class IDs from COCO dataset (used by YOLOv8)
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


def load_plate_model(device: str = "cpu") -> Any:
    """Load the custom license plate detection model."""
    plate_model_path = Path(settings.plate_model)
    
    # Check multiple locations for the model
    possible_paths = [
        plate_model_path,
        Path("models") / "best_plate.pt",
        Path(__file__).parent.parent.parent.parent / "models" / "best_plate.pt",
    ]
    
    for path in possible_paths:
        if path.exists():
            return load_model(str(path), device)
    
    print(f"⚠️ Plate model not found, tried: {[str(p) for p in possible_paths]}")
    return None


def detect_plates(
    plate_model: Any,
    frame: np.ndarray,
    vehicle_detections: List[Detection],
    confidence: float = 0.3,
) -> Tuple[List[Tuple[int, int, int, int]], Dict[int, Tuple[int, int, int, int]]]:
    """
    Detect license plates in frame and associate with vehicles.
    
    Args:
        plate_model: Loaded plate detection model
        frame: Input image
        vehicle_detections: List of vehicle detections to associate plates with
        confidence: Detection confidence threshold
    
    Returns:
        Tuple of (all_plate_boxes, vehicle_plate_map)
        - all_plate_boxes: List of (x1, y1, x2, y2) for all detected plates
        - vehicle_plate_map: Dict mapping track_id to plate bbox
    """
    global _plate_detections
    
    if plate_model is None:
        return [], {}
    
    # Run plate detection on entire frame
    results = plate_model.predict(
        frame,
        conf=confidence,
        verbose=False,
    )
    
    all_plates = []
    vehicle_plate_map = {}
    
    if results and len(results) > 0 and results[0].boxes is not None:
        boxes = results[0].boxes
        
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = map(int, xyxy)
            plate_bbox = (x1, y1, x2, y2)
            all_plates.append(plate_bbox)
            
            # Find which vehicle this plate belongs to
            plate_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            for det in vehicle_detections:
                vx1, vy1, vx2, vy2 = det.bbox
                
                # Check if plate center is inside vehicle bbox
                if vx1 <= plate_center[0] <= vx2 and vy1 <= plate_center[1] <= vy2:
                    vehicle_plate_map[det.track_id] = plate_bbox
                    
                    # Cache the plate detection for this vehicle
                    _plate_detections[det.track_id] = {
                        "bbox": plate_bbox,
                        "timestamp": time.time(),
                    }
                    break
    
    return all_plates, vehicle_plate_map


def detect_and_track(
    model: Any,
    frame: np.ndarray,
    frame_id: int = 0,
    confidence: float = 0.5,
    classes: Optional[List[int]] = None,
    track: bool = True,
) -> FrameResult:
    """
    Run detection and tracking on a single frame.
    
    Args:
        model: Loaded YOLO model
        frame: Input image (BGR format from OpenCV)
        frame_id: Frame identifier
        confidence: Minimum confidence threshold
        classes: List of class IDs to detect (None = all)
        track: Whether to use tracking (assigns persistent IDs)
    
    Returns:
        FrameResult with detections
    """
    timestamp = time.time()
    
    # Default to traffic-relevant classes
    if classes is None:
        classes = list(TRAFFIC_CLASSES.keys())
    
    # Run inference with or without tracking
    start_time = time.time()
    
    if track:
        results = model.track(
            frame,
            conf=confidence,
            classes=classes,
            persist=True,  # Maintain track IDs across frames
            verbose=False,
        )
    else:
        results = model.predict(
            frame,
            conf=confidence,
            classes=classes,
            verbose=False,
        )
    
    inference_time = (time.time() - start_time) * 1000  # ms
    
    # Parse results
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
                
                # Get track ID (if tracking)
                if track and boxes.id is not None:
                    track_id = int(boxes.id[i].cpu().numpy())
                else:
                    track_id = -1
                
                # Calculate centroid and area
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                area = (x2 - x1) * (y2 - y1)
                
                # Get class name
                class_name = TRAFFIC_CLASSES.get(cls_id, f"class_{cls_id}")
                
                detection = Detection(
                    track_id=track_id,
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    centroid=centroid,
                    area=area,
                    timestamp=timestamp,
                )
                detections.append(detection)
    
    return FrameResult(
        frame_id=frame_id,
        timestamp=timestamp,
        detections=detections,
        inference_time_ms=inference_time,
        image=frame,
    )


def draw_detections(
    frame: np.ndarray,
    detections: List[Detection],
    plate_boxes: Optional[List[Tuple[int, int, int, int]]] = None,
    vehicle_plate_map: Optional[Dict[int, Tuple[int, int, int, int]]] = None,
    show_labels: bool = True,
    show_track_id: bool = True,
    box_thickness: int = 2,
) -> np.ndarray:
    """
    Draw detection boxes and labels on a frame.
    
    Args:
        frame: Input image
        detections: List of Detection objects
        plate_boxes: List of plate bounding boxes to draw
        vehicle_plate_map: Map of track_id to plate bbox
        show_labels: Whether to show class labels
        show_track_id: Whether to show track IDs
        box_thickness: Line thickness for boxes
    
    Returns:
        Annotated image
    """
    annotated = frame.copy()
    
    # Color palette for different classes
    colors = {
        "car": (0, 255, 0),        # Green
        "motorcycle": (255, 165, 0), # Orange
        "bus": (255, 0, 0),        # Blue
        "truck": (128, 0, 128),    # Purple
        "person": (0, 255, 255),   # Yellow
        "bicycle": (255, 0, 255),  # Magenta
    }
    default_color = (200, 200, 200)
    plate_color = (255, 0, 0)  # Blue for plates
    
    # Draw plate boxes first (so vehicle boxes overlay them)
    if plate_boxes:
        for px1, py1, px2, py2 in plate_boxes:
            cv2.rectangle(annotated, (px1, py1), (px2, py2), plate_color, 2)
            # Small "PLATE" label
            cv2.putText(annotated, "PLATE", (px1, py1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, plate_color, 1)
    
    # Build map of which vehicles have plates
    vehicles_with_plates = set()
    if vehicle_plate_map:
        vehicles_with_plates = set(vehicle_plate_map.keys())
    
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        color = colors.get(det.class_name, default_color)
        
        # Check if this vehicle has a plate detected
        has_plate = det.track_id in vehicles_with_plates or det.has_plate
        
        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, box_thickness)
        
        # Build label text
        if show_labels or show_track_id:
            label_parts = []
            if show_track_id and det.track_id >= 0:
                if has_plate:
                    label_parts.append(f"ID:{det.track_id} [Plate Detected]")
                else:
                    label_parts.append(f"ID:{det.track_id}")
            if show_labels:
                label_parts.append(f"{det.class_name}")
                label_parts.append(f"{det.confidence:.2f}")
            
            label = " ".join(label_parts)
            
            # Draw label background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # Use different background color if plate detected
            bg_color = (255, 100, 0) if has_plate else color  # Cyan-ish for plate detected
            
            cv2.rectangle(annotated, (x1, y1 - text_h - 10), (x1 + text_w + 4, y1), bg_color, -1)
            cv2.putText(annotated, label, (x1 + 2, y1 - 5), font, font_scale, (255, 255, 255), thickness)
    
    return annotated


def process_video(
    video_path: str,
    model_path: str = "yolov8n.pt",
    output_path: Optional[str] = None,
    confidence: float = 0.5,
    frame_skip: int = 1,
    max_frames: Optional[int] = None,
    show_preview: bool = False,
    track: bool = True,
    detect_plates: bool = True,
) -> Generator[FrameResult, None, None]:
    """
    Process a video file and yield detection results.
    
    Args:
        video_path: Path to input video
        model_path: Path to YOLO model weights
        output_path: Optional path to save annotated video
        confidence: Detection confidence threshold
        frame_skip: Process every Nth frame
        max_frames: Maximum frames to process
        show_preview: Show preview window
        track: Use object tracking
        detect_plates: Also run license plate detection
    
    Yields:
        FrameResult for each processed frame
    """
    # Load models
    model = load_model(model_path)
    plate_model = load_plate_model() if detect_plates else None
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📹 Processing video: {video_path}")
    print(f"   Resolution: {width}x{height} @ {fps:.1f} FPS")
    print(f"   Total frames: {total_frames}")
    print(f"   Frame skip: {frame_skip}")
    print(f"   Plate detection: {'ON' if plate_model else 'OFF'}")
    
    # Setup video writer
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps // frame_skip, (width, height))
    
    frame_id = 0
    processed = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames
            if frame_id % frame_skip != 0:
                frame_id += 1
                continue
            
            # Process frame - vehicle detection
            result = detect_and_track(
                model, frame, frame_id, confidence, track=track
            )
            
            # Detect plates and associate with vehicles
            plate_boxes = []
            vehicle_plate_map = {}
            if plate_model and result.detections:
                # Filter to only vehicle detections for plate association
                vehicle_dets = [d for d in result.detections if d.class_name in VEHICLE_CLASSES.values()]
                from app.detection.yolo_detector import detect_plates as run_plate_detection
                plate_boxes, vehicle_plate_map = run_plate_detection(
                    plate_model, frame, vehicle_dets, confidence=0.3
                )
                
                # Update detections with plate info
                for det in result.detections:
                    if det.track_id in vehicle_plate_map:
                        det.has_plate = True
                        det.plate_bbox = vehicle_plate_map[det.track_id]
            
            # Draw annotations
            annotated = draw_detections(
                frame, result.detections, 
                plate_boxes=plate_boxes,
                vehicle_plate_map=vehicle_plate_map
            )
            result.image = annotated
            
            # Save to output video
            if writer:
                writer.write(annotated)
            
            # Show preview
            if show_preview:
                cv2.imshow("Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            yield result
            
            processed += 1
            frame_id += 1
            
            if max_frames and processed >= max_frames:
                break
            
            # Progress update every 100 frames
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                fps_actual = processed / elapsed
                print(f"   Processed {processed} frames ({fps_actual:.1f} FPS)")
    
    finally:
        cap.release()
        if writer:
            writer.release()
        if show_preview:
            cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        fps_actual = processed / elapsed if elapsed > 0 else 0
        print(f"✅ Completed: {processed} frames in {elapsed:.1f}s ({fps_actual:.1f} FPS)")


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Command-line interface for YOLOv8 detection."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="YOLOv8 Detection Module - Detect and track vehicles"
    )
    
    parser.add_argument("source", help="Video file path or camera index")
    parser.add_argument(
        "-m", "--model",
        default="yolov8n.pt",
        help="Model path (default: yolov8n.pt)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output video path"
    )
    parser.add_argument(
        "-c", "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold (default: 0.5)"
    )
    parser.add_argument(
        "-s", "--skip",
        type=int,
        default=1,
        help="Frame skip (default: 1 = process all)"
    )
    parser.add_argument(
        "-n", "--max-frames",
        type=int,
        help="Maximum frames to process"
    )
    parser.add_argument(
        "--no-track",
        action="store_true",
        help="Disable tracking"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show preview window"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON results"
    )
    
    args = parser.parse_args()
    
    import json
    
    for result in process_video(
        args.source,
        model_path=args.model,
        output_path=args.output,
        confidence=args.confidence,
        frame_skip=args.skip,
        max_frames=args.max_frames,
        show_preview=args.preview,
        track=not args.no_track,
    ):
        if args.json:
            print(json.dumps(result.to_dict()))
        else:
            vehicles = [d for d in result.detections if d.class_name in VEHICLE_CLASSES.values()]
            print(f"Frame {result.frame_id}: {len(vehicles)} vehicles, {result.inference_time_ms:.1f}ms")


if __name__ == "__main__":
    main()
