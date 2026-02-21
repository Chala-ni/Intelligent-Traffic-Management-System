# 🚦 Intelligent Traffic Management System (ITMS)

An AI-powered system designed to reduce traffic congestion and improve road safety through real-time violation detection, adaptive traffic signals, and driver scoring. The system includes a **FastAPI backend**, a **Flutter web admin dashboard**, and a **Flutter mobile app** for drivers.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
  - [Step 1: Firebase Setup](#step-1-firebase-setup)
  - [Step 2: Backend Setup](#step-2-backend-setup)
  - [Step 3: Frontend Setup (Web Dashboard)](#step-3-frontend-setup-web-dashboard)
  - [Step 4: Mobile App Setup (Android)](#step-4-mobile-app-setup-android)
- [Running the System](#-running-the-system)
  - [Start the Backend](#start-the-backend)
  - [Run the Web Dashboard](#run-the-web-dashboard)
  - [Run the Mobile App on Android](#run-the-mobile-app-on-android)
- [ADB Port Forwarding (Mobile ↔ Backend)](#-adb-port-forwarding-mobile--backend)
- [Default Credentials](#-default-credentials)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [Team Members](#-team-members)

---

## 🎯 Overview

**Version:** 2.0 (Final)  
**Date:** February 21, 2026  

This project demonstrates an intelligent traffic management system with:
- Real-time vehicle detection using YOLOv8
- License plate recognition with custom-trained models
- Parking and speeding violation detection
- Lane weaving and abnormal driving behavior detection
- Driver scoring system (LiveSafe Score)
- Adaptive traffic signals using fuzzy logic
- Push notifications (FCM) for drivers
- Admin web dashboard for monitoring
- Driver mobile app for scores, violations, and fine payments

---

## ✅ Features

### Backend

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
| 🔔 Push Notifications | Firebase Cloud Messaging (FCM) | ✅ Complete |
| 🛡️ Risk Prediction | Vehicle risk scoring & abnormal behavior | ✅ Complete |
| 🏘️ Community Alerts | Crowd-sourced safety alerts | ✅ Complete |

### Web Dashboard (Admin)

| Feature | Description | Status |
|---------|-------------|--------|
| 📺 Live Video Feed | Real-time detection display via WebSocket | ✅ Complete |
| 🚦 Traffic Light Panel | 4-way signal visualization | ✅ Complete |
| 🗺️ Zone Editor | Draw no-parking zones on video snapshot | ✅ Complete |
| 🚨 Emergency Button | Trigger emergency mode | ✅ Complete |
| 📋 Violations List | View and manage traffic violations | ✅ Complete |
| 👥 Drivers List | View driver scores & profiles | ✅ Complete |
| 📈 Analytics | Charts, trends, and statistics | ✅ Complete |
| 📜 Audit Log | Admin activity tracking | ✅ Complete |

### Mobile App (Driver)

| Feature | Description | Status |
|---------|-------------|--------|
| 🔐 Authentication | Driver login with phone + license plate | ✅ Complete |
| 📊 Dashboard | LiveSafe Score, recent violations, risk level | ✅ Complete |
| 📋 Violations History | View all violations with evidence snapshots | ✅ Complete |
| 💳 Fine Payments | View and pay fines | ✅ Complete |
| 🔔 Push Notifications | Real-time violation alerts via FCM | ✅ Complete |
| 🔊 TTS Alerts | Text-to-speech notification readout | ✅ Complete |

---

## 📋 Prerequisites

### For Backend
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.11 or 3.12 | Required |
| **Windows** | 10 or 11 | PowerShell recommended |
| **Firebase Project** | — | See [FIREBASE_SETUP.md](FIREBASE_SETUP.md) |

### For Web Dashboard
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Flutter SDK** | 3.16+ | With Dart 3.2+ |
| **Chrome** | Latest | For web development |

### For Mobile App (Android)
| Requirement | Version | Notes |
|-------------|---------|-------|
| **Flutter SDK** | 3.16+ | With Dart 3.2+ |
| **Android Studio** | 2023.1+ | Required for SDK tools |
| **Android SDK** | API Level 34 | Required |
| **Android NDK** | **27.0.12077973** | ⚠️ **EXACT VERSION REQUIRED** |
| **Java** | 17 | Bundled with Android Studio |
| **ADB** | Latest | For port forwarding (comes with Android SDK) |
| **Physical Android Device** or **Emulator** | Android 7.0+ | USB debugging enabled |

---

## 📦 Setup Instructions

> **Note:** This project is provided as a ZIP file. Extract it to `D:\Intelligent-Traffic-Management-System\`

---

### Step 1: Firebase Setup

> ⚠️ **REQUIRED** — The backend uses Firebase Firestore as its database and FCM for push notifications.

Follow the complete guide in **[FIREBASE_SETUP.md](FIREBASE_SETUP.md)** to:

1. Create a Firebase project
2. Enable Firestore database
3. Generate and place the service account key (`backend/firebase-service-account.json`)
4. Add an Android app and download `google-services.json` to `frontend/android/app/`
5. Verify the setup

> **Without Firebase configured, the backend will not start and the mobile app will not receive push notifications.**

---

### Step 2: Backend Setup

Open **PowerShell** and follow these steps:

#### 2.1 Navigate to Project
```powershell
cd D:\Intelligent-Traffic-Management-System
```

#### 2.2 Create Virtual Environment
```powershell
python -m venv .venv
```

#### 2.3 Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

✅ **Success:** You should see `(.venv)` prefix in your terminal

#### 2.4 Upgrade pip
```powershell
python -m pip install --upgrade pip
```

#### 2.5 Install Backend Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

**⏱️ Duration:** 2-3 minutes

#### 2.6 Install PyTorch (CPU Version)

> ⚠️ **IMPORTANT:** Run this command SEPARATELY after requirements.txt

```powershell
pip install torch==2.2.0+cpu torchvision==0.17.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

**⏱️ Duration:** 3-5 minutes (large download ~200MB)

#### 2.7 Verify Installation
```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Expected:** Server starts and prints `Firebase Admin SDK initialized`  
Press `Ctrl+C` to stop the server after verifying.

---

### Step 3: Frontend Setup (Web Dashboard)

#### 3.1 Install Flutter SDK

1. Download Flutter from: https://docs.flutter.dev/get-started/install/windows
2. Extract to `C:\flutter`
3. Add `C:\flutter\bin` to your system PATH

#### 3.2 Verify Flutter Installation
```powershell
flutter --version
```

✅ **Expected:** `Flutter 3.16.x • Dart 3.2.x` or newer

#### 3.3 Install Flutter Dependencies
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter pub get
```

---

### Step 4: Mobile App Setup (Android)

#### 4.1 Install Android Studio

1. Download from: https://developer.android.com/studio
2. Install and complete the setup wizard

#### 4.2 Install Required SDK Components

1. Open **Android Studio** → **File** → **Settings**
2. Go to **Languages & Frameworks** → **Android SDK**
3. **SDK Platforms** tab:
   - ✅ Check **Android 14.0 (API 34)**
4. **SDK Tools** tab:
   - ✅ Click **Show Package Details** (bottom right)
   - ✅ Expand **NDK (Side by side)** → select **27.0.12077973**
   - ✅ Check **Android SDK Build-Tools 34.0.0**
   - ✅ Check **Android SDK Command-line Tools (latest)**
5. Click **Apply** and wait for installation

#### 4.3 Accept Licenses
```powershell
flutter doctor --android-licenses
# Press 'y' for all prompts
```

#### 4.4 Place `google-services.json`

Make sure you have completed [Step 1 (Firebase Setup)](#step-1-firebase-setup) and placed the `google-services.json` file at:

```
frontend/android/app/google-services.json
```

> This file is required for Firebase initialization and FCM push notifications on Android.

#### 4.5 Verify Setup
```powershell
flutter doctor
```

✅ **Expected:** No issues for Android toolchain and connected devices

#### 4.6 Enable USB Debugging on Your Android Device

1. Go to **Settings** → **About Phone** → Tap **Build Number** 7 times to enable Developer Options
2. Go to **Settings** → **Developer Options** → Enable **USB Debugging**
3. Connect your device via USB cable
4. Accept the USB debugging prompt on the device

#### 4.7 Verify Device Connection
```powershell
flutter devices
```

✅ **Expected:** Your Android device should appear in the list

---

## 🚀 Running the System

### Start the Backend

**Terminal 1 — Backend Server:**
```powershell
cd D:\Intelligent-Traffic-Management-System
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Success:** `Uvicorn running on http://0.0.0.0:8000`

> The backend must be running before launching the web dashboard or mobile app.

---

### Run the Web Dashboard

**Terminal 2 — Web Dashboard (new PowerShell window):**
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter run -d chrome --web-port 8080
```

✅ **Success:** Admin dashboard opens at http://localhost:8080

---

### Run the Mobile App on Android

#### Step A: Set Up ADB Port Forwarding

> ⚠️ **CRITICAL** — The mobile app connects to `localhost:8000` which maps to the device itself. You must forward the port so the Android device can reach your PC's backend.

See the [ADB Port Forwarding](#-adb-port-forwarding-mobile--backend) section below.

#### Step B: Build and Run

**Terminal 3 — Mobile App (new PowerShell window):**
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter run
```

If multiple devices are connected, select your Android device when prompted or specify it:

```powershell
# List available devices
flutter devices

# Run on a specific device
flutter run -d <device-id>
```

✅ **Success:** The app installs and opens on your Android device showing the login screen.

#### Step C: First-Time Build

The first build takes **3-5 minutes** as Gradle downloads dependencies. Subsequent builds are faster.

If the first build fails, clean and retry:
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend
flutter clean
flutter pub get
flutter run
```

---

## 📡 ADB Port Forwarding (Mobile ↔ Backend)

The mobile app is configured to call the backend at `http://localhost:8000`. On an Android device, `localhost` refers to the device itself — **not** your PC. To fix this, use ADB reverse port forwarding to tunnel traffic from the device's `localhost:8000` to your PC's `localhost:8000`.

### Setup (Run Once per USB Connection)

```powershell
adb reverse tcp:8000 tcp:8000
```

✅ **Verify:** The command should output `8000`

### How It Works

```
Android Device (localhost:8000)  →  ADB Reverse Tunnel  →  PC (localhost:8000)
         ↑ Mobile App                                           ↑ FastAPI Backend
```

### Important Notes

- You must re-run `adb reverse tcp:8000 tcp:8000` every time you **reconnect** the USB cable
- The **backend must be running** on your PC before the app can communicate
- If using an **Android emulator** instead of a physical device, use `10.0.2.2:8000` as the host OR still use `adb reverse`
- To check active reverse forwards:
  ```powershell
  adb reverse --list
  ```
- To remove the reverse forward:
  ```powershell
  adb reverse --remove tcp:8000
  ```

### Wireless ADB (Optional)

If you prefer wireless debugging (no USB cable after initial setup):

```powershell
# 1. Connect device via USB first
# 2. Enable wireless debugging
adb tcpip 5555

# 3. Find device IP (Settings → Wi-Fi → your network → IP address)
adb connect <device-ip>:5555

# 4. Disconnect USB cable

# 5. Set up port forwarding over Wi-Fi
adb reverse tcp:8000 tcp:8000
```

---

### 📍 Access Points

| URL | Description |
|-----|-------------|
| http://localhost:8080 | 🖥️ Admin Web Dashboard |
| http://localhost:8000/docs | 📡 API Documentation (Swagger) |
| http://localhost:8000/redoc | 📖 API Documentation (ReDoc) |
| http://localhost:8000/detect | 🎥 Live Detection Stream |

---

## 🔐 Default Credentials

### Admin Login (Web Dashboard)

- **Username:** `admin`
- **Password:** `admin123`

### Driver Login (Mobile App)

Register a new driver through the app's sign-up flow using a phone number and license plate number, or use the admin dashboard to create driver accounts.

---

## 🔧 Troubleshooting

### ❌ Firebase Not Initializing

- Ensure `backend/firebase-service-account.json` exists (see [FIREBASE_SETUP.md](FIREBASE_SETUP.md))
- Ensure `frontend/android/app/google-services.json` exists for the mobile app
- Both files must be from the **same** Firebase project

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
cd D:\Intelligent-Traffic-Management-System\frontend
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

### ❌ Mobile App Can't Connect to Backend

1. Ensure the backend is running: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Ensure ADB port forwarding is set up:
   ```powershell
   adb reverse tcp:8000 tcp:8000
   ```
3. Check the forward is active:
   ```powershell
   adb reverse --list
   ```
4. Restart the app after setting up port forwarding

### ❌ Android Build Fails

**"NDK not found":**
1. Open **Android Studio** → **SDK Manager** → **SDK Tools**
2. Check **Show Package Details**
3. Install **NDK 27.0.12077973**

**"google-services.json not found":**
- Follow [FIREBASE_SETUP.md](FIREBASE_SETUP.md) Step 6 to download and place the file at `frontend/android/app/google-services.json`

**"Gradle build failed":**
```powershell
cd D:\Intelligent-Traffic-Management-System\frontend\android
.\gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

### ❌ ADB Device Not Found

```powershell
# Check connected devices
adb devices

# If no device listed:
# 1. Ensure USB debugging is enabled on the Android device
# 2. Try a different USB cable (use data cable, not charge-only)
# 3. Install device USB drivers from manufacturer website
# 4. Restart ADB server:
adb kill-server
adb start-server
adb devices
```

### ❌ Port Already in Use

```powershell
# Kill process using port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### ❌ Push Notifications Not Working

1. Ensure `google-services.json` (Android app) and `firebase-service-account.json` (backend) are from the **same** Firebase project
2. Check that FCM is enabled in Firebase Console
3. Ensure the device has Google Play Services installed
4. Check backend logs for FCM errors

---

## 📁 Project Structure

```
Intelligent-Traffic-Management-System/
├── backend/                    # FastAPI backend server
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Settings & environment config
│   │   ├── db/                # Firestore database layer
│   │   ├── detection/         # YOLOv8 vehicle & plate detection
│   │   ├── fuzzy/             # Fuzzy logic traffic controller
│   │   ├── parking/           # Parking violation detection
│   │   ├── routers/           # API route handlers
│   │   ├── scoring/           # Driver scoring system
│   │   ├── services/          # OCR, push notifications, etc.
│   │   ├── tracking/          # DeepSORT object tracking
│   │   ├── tts/               # Text-to-speech service
│   │   └── wokwi/             # IoT simulation integration
│   ├── requirements.txt       # Python dependencies
│   └── firebase-service-account.json  # 🔒 Firebase credentials (not in Git)
├── frontend/                   # Flutter app (web + mobile)
│   ├── lib/
│   │   ├── main.dart          # App entry point
│   │   ├── core/              # Theme, config, networking, services
│   │   ├── models/            # Data models
│   │   ├── providers/         # State management (Provider)
│   │   ├── screens/           # UI screens (admin + driver)
│   │   └── widgets/           # Reusable UI components
│   ├── android/               # Android-specific config
│   │   └── app/google-services.json  # 🔒 Firebase config (not in Git)
│   ├── pubspec.yaml           # Flutter dependencies
│   └── assets/                # Images, animations
├── models/                    # Trained ML models (.pt files)
├── data/                      # Training data, videos, snapshots
├── FIREBASE_SETUP.md          # 📖 Firebase setup guide
└── README.md                  # 📖 This file
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

**Version:** 2.0 (Final)  
**Date:** February 21, 2026
