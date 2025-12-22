# Intelligent Traffic Management System

An AI-powered system designed to reduce traffic congestion and improve road safety by detecting violations, predicting illegal parking, adapting traffic signals, and providing real-time feedback to drivers and authorities.

## 🎬 Demo Status - First Evaluation

**Current Implementation:** Backend AI/ML pipeline fully operational with real-time detection  
**Status:** ✅ Ready for demonstration  
**Last Updated:** December 12, 2025

### ✅ Completed Features

- **🚗 Vehicle Detection & Tracking** - YOLOv8n with object persistence across frames
- **🔍 License Plate Detection** - Custom-trained YOLOv8 model (best_plate.pt) on 281 Sri Lankan plate images
- **📝 OCR Integration** - EasyOCR with preprocessing pipeline, geometric filtering, and regex validation for Sri Lankan plates
- **🅿️ Parking Zone Monitoring** - Configurable no-parking zones with warning (3s) and violation (8s) detection (demo sensitivity)
- **⚡ Speeding Detection** - Real-time speed estimation (demo threshold: 60 km/h / ~120 px/s) - alerts and penalties
- **📊 Driver Scoring System** - 100-point scoring with violation tracking and dynamic fines
- **🚦 Fuzzy Logic Traffic Controller** - Adaptive signal timing based on vehicle density
- **🔊 Voice Warnings (TTS)** - edge-tts + pyttsx3 fallback for audio alerts
- **📡 Real-time Event Stream** - Server-Sent Events (SSE) for live dashboard updates

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTELLIGENT TRAFFIC SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│  Video Ingestion ──► YOLOv8 Detection ──► Object Tracking               │
│        │                    │                    │                       │
│        ▼                    ▼                    ▼                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Plate Model  │    │   Parking    │    │   Traffic    │              │
│  │ (best_plate) │    │  Violations  │    │  Violations  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│        │                    │                    │                       │
│        └────────────────────┼────────────────────┘                       │
│                             ▼                                            │
│                    ┌──────────────────┐                                 │
│                    │  Driver Scoring  │                                 │
│                    │  & Dynamic Fines │                                 │
│                    └────────┬─────────┘                                 │
│                             │                                            │
│              ┌──────────────┼──────────────┐                            │
│              ▼              ▼              ▼                            │
│         SQLite DB      SSE Events    Wokwi Signals                      │
│              │              │              │                            │
│              └──────────────┼──────────────┘                            │
│                             ▼                                            │
│                    ┌──────────────────┐                                 │
│                    │  Flutter Web &   │                                 │
│                    │   Mobile App     │                                 │
│                    └──────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+** (Required)
- **Git** (Required)
- **Webcam or Video File** (For testing)
- **Windows OS** (Current setup optimized for Windows PowerShell)

## 🛠️ Setup Instructions for Demonstration

### Step 1: Create Virtual Environment

Open PowerShell in the project directory and run:

```powershell
# Navigate to project root
cd D:\Intelligent-Traffic-Management-System

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip to latest version
python -m pip install --upgrade pip
```

**Expected Output:** You should see `(.venv)` prefix in your terminal prompt

---

### Step 2: Install Python Dependencies

```powershell
# Navigate to backend folder
cd backend

# Install all requirements
pip install -r requirements.txt

# Install PyTorch CPU version (no NVIDIA GPU needed)
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

**Expected Duration:** 3-5 minutes depending on internet speed  
**Expected Output:** All packages installed successfully with no errors

---

### Step 3: Verify Installation

Run the verification script to check if all components are ready:

```powershell
# From backend folder
python check_db.py
```

**Expected Output:**
- ✅ Database status check
- ✅ TTS warnings folder verification
- ✅ 5 audio files found (parking warnings, speeding alerts)
- ℹ️ Note: Database file will auto-create when first violation is detected

---

### Step 4: Start the Backend Server

```powershell
# Make sure you're in the backend folder with venv activated
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
🔤 Initializing EasyOCR reader (English)...
✅ EasyOCR initialized successfully
```

**Server is now running!** Keep this terminal open.

---

### Step 5: Test the Detection System (Easiest Method)

**🌐 Option A: Web Browser (Recommended for Demo)**

With the server running, simply open your browser and navigate to:

**Live Detection Stream:**  
🎥 **http://127.0.0.1:8000/detect**

This will show:
- Real-time video stream with detection overlay
- All vehicles tracked with bounding boxes
- License plates detected and highlighted
- Speed and parking violations displayed
- All processing happens in the browser!

**Traffic Simulation Dashboard:**  
🚦 **http://127.0.0.1:8000/simulation** (if available)

---

**🖥️ Option B: Command Line (Advanced Testing)**

Open a **new PowerShell terminal** (keep server running) and activate venv:

```powershell
cd D:\Intelligent-Traffic-Management-System
.\.venv\Scripts\Activate.ps1
cd backend

