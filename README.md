# Intelligent Traffic Management System

An AI-powered system designed to reduce traffic congestion and improve road safety by detecting violations, predicting illegal parking, adapting traffic signals, and providing real-time feedback to drivers and authorities.

## 🚀 Features

- **🅿️ Parking Behaviour & Dynamic Fine System** - Detects roadside parking violations, predicts illegal parking before it happens, calculates dynamic fines based on duration + traffic impact
- **🚗 Traffic Violation Detection & Driver Scoring** - Uses YOLOv8 to detect unsafe driving, maintains 100-point driver safety scores with daily reset
- **🚦 Fuzzy Logic Adaptive Traffic Signals** - Adjusts signal timings based on real-time traffic density, gives priority to emergency vehicles
- **⚠️ Accident Risk Prediction & Dashboard** - Calculates real-time accident risk, identifies danger zones, displays live stats and heatmaps
- **📱 Web Dashboard + Mobile App** - Flutter-based single codebase for admin dashboard (web) and driver app (mobile)

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

- Python 3.11+
- Node.js 18+ (for Flutter web)
- Flutter 3.16+ (for mobile/web app)
- Git

## 🛠️ Quick Start

### 1. Clone and Setup

```powershell
cd d:\Intelligent-Traffic-Management-System

# Create Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### 2. Install Dependencies

```powershell
cd backend

# Install requirements
pip install -r requirements.txt

# Install PyTorch (CPU-only for systems without NVIDIA GPU)
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

### 3. Run the Backend Server

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs for API documentation

### 4. Test Video Ingestion

```powershell
# Download a sample traffic video from YouTube
python -m app.ingest.youtube_stream download "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" -r 720

# Get video info
python -m app.ingest.youtube_stream info data/videos/your_video.mp4

# Test streaming
python -m app.ingest.youtube_stream stream data/videos/your_video.mp4 -n 50
```

## 📁 Project Structure

```
Intelligent-Traffic-Management-System/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── ingest/              # Video ingestion module
│   │   ├── detection/           # YOLOv8 detection module
│   │   ├── tracking/            # Object tracking
│   │   ├── parking/             # Parking violation detection
│   │   ├── scoring/             # Driver scoring system
│   │   ├── fuzzy/               # Fuzzy logic traffic controller
│   │   ├── wokwi/               # Arduino simulation bridge
│   │   ├── tts/                 # Text-to-speech warnings
│   │   ├── db/                  # Database models
│   │   └── services/            # Business logic services
│   └── requirements.txt
├── frontend/                     # Flutter web/mobile app
├── wokwi/                        # Arduino traffic light simulation
├── data/
│   ├── videos/                   # Downloaded CCTV footage
│   └── plates/                   # License plate training data
├── models/                       # YOLOv8 model weights
└── tests/                        # Test suite
```

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/version` | GET | Version and config info |
| `/events` | GET | SSE stream for real-time updates |
| `/pipeline/start` | POST | Start detection pipeline |
| `/pipeline/stop` | POST | Stop detection pipeline |
| `/pipeline/status` | GET | Get pipeline status |

## 🧠 Models

| Model | Purpose | File |
|-------|---------|------|
| Vehicle Detection | Detect cars, trucks, buses, motorcycles | `yolov8n.pt` |
| License Plate Detection | Detect license plates on vehicles | `best_plate.pt` |

## 📊 Tech Stack

- **Backend**: FastAPI, Python 3.11
- **AI/ML**: YOLOv8 (Ultralytics), OpenCV
- **Database**: SQLite (local-first)
- **Real-time**: Server-Sent Events (SSE)
- **Frontend**: Flutter (Web + Mobile)
- **Hardware Sim**: Wokwi (Arduino)
- **TTS**: edge-tts / pyttsx3

## 🔧 Configuration

Edit `backend/app/config.py` or create a `.env` file:

```env
DEBUG=true
DETECTION_CONFIDENCE=0.5
FRAME_SKIP=2
PARKING_DURATION_THRESHOLD=30
```

## 📜 License

This project is for educational purposes.

## 👥 Team

See `plan/` folder for team details and proposal presentation.
