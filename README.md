# 🚦 Intelligent Traffic Management System (ITMS)

An AI-powered system designed to reduce traffic congestion and improve road safety through real-time violation detection, adaptive traffic signals, and driver scoring.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Current Progress](#-current-progress)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
  - [Step 1: Backend Setup](#step-1-backend-setup)
  - [Step 2: Frontend Setup (Web)](#step-2-frontend-setup-web)
  - [Step 3: Mobile App Setup (Optional)](#step-3-mobile-app-setup-optional)
- [Running the System](#-running-the-system)
- [Troubleshooting](#-troubleshooting)
- [Team Members](#-team-members)

---

## 🎯 Overview

**Version:** 1.0 (First Evaluation)  
**Date:** January 3, 2026  

This project demonstrates an intelligent traffic management system with:
- Real-time vehicle detection using YOLOv8
- License plate recognition with custom-trained models
- Parking and speeding violation detection
- Driver scoring system (LiveSafe Score)
- Adaptive traffic signals using fuzzy logic
- Admin dashboard for monitoring

---

## 📊 Current Progress

### ✅ Completed (Backend)

| Feature | Description | Status |
|---------|-------------|--------|
| 🚗 Vehicle Detection | YOLOv8n with DeepSORT tracking | ✅ Complete |
| 🔍 License Plate Detection | Custom YOLOv8 model (281 Sri Lankan plates) | ✅ Complete |
| 📝 OCR Integration | EasyOCR with preprocessing pipeline | ✅ Complete |
| 🅿️ Parking Violations | No-parking zone monitoring with warnings | ✅ Complete |
| ⚡ Speed Detection | Real-time speed estimation | ✅ Complete |
| 📊 Driver Scoring | 100-point LiveSafe Score system | ✅ Complete |
| 🚦 Traffic Signals | Fuzzy logic adaptive timing | ✅ Complete |
| 🔊 Voice Warnings | edge-tts + pyttsx3 audio alerts | ✅ Complete |
| 🚨 Emergency Mode | Admin-triggered emergency override | ✅ Complete |

### 🔄 In Progress (Frontend)

| Feature | Description | Status |
|---------|-------------|--------|
| 📺 Live Video Feed | Real-time detection display | ✅ Complete |
| 🚦 Traffic Light Panel | 4-way signal visualization | ✅ Complete |
| 🗺️ Zone Editor | Draw no-parking zones on map | ✅ Complete |
| 🚨 Emergency Button | Trigger emergency mode | ✅ Complete |
| 📋 Violations List | View and manage violations | 🔄 In Progress |
| 👥 Drivers List | View driver scores | 🔄 In Progress |
| 📈 Analytics | Charts and trends | 🔄 In Progress |

### 🔄 In Progress (Mobile App)

| Feature | Description | Status |
|---------|-------------|--------|
| 🔐 Authentication | Driver login with phone + plate | ✅ Complete |
| 📊 Dashboard | Score and violations | 🔄 In Progress |
| 💳 Payments | Fine payments | 📅 Planned |

---

## 📋 Prerequisites

### For Backend
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.11 or 3.12 | Required |
| **Windows** | 10 or 11 | PowerShell recommended |

### For Frontend (Web)
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Flutter SDK** | 3.16+ | With Dart 3.2+ |
| **Chrome** | Latest | For web development |

### For Mobile App (Android) ⚠️ IMPORTANT
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Flutter SDK** | 3.16+ | With Dart 3.2+ |
| **Android Studio** | 2023.1+ | Required for SDK tools |
| **Android SDK** | API Level 34 | Required |
| **Android NDK** | **23.1.7779620** | ⚠️ **EXACT VERSION** |
| **Java** | 17 | Bundled with Android Studio |

---

## 📦 Setup Instructions

> **Note:** This project is provided as a ZIP file. Extract it to `D:\Intelligent-Traffic-Management-System\`

---

### Step 1: Backend Setup

Open **PowerShell** and follow these steps:

#### 1.1 Navigate to Project
```powershell
cd D:\Intelligent-Traffic-Management-System
```

#### 1.2 Create Virtual Environment
```powershell
python -m venv .venv
```

#### 1.3 Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

✅ **Success:** You should see `(.venv)` prefix in your terminal

#### 1.4 Upgrade pip
```powershell
python -m pip install --upgrade pip
```

#### 1.5 Install Backend Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

**⏱️ Duration:** 2-3 minutes

#### 1.6 Install PyTorch (CPU Version)

> ⚠️ **IMPORTANT:** Run this command SEPARATELY after requirements.txt

```powershell
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

**⏱️ Duration:** 3-5 minutes (large download ~200MB)

#### 1.7 Verify Installation
```powershell
python check_db.py
```

✅ **Expected Output:**
```
✅ Database connection OK
✅ TTS warnings folder found
✅ 5 audio files ready
```

---

### Step 2: Frontend Setup (Web)

#### 2.1 Install Flutter SDK

1. Download Flutter from: https://docs.flutter.dev/get-started/install/windows
2. Extract to `C:\flutter`
3. Add `C:\flutter\bin` to your system PATH

#### 2.2 Verify Flutter Installation
```powershell
flutter --version
```

✅ **Expected:** `Flutter 3.16.x • Dart 3.2.x`

#### 2.3 Install Flutter Dependencies
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter pub get
```

---

### Step 3: Mobile App Setup (Optional)

> ⚠️ Only needed if you want to run the mobile app on Android

#### 3.1 Install Android Studio

1. Download from: https://developer.android.com/studio
2. Install and complete the setup wizard

#### 3.2 Install Required SDK Components

1. Open **Android Studio** → **File** → **Settings**
2. Go to **Languages & Frameworks** → **Android SDK**
3. **SDK Platforms** tab:
   - ✅ Check **Android 14.0 (API 34)**
4. **SDK Tools** tab:
   - ✅ Click **Show Package Details** (bottom right)
   - ✅ Expand **NDK (Side by side)**
   - ✅ Select exactly **23.1.7779620**
   - ✅ Check **Android SDK Build-Tools 34.0.0**
5. Click **Apply** and wait for installation

#### 3.3 Accept Licenses
```powershell
flutter doctor --android-licenses
# Press 'y' for all prompts
```

---

## 🚀 Running the System

### Full Stack (Backend + Frontend)

**Terminal 1 - Start Backend:**
```powershell
cd D:\Intelligent-Traffic-Management-System
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Success:** `Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Start Frontend (new PowerShell window):**
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter run -d chrome --web-port 8080
```

✅ **Success:** Admin dashboard opens at http://localhost:8080

### Run Mobile App (Optional)
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter run
```

Select your Android device when prompted.

---

### 📍 Access Points

| URL | Description |
|-----|-------------|
| http://localhost:8080 | 🖥️ Admin Dashboard |
| http://localhost:8000/docs | 📡 API Documentation |
| http://localhost:8000/detect | 🎥 Live Detection Stream |

### 🔐 Default Admin Login

- **Username:** `admin`
- **Password:** `admin123`

---

## 🔧 Troubleshooting

### ❌ First Flutter Build Fails

If the first `flutter run` fails, clean and rebuild:

```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter clean
flutter pub get
flutter run -d chrome --web-port 8080
```

### ❌ "flutter pub get" Fails

```powershell
Remove-Item pubspec.lock
flutter pub get
```

### ❌ Backend Errors

**"Torch not found" or CUDA errors:**
```powershell
cd D:\Intelligent-Traffic-Management-System\backend
pip uninstall torch torchvision -y
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

**"EasyOCR not installed":**
```powershell
pip install easyocr==1.7.1
```

### ❌ Android Build Fails

**"NDK not found":**
1. Open **Android Studio** → **SDK Manager** → **SDK Tools**
2. Check **Show Package Details**
3. Install exactly **NDK 23.1.7779620**

**"Gradle build failed":**
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend\android
.\gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

### ❌ Port Already in Use

```powershell
# Kill process using port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

---

## 👥 Team Members

| ID | Focus Area |
|----|------------|
| IT22900890 | Parking Detection, License Plate OCR |
| IT22337580 | Lane Safety, Driver Scoring System |
| IT22925572 | Traffic Signals, Fuzzy Logic Controller |
| IT22363848 | Speed Detection, Risk Prediction |

---

**Version:** 1.0 (First Evaluation)  
**Date:** January 3, 2026