# Test with webcam (real-time)
python -m app.detection.yolo_detector

# OR test with a video file
python -m app.detection.yolo_detector --source path\to\your\video.mp4
```

**Expected Behavior:**
- OpenCV window opens showing live video feed
- Vehicles detected with bounding boxes and IDs
- License plates detected and cropped
- OCR reads plate numbers (cached for 2 seconds per plate)
- Parking violations triggered after 15 seconds in no-parking zones
- Speed violations triggered above 80 km/h (or 150 px/s in video)
- Voice warnings play automatically via speakers
- Console shows detailed logs: `[TRACK]`, `[PLATE]`, `[OCR]`, `[AUDIO]`, `[SIGNAL]`

---

### Step 6: Access the API Documentation

While server is running, open your browser:

**Swagger UI:** http://127.0.0.1:8000/docs  
**ReDoc:** http://127.0.0.1:8000/redoc

**Key Endpoints for Demo:**
- `GET /` - Welcome message
- `GET /detect` - 🎥 **Live video detection stream** (easiest way to demo!)
- `GET /simulation` - 🚦 Traffic simulation dashboard
- `GET /health` - System health check
- `GET /version` - Version and configuration info
- `GET /events` - Server-Sent Events stream (real-time updates)
- `POST /pipeline/start` - Start detection pipeline
- `POST /pipeline/stop` - Stop detection pipeline
- `GET /pipeline/status` - Current pipeline status

## 📁 Project Structure

```
Intelligent-Traffic-Management-System/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Configuration settings
│   │   ├── detection/
│   │   │   └── yolo_detector.py       # ⭐ Main detection engine (1244 lines)
│   │   ├── services/
│   │   │   └── ocr_service.py         # EasyOCR with preprocessing pipeline
│   │   ├── tts/
│   │   │   ├── tts_service.py         # Voice warning system
│   │   │   └── warnings/              # Generated audio files
│   │   ├── fuzzy/                     # Fuzzy logic traffic signal controller
│   │   ├── scoring/                   # Driver scoring & violation tracking
│   │   ├── parking/                   # Parking zone logic
│   │   ├── tracking/                  # Object tracking utilities
│   │   ├── wokwi/                     # Arduino simulation bridge
│   │   ├── db/                        # Database models
│   │   └── ingest/                    # Video ingestion utilities
│   ├── check_db.py                    # ⭐ Verification script
│   └── requirements.txt               # Python dependencies
├── models/
│   ├── yolov8n.pt                     # Vehicle detection model
│   └── best_plate.pt                  # ⭐ Custom-trained license plate model
├── data/
│   ├── videos/                        # Test video files
│   └── plates/                        # Training dataset (281 images)
├── plan/                              # Project documentation
└── README.md                          # This file
```

## 🎯 What to Expect During Demo

### Console Output

When running detection, you'll see real-time logs:

```
[TRACK] Vehicle ID 3 (car) at (450, 320)
[PLATE] Detected plate for vehicle 3 - size: (120, 45)
[OCR] Reading plate from vehicle 3...
[OCR] ✓ "CAA-1234" (Cached for 2.0s)
[AUDIO] ♪ Playing: warnings\parking_zone_warning.mp3
[PARKING] Vehicle 3 in NO-PARKING zone for 5.2s (WARNING)
[SIGNAL] 🚦 Green: 45.0s | Density: 12 vehicles
[SPEED] Vehicle 7 speeding: 165.3 px/s (threshold: 150.0)
[AUDIO] ♪ Playing: warnings\speeding_violation.mp3
[PARKING] Vehicle 3 in NO-PARKING zone for 15.8s (VIOLATION)
```

### Video Window

- **Green boxes:** Tracked vehicles with IDs
- **Yellow boxes:** Detected license plates
- **Red zones:** No-parking areas (if configured)
- **Speed indicators:** Displayed on fast-moving vehicles
- **FPS counter:** Shows processing speed

### Audio Warnings

The system automatically plays voice warnings:
1. **"Warning: Vehicle detected in no parking zone"** - After 5 seconds
2. **"Parking violation detected"** - After 15 seconds
3. **"Speed violation detected"** - When exceeding 80 km/h
4. **Emergency alerts** - For critical violations

### Performance Metrics

- **Detection FPS:** 15-30 fps (depends on CPU)
- **OCR Processing:** ~500ms per plate (first read), then cached
- **Frame Skip:** Every 2nd frame processed to maintain speed
- **Tracking:** Persistent IDs across frames even when occluded

---

## 🧠 AI Models

| Model | Purpose | Training | File | Accuracy |
|-------|---------|----------|------|----------|
| YOLOv8n | Vehicle Detection | COCO pre-trained | `yolov8n.pt` | 95%+ |
| YOLOv8 Custom | License Plate Detection | 281 Sri Lankan plates (50 epochs) | `best_plate.pt` | 87% mAP@50 |
| EasyOCR | Text Recognition | Pre-trained English | Built-in | 85%+ (with filtering) |

---

## 📊 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI, Python 3.11 | REST API & WebSocket server |
| **AI/ML** | YOLOv8, OpenCV, EasyOCR | Computer vision pipeline |
| **Detection** | Ultralytics YOLO | Two-stage object detection |
| **OCR** | EasyOCR | License plate text recognition |
| **Control** | scikit-fuzzy | Fuzzy logic signal controller |
| **TTS** | edge-tts + pyttsx3 | Voice warning synthesis |
| **Database** | SQLite + aiosqlite | Local-first violation storage |
| **Real-time** | SSE (Server-Sent Events) | Live dashboard updates |
| **Hardware Sim** | Wokwi Arduino | Traffic light prototype |

---

## 🎮 Keyboard Controls (During Detection)

When the OpenCV window is active:

- **`Q`** - Quit detection and close window
- **`P`** - Pause/Resume video processing
- **`S`** - Save current frame as screenshot
- **`Space`** - Advance one frame (when paused)

---

## 🔧 Configuration

Key settings in [backend/app/config.py](backend/app/config.py):

```python
DETECTION_CONFIDENCE = 0.5      # YOLO confidence threshold
FRAME_SKIP = 2                  # Process every Nth frame
PARKING_WARNING_TIME = 5        # Seconds before warning
PARKING_VIOLATION_TIME = 15     # Seconds before fine
SPEED_THRESHOLD_KMH = 80        # Speed limit in km/h
OCR_CACHE_DURATION = 2.0        # Cache plate reads (seconds)
```

You can override these via environment variables or `.env` file.

## ⚠️ Troubleshooting

### Issue: "EasyOCR not installed"
```powershell
pip install easyocr==1.7.1
```

### Issue: "Torch not found" or CUDA errors
```powershell
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

### Issue: No audio warnings
- Check if `backend/app/tts/warnings/` folder has `.mp3` files
- Run `python check_db.py` to verify TTS setup
- Ensure speakers/volume are enabled

### Issue: Low FPS / Slow detection
- Increase `FRAME_SKIP` to 3 or 4 in config.py
- Close other applications to free CPU/RAM
- Use lower resolution video (480p instead of 1080p)

### Issue: Webcam not detected
```powershell
# List available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

---

## 📝 Notes for Evaluators

### Demo Highlights

1. **Two-Stage Detection:** First detects vehicles → then crops and detects plates on vehicles only (not background plates)
2. **Smart Caching:** OCR results cached for 2 seconds to avoid redundant processing
3. **Configurable Zones:** Parking zones defined in code, easily customizable
4. **Offline Capable:** All processing runs locally, no cloud dependencies
5. **Real-time Performance:** Frame skipping and optimizations maintain 20+ FPS

### Known Limitations

- OCR accuracy depends on plate clarity and angle (~85% success rate)
- Speed estimation is pixel-based (requires calibration for real-world accuracy)
- Database persistence occurs only when violations are recorded
- Currently optimized for Sri Lankan license plate format (regex: `[A-Z]{2,3}-\d{4}`)

### Future Enhancements

- GPS integration for real-world location tracking
- Cloud storage for violation records
- Mobile app for driver notifications
- Multi-lane support with lane detection
- Night vision mode with infrared support

---

## 📜 License

This project is for educational purposes as part of an academic evaluation.

## 👥 Team

See [plan/](plan/) folder for team details and proposal presentation.

---

## 📞 Quic/ URL | Purpose |
|---------|---------|
| `.\.venv\Scripts\Activate.ps1` | Activate virtual environment |
| `pip install -r backend/requirements.txt` | Install dependencies |
| `python backend/check_db.py` | Verify system setup |
| `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` | Start API server |
| **`http://127.0.0.1:8000/detect`** | **🎥 Live detection in browser (EASIEST!)** |
| **`http://127.0.0.1:8000/simulation`** | **🚦 Traffic simulation dashboard** |
| `http://127.0.0.1:8000/docs` | API documentation |
| `python -m app.detection.yolo_detector` | Run detection via command line |

**For Demo:** Just run steps 1-4 from setup, then open `http://127.0.0.1:8000/detect` in your browser

**For Demo:** Just run steps 1-4 from setup, then step 5 to see the system in action!

---

**Last Updated:** December 12, 2025  
**Version:** 1.0 (First Evaluation Build)
