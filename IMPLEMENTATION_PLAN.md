# Intelligent Traffic Management System - Implementation Plan
## Final Requirements (Supervisor Approved)

**Project ID:** 25-26J-330  
**Last Updated:** December 22, 2025  
**Status:** ✅ Requirements Finalized

---

## 📋 Team Member Assignments

| Member ID | Name | Focus Area | Key Deliverables |
|-----------|------|------------|------------------|
| IT22925572 | Gunarathna R.P | **Parking Violations & Dynamic Fines** | Predictive warnings, impact-based fines, grace period |
| IT22900890 | Randima K.M.G.D | **Junction Safety Scoring** | LiveSafeScore, lane weaving detection, community feedback |
| IT22363848 | Tennakoon I.M.S.R | **Adaptive Traffic Signals** | Fuzzy logic control, emergency override, Arduino prototype |
| IT22337580 | Palihakkara P.I | **Accident Risk Prediction** | Risk scoring, behavior detection, dashboard analytics |

---

## 🏗️ System Architecture (Finalized)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT TRAFFIC MANAGEMENT SYSTEM                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   VIDEO INPUT   │───▶│  YOLOv8 + SORT  │───▶│   VIOLATION     │        │
│  │  (Camera/File)  │    │   Detection     │    │   DETECTION     │        │
│  └─────────────────┘    └─────────────────┘    └────────┬────────┘        │
│                                                          │                 │
│         ┌────────────────────────────────────────────────┼─────────────┐   │
│         │                                                │             │   │
│         ▼                                                ▼             ▼   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   MEMBER 1      │    │   MEMBER 2      │    │   MEMBER 3      │        │
│  │ Dynamic Fines   │    │ LiveSafeScore   │    │ Traffic Signals │        │
│  │ Parking Alerts  │    │ Lane Weaving    │    │ Fuzzy Logic     │        │
│  │ Grace Period    │    │ Safety Score    │    │ Emergency Mode  │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                 │
│           └──────────────────────┼──────────────────────┘                 │
│                                  │                                         │
│                                  ▼                                         │
│                    ┌─────────────────────────┐                            │
│                    │      MEMBER 4           │                            │
│                    │   Accident Risk Score   │                            │
│                    │   Behavior Detection    │                            │
│                    └────────────┬────────────┘                            │
│                                 │                                          │
│           ┌─────────────────────┼─────────────────────┐                   │
│           ▼                     ▼                     ▼                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   SQLite DB     │  │   FastAPI       │  │   Arduino       │           │
│  │   (Violations,  │  │   REST API      │  │   (LED Traffic  │           │
│  │    Scores)      │  │   + SSE Events  │  │    Light+Buzzer)│           │
│  └─────────────────┘  └────────┬────────┘  └─────────────────┘           │
│                                │                                          │
│              ┌─────────────────┴─────────────────┐                        │
│              ▼                                   ▼                        │
│   ┌─────────────────────────┐     ┌─────────────────────────┐            │
│   │  FLUTTER WEB DASHBOARD  │     │   FLUTTER MOBILE APP    │            │
│   │  (Admin/Police Only)    │     │   (Drivers/Community)   │            │
│   │                         │     │                         │            │
│   │  • License Plates       │     │  • LiveSafeScore View   │            │
│   │  • Detection Video      │     │  • Personal Alerts      │            │
│   │  • Specific Fines       │     │  • My Violations/Fines  │            │
│   │  • Full Violation Log   │     │  • Junction Safety Map  │            │
│   │  • Simulate Ambulance   │     │  • Push Notifications   │            │
│   └─────────────────────────┘     └─────────────────────────┘            │
│                                                                           │
│              ▲ UNIFIED FLUTTER CODEBASE (Higher Distinction) ▲            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Privacy & Access Strategy

### **Flutter Web Dashboard (Admin/Police ONLY)**
| Feature | Access Level | Description |
|---------|--------------|-------------|
| License Plates | 🔒 Admin Only | Full OCR results, plate images |
| Detection Video | 🔒 Admin Only | Live MJPEG stream with overlays |
| Violation Details | 🔒 Admin Only | Complete fine breakdown, evidence |
| Driver Records | 🔒 Admin Only | Violation history per driver |
| Simulate Ambulance | 🔒 Admin Only | Digital twin emergency trigger |
| Analytics Dashboard | 🔒 Admin Only | All statistics and reports |

### **Flutter Mobile App (Drivers/Community)**
| Feature | Access Level | Description |
|---------|--------------|-------------|
| LiveSafeScore | 🌐 Public | Junction safety score (0-100) |
| Junction Map | 🌐 Public | Safety status of nearby junctions |
| Community Alerts | 🌐 Public | Broadcast warnings (anonymized) |
| My Violations | 🔐 Logged-in Driver | Personal violation history |
| My Fines | 🔐 Logged-in Driver | Outstanding fines, payment status |
| My Alerts | 🔐 Logged-in Driver | Personal warnings received |

---

## 🛠️ Tech Stack (Finalized)

### **Backend**
| Technology | Purpose | Status |
|------------|---------|--------|
| Python 3.11+ | Core runtime | ✅ Implemented |
| FastAPI | REST API + SSE | ✅ Implemented |
| YOLOv8 | Vehicle detection | ✅ Implemented |
| DeepSORT | Object tracking | ✅ Implemented |
| EasyOCR | License plate reading | ✅ Implemented |
| scikit-fuzzy | Traffic signal control | ✅ Implemented |
| SQLite/aiosqlite | Database | ✅ Implemented |
| edge-tts + pyttsx3 | Voice warnings | ✅ Implemented |

### **Frontend (UNIFIED CODEBASE)**
| Technology | Purpose | Status |
|------------|---------|--------|
| **Flutter Web** | Admin Dashboard | 🆕 To Implement |
| **Flutter Mobile** | Driver App (iOS/Android) | 🆕 To Implement |
| Dart | Programming language | 🆕 To Implement |

### **Hardware: 100% SOFTWARE APPROACH**
| Component | Status | Replacement |
|-----------|--------|-------------|
| ~~Arduino Mega 2560~~ | ❌ REMOVED | Software simulation |
| ~~LED Traffic Lights~~ | ❌ REMOVED | Flutter UI Widget |
| ~~Buzzer~~ | ❌ REMOVED | TTS Audio Alerts |
| ~~RFID Reader~~ | ❌ REMOVED | Visual AI Detection (YOLO) |
| ~~Weather Sensors~~ | ❌ REMOVED | Supervisor canceled |

**Note:** System is now 100% software-based. Emergency vehicles detected via YOLO (ambulance class).

---

## ✅ Currently Implemented Features

- ✅ YOLOv8 Vehicle Detection
- ✅ DeepSORT Multi-Object Tracking
- ✅ Custom License Plate Model (best_plate.pt)
- ✅ EasyOCR with Preprocessing
- ✅ Parking Zone Violation Detection
- ✅ Speed Estimation (pixel-based)
- ✅ Basic Fuzzy Logic Traffic Controller
- ✅ TTS Voice Warnings
- ✅ SQLite Database
- ✅ SSE Event Streaming
- ✅ Auto-Advancing Traffic Signals
- ✅ MJPEG Video Streaming

---

## 🎯 NEW FEATURES TO IMPLEMENT

---

### **MEMBER 1: Dynamic Fines & Parking Violations** (IT22925572)

#### **1.1 Predictive Warning System**
- [ ] **Pre-Violation Detection**
  - Detect vehicle slowing/stopping near no-parking zones
  - Trigger early warning before violation starts
  - Vehicle trajectory prediction

- [ ] **30-Second Grace Period**
  - Start countdown when vehicle enters violation zone
  - Escalating warnings: 10s → 20s → 30s
  - Auto-cancel if vehicle moves within grace period
  - Visual countdown on Admin Dashboard

#### **1.2 Dynamic Fine Calculation** *(Finalized Formula)*

```python
# FINALIZED FORMULA
Fine = Base_Penalty + (Duration_Seconds × Rate_Per_Second) + (Traffic_Impact × Multiplier)

# Where:
# Traffic_Impact = Count of OTHER moving vehicles in the frame during violation
# This measures how many vehicles are affected by the illegal parking
```

**Implementation Details:**
```python
def calculate_dynamic_fine(violation):
    # Base penalty by zone type
    BASE_PENALTIES = {
        'no_parking': 1000,      # LKR
        'handicap_zone': 2500,
        'fire_lane': 3000,
        'bus_stop': 1500,
        'school_zone': 2000
    }
    
    # Duration rate (per second)
    DURATION_RATE = 5  # LKR per second
    
    # Traffic impact multiplier
    TRAFFIC_MULTIPLIER = 50  # LKR per affected vehicle
    
    base = BASE_PENALTIES.get(violation.zone_type, 1000)
    duration_penalty = violation.duration_seconds * DURATION_RATE
    
    # Count OTHER moving vehicles in frame during violation
    traffic_impact = count_moving_vehicles_in_frame(violation.frame)
    impact_penalty = traffic_impact * TRAFFIC_MULTIPLIER
    
    total_fine = base + duration_penalty + impact_penalty
    
    return {
        'base_penalty': base,
        'duration_penalty': duration_penalty,
        'traffic_impact': traffic_impact,
        'impact_penalty': impact_penalty,
        'total_fine': total_fine
    }
```

#### **1.3 Violation Evidence Package**
- [ ] **For Admin Dashboard:**
  - License plate image (cropped)
  - Full frame screenshot
  - OCR result with confidence
  - Fine breakdown (base + duration + impact)
  - Timestamp and duration

- [ ] **For Driver Mobile App:**
  - Violation type and location
  - Fine amount (total only)
  - Payment status
  - Appeal option

---

### **MEMBER 2: Junction Safety Scoring** (IT22900890)

#### **2.1 LiveSafeScore System**

```python
# Junction Safety Score (0-100)
# Starts at 100, decreases with violations, recovers over time

VIOLATION_PENALTIES = {
    'lane_weaving': -5,
    'wrong_way_driving': -20,
    'improper_stopping': -8,
    'speeding': -10,
    'running_red_light': -25,
    'parking_violation': -3
}

# Score recovery: +1 point per 30 seconds without violations
# Minimum score: 0, Maximum score: 100
```

#### **2.2 Lane Weaving Detection** *(Finalized Formula)*

```python
# FINALIZED FORMULA
# Lane_Weaving = Detected if x_axis_velocity > threshold (zig-zag movement)

def detect_lane_weaving(vehicle_track):
    """
    Detect zig-zag/weaving movement by analyzing x-axis velocity changes.
    """
    X_VELOCITY_THRESHOLD = 15  # pixels per frame
    DIRECTION_CHANGES_THRESHOLD = 3  # minimum direction changes
    WINDOW_FRAMES = 30  # analysis window
    
    positions = vehicle_track.last_n_positions(WINDOW_FRAMES)
    
    x_velocities = []
    direction_changes = 0
    prev_direction = None
    
    for i in range(1, len(positions)):
        x_velocity = positions[i].x - positions[i-1].x
        x_velocities.append(abs(x_velocity))
        
        # Track direction changes (left/right)
        current_direction = 'left' if x_velocity < 0 else 'right'
        if prev_direction and current_direction != prev_direction:
            direction_changes += 1
        prev_direction = current_direction
    
    avg_x_velocity = sum(x_velocities) / len(x_velocities) if x_velocities else 0
    
    # Lane weaving detected if:
    # 1. Average x-axis velocity exceeds threshold AND
    # 2. Multiple direction changes (zig-zag pattern)
    is_weaving = (avg_x_velocity > X_VELOCITY_THRESHOLD and 
                  direction_changes >= DIRECTION_CHANGES_THRESHOLD)
    
    return {
        'is_weaving': is_weaving,
        'avg_x_velocity': avg_x_velocity,
        'direction_changes': direction_changes
    }
```

#### **2.3 Community Feedback (Mobile App)**
- [ ] **LiveSafeScore Display**
  - Real-time junction safety score (0-100)
  - Color-coded: Green (70-100), Yellow (40-69), Red (0-39)
  - Trend indicator (improving/declining)

- [ ] **Community Alerts (Anonymized)**
  - "High violation activity at Junction X"
  - "Junction safety declining - drive carefully"
  - No individual vehicle/plate information

- [ ] **Junction Map View**
  - Map with junction markers
  - Color-coded by safety score
  - Tap for details and recent alerts

---

### **MEMBER 3: Adaptive Traffic Signals** (IT22363848)

#### **3.1 4-Way Hybrid Junction Controller** *(NEW - Pure Software)*

Since we only have **one video feed**, we implement a **Hybrid 4-Way Controller**:

| Lane | Data Source | Description |
|------|-------------|-------------|
| **North** | REAL (YOLO) | Vehicle count from video detection |
| **South** | SIMULATED | Random density, updates every 10 seconds |
| **East** | SIMULATED | Random density, updates every 10 seconds |
| **West** | SIMULATED | Random density, updates every 10 seconds |
 show the 4 traffic lights seperatedly for simple identification

```python
# 4-WAY HYBRID JUNCTION CONTROLLER
# Lane North = Real YOLO data, Lanes S/E/W = Simulated

import random
import time

class FourWayTrafficController:
    """
    4-Way Junction Controller with Hybrid Data.
    - North: Real vehicle count from YOLO
    - South, East, West: Simulated traffic density
    """
    
    LANES = ['north', 'south', 'east', 'west']
    CYCLE_ORDER = ['north', 'east', 'south', 'west']  # Round-robin
    
    def __init__(self):
        self.lane_counts = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        self.lane_states = {'north': 'red', 'south': 'red', 'east': 'red', 'west': 'red'}
        self.current_green_lane = 'north'
        self.green_remaining = 30
        self.last_sim_update = time.time()
        self.sim_update_interval = 10  # seconds
        self.emergency_mode = False
        self.emergency_lane = None
        self.fuzzy_controller = FuzzyTrafficController()
    
    def get_simulated_density(self) -> dict:
        """Generate random traffic density for simulated lanes."""
        current_time = time.time()
        
        # Update simulated lanes every 10 seconds
        if current_time - self.last_sim_update >= self.sim_update_interval:
            self.lane_counts['south'] = random.randint(0, 20)
            self.lane_counts['east'] = random.randint(0, 20)
            self.lane_counts['west'] = random.randint(0, 20)
            self.last_sim_update = current_time
        
        return {
            'south': self.lane_counts['south'],
            'east': self.lane_counts['east'],
            'west': self.lane_counts['west']
        }
    
    def update_north_count(self, yolo_count: int):
        """Update North lane with real YOLO detection count."""
        self.lane_counts['north'] = yolo_count
    
    def activate_emergency_mode(self, lane: str = 'north'):
        """
        Activate emergency mode for a specific lane.
        Forces that lane GREEN, all others RED.
        """
        self.emergency_mode = True
        self.emergency_lane = lane
        for l in self.LANES:
            self.lane_states[l] = 'green' if l == lane else 'red'
        return {'status': 'emergency', 'green_lane': lane}
    
    def deactivate_emergency_mode(self):
        """Return to normal round-robin operation."""
        self.emergency_mode = False
        self.emergency_lane = None
    
    def tick(self) -> dict:
        """Advance the signal cycle. Called every second."""
        if self.emergency_mode:
            return self.get_all_states()
        
        self.green_remaining -= 1
        
        if self.green_remaining <= 0:
            # Move to next lane in cycle
            current_idx = self.CYCLE_ORDER.index(self.current_green_lane)
            next_idx = (current_idx + 1) % len(self.CYCLE_ORDER)
            next_lane = self.CYCLE_ORDER[next_idx]
            
            # Calculate green duration using fuzzy logic
            vehicle_count = self.lane_counts[next_lane]
            self.green_remaining = self.fuzzy_controller.compute_green_duration(vehicle_count)
            
            # Update states
            self.current_green_lane = next_lane
            for lane in self.LANES:
                self.lane_states[lane] = 'green' if lane == next_lane else 'red'
        
        return self.get_all_states()
    
    def get_all_states(self) -> dict:
        """Get current state of all 4 lanes."""
        self.get_simulated_density()  # Refresh simulated data
        return {
            'lanes': {
                lane: {
                    'state': self.lane_states[lane],
                    'vehicle_count': self.lane_counts[lane],
                    'is_real': lane == 'north'
                } for lane in self.LANES
            },
            'current_green': self.current_green_lane,
            'green_remaining': self.green_remaining,
            'emergency_mode': self.emergency_mode
        }
```

#### **3.2 Visual Emergency Detection (AI - YOLO Retrained)**

**Replaces Digital Twin button as PRIMARY trigger** (button kept as backup).

```python
# YOLO AMBULANCE DETECTION → EMERGENCY MODE TRIGGER
# Retrain YOLO with new class: ambulance (class_id = 8)

EMERGENCY_CLASS_IDS = {
    8: 'ambulance',
    # Future: 9: 'fire_truck', 10: 'police_car'
}

def check_for_emergency_vehicle(detections: List[Detection]) -> Optional[str]:
    """
    Check if any detection is an emergency vehicle.
    If found, return the vehicle type.
    """
    for det in detections:
        if det.class_id in EMERGENCY_CLASS_IDS:
            return EMERGENCY_CLASS_IDS[det.class_id]
    return None

# In detection loop:
if emergency_type := check_for_emergency_vehicle(detections):
    traffic_controller.activate_emergency_mode('north')  # Video = North lane
    play_tts(f"Emergency! {emergency_type} detected. Clearing North lane.")
```

**YOLO Retraining Task:**
- Old Classes: `car, bus, truck, tuk-tuk, plate`
- New Class: `ambulance` (class_id = 8)
- Dataset: Provided by Member 3

#### **3.3 Dashboard UI (Flutter Web) - 4-Way Intersection Widget**

**Replace "Arduino Status" with 4-Way Intersection Graphic:**

```
┌────────────────────────────────────────────────────┐
│                  4-WAY JUNCTION                    │
├────────────────────────────────────────────────────┤
│                                                    │
│                    NORTH (REAL)                    │
│                   🔴 🟡 🟢 (15)                    │
│                       │                            │
│                       │                            │
│   WEST (SIM)    ──────┼──────    EAST (SIM)       │
│   🔴 (8)              │            🔴 (12)         │
│                       │                            │
│                       │                            │
│                   SOUTH (SIM)                      │
│                   🔴 (6)                           │
│                                                    │
│   Green: NORTH | Remaining: 25s                    │
│   Emergency Mode: OFF                              │
└────────────────────────────────────────────────────┘
```

**Features:**
- Real-time light colors for all 4 directions
- Vehicle count labels (REAL vs SIM indicator)
- Current green lane highlighted
- Countdown timer
- Emergency mode indicator

#### **3.4 Hardware Status: 100% SOFTWARE**

| Component | Status | Replacement |
|-----------|--------|-------------|
| ~~Arduino Mega~~ | ❌ REMOVED | Software Digital Twin |
| ~~LED Lights~~ | ❌ REMOVED | Flutter UI Widget |
| ~~Buzzer~~ | ❌ REMOVED | TTS Audio Alerts |
| ~~Serial Communication~~ | ❌ REMOVED | REST API |

**Rationale:** Pure software approach is better for IT degree (more AI/algorithm focus, less hardware debugging).

---

### **MEMBER 4: Accident Risk Prediction** (IT22337580)

#### **4.1 Risk Score Calculation** *(Finalized Formula - No Weather)*

```python
# FINALIZED FORMULA (Weather component REMOVED per Supervisor)
Risk_Score = (Speed_Factor × 0.6) + (Violation_History_Factor × 0.4)

# Scale: 0-100 (higher = more dangerous)
```

**Implementation:**
```python
def calculate_risk_score(vehicle_id, current_speed, speed_limit):
    """
    Calculate accident risk score for a vehicle.
    
    Components:
    1. Speed Factor (60% weight) - How fast relative to limit
    2. Violation History Factor (40% weight) - Past behavior
    
    Note: Weather factor REMOVED per supervisor decision.
    """
    
    # ===== SPEED FACTOR (0-100) =====
    speed_ratio = current_speed / speed_limit if speed_limit > 0 else 1.0
    
    if speed_ratio <= 0.8:
        speed_factor = 0  # Safe speed
    elif speed_ratio <= 1.0:
        speed_factor = (speed_ratio - 0.8) * 100  # 0-20
    elif speed_ratio <= 1.2:
        speed_factor = 20 + (speed_ratio - 1.0) * 150  # 20-50
    elif speed_ratio <= 1.5:
        speed_factor = 50 + (speed_ratio - 1.2) * 166  # 50-100
    else:
        speed_factor = 100  # Maximum risk
    
    # ===== VIOLATION HISTORY FACTOR (0-100) =====
    violations = get_recent_violations(vehicle_id, days=30)
    
    violation_weights = {
        'speeding': 15,
        'parking_violation': 5,
        'lane_weaving': 20,
        'wrong_way_driving': 40,
        'running_red_light': 35,
        'improper_stopping': 10
    }
    
    history_score = 0
    for v in violations:
        history_score += violation_weights.get(v.type, 10)
    
    # Cap at 100
    violation_history_factor = min(100, history_score)
    
    # ===== FINAL RISK SCORE =====
    risk_score = (speed_factor * 0.6) + (violation_history_factor * 0.4)
    
    return {
        'risk_score': round(risk_score, 1),
        'speed_factor': round(speed_factor, 1),
        'violation_history_factor': round(violation_history_factor, 1),
        'risk_level': get_risk_level(risk_score)
    }

def get_risk_level(score):
    if score < 30:
        return 'LOW'
    elif score < 60:
        return 'MEDIUM'
    elif score < 80:
        return 'HIGH'
    else:
        return 'CRITICAL'
```

#### **4.2 Abnormal Driving Behavior Detection**
- [ ] **Sudden Stop Detection**
  - Threshold: >50% speed reduction in <2 seconds
  - Log as potential emergency braking

- [ ] **Harsh Braking Detection**
  - Threshold: Deceleration >8 m/s²
  - Contributes to violation history

- [ ] **Lane Drifting Detection**
  - Track vehicle centroid variance
  - Alert if consistently drifting toward lane edges

- [ ] **Wrong-Way Driving Detection**
  - Compare vehicle heading with expected lane direction
  - Immediate CRITICAL alert

#### **4.3 Dashboard Analytics (Flutter Web - Admin Only)**
- [ ] **Real-Time Risk Panel**
  - Live risk scores per detected vehicle
  - Color-coded vehicle overlays
  - Alert feed for high-risk events

- [ ] **Historical Analytics**
  - Risk score trends (hourly/daily/weekly)
  - Violation frequency charts
  - Peak risk hours identification

- [ ] **Incident Log**
  - Searchable violation/incident history
  - Export to CSV/PDF
  - Evidence attachments

---

## 💾 Database Schema (Updated)

```sql
-- =====================================================
-- EXISTING TABLES (Keep as-is)
-- =====================================================
-- violations, drivers, scores (already implemented)

-- =====================================================
-- NEW TABLES FOR MEMBER 1: Dynamic Fines
-- =====================================================

CREATE TABLE dynamic_fines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    violation_id INTEGER NOT NULL,
    zone_type TEXT NOT NULL,  -- 'no_parking', 'handicap_zone', etc.
    base_penalty REAL NOT NULL,
    duration_seconds INTEGER NOT NULL,
    duration_penalty REAL NOT NULL,
    traffic_impact INTEGER NOT NULL,  -- Count of other moving vehicles
    impact_penalty REAL NOT NULL,
    total_fine REAL NOT NULL,
    payment_status TEXT DEFAULT 'unpaid',  -- 'unpaid', 'paid', 'disputed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (violation_id) REFERENCES violations(id)
);

CREATE TABLE grace_period_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    plate_number TEXT,
    zone_type TEXT NOT NULL,
    warning_start TIMESTAMP NOT NULL,
    warning_level INTEGER DEFAULT 1,  -- 1, 2, 3 (escalating)
    vehicle_moved BOOLEAN DEFAULT FALSE,
    violation_recorded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- NEW TABLES FOR MEMBER 2: Junction Safety
-- =====================================================

CREATE TABLE junction_safety (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    junction_id TEXT NOT NULL DEFAULT 'main',
    safety_score INTEGER NOT NULL CHECK(safety_score >= 0 AND safety_score <= 100),
    last_violation_type TEXT,
    last_violation_severity INTEGER,
    violations_last_hour INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lane_weaving_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    avg_x_velocity REAL NOT NULL,
    direction_changes INTEGER NOT NULL,
    duration_frames INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE community_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    junction_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- 'warning', 'danger', 'critical'
    message TEXT NOT NULL,
    safety_score_at_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- NEW TABLES FOR MEMBER 3: Traffic Signals
-- =====================================================

CREATE TABLE emergency_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_type TEXT NOT NULL,  -- 'ambulance', 'fire_truck', 'police'
    trigger_type TEXT NOT NULL,  -- 'simulation' (Digital Twin)
    override_start TIMESTAMP NOT NULL,
    override_end TIMESTAMP,
    duration_seconds INTEGER,
    signal_state_before TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE signal_timing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_count INTEGER NOT NULL,
    traffic_level TEXT NOT NULL,  -- 'low', 'medium', 'high'
    green_duration INTEGER NOT NULL,
    yellow_duration INTEGER NOT NULL,
    red_duration INTEGER NOT NULL,
    emergency_mode BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- NEW TABLES FOR MEMBER 4: Risk Prediction
-- =====================================================

CREATE TABLE risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    plate_number TEXT,
    risk_score REAL NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100),
    speed_factor REAL NOT NULL,
    violation_history_factor REAL NOT NULL,
    risk_level TEXT NOT NULL,  -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    current_speed REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE abnormal_behavior_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    behavior_type TEXT NOT NULL,  -- 'sudden_stop', 'harsh_brake', 'lane_drift', 'wrong_way'
    severity TEXT NOT NULL,  -- 'warning', 'danger', 'critical'
    details TEXT,  -- JSON with specific measurements
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE incident_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type TEXT NOT NULL,
    risk_score_at_time REAL,
    vehicles_involved TEXT,  -- JSON array of vehicle IDs
    description TEXT,
    evidence_path TEXT,
    auto_generated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- USER TABLES FOR FLUTTER APPS
-- =====================================================

CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin',  -- 'admin', 'police', 'supervisor'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE driver_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT,
    license_number TEXT,
    vehicle_plates TEXT,  -- JSON array of registered plates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE driver_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,  -- 'violation', 'fine', 'warning', 'community'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES driver_users(id)
);
```

---

## 📡 API Endpoints (Updated)

### **Public Endpoints (No Auth)**
```python
GET  /health                          # System health check
GET  /junction/safety-score           # LiveSafeScore (public)
GET  /junction/community-alerts       # Recent anonymized alerts
```

### **Driver App Endpoints (Auth Required)**
```python
POST /auth/driver/login               # Phone OTP login
GET  /driver/me                       # Driver profile
GET  /driver/my-violations            # Personal violation history
GET  /driver/my-fines                 # Outstanding fines
GET  /driver/my-alerts                # Personal notifications
POST /driver/register-plate           # Register vehicle plate
```

### **Admin Dashboard Endpoints (Admin Auth Required)**
```python
POST /auth/admin/login                # Admin login
GET  /admin/violations                # All violations with plates
GET  /admin/violations/{id}           # Full violation details + evidence
GET  /admin/video/stream              # Live detection video (MJPEG)
GET  /admin/analytics/overview        # Dashboard statistics
GET  /admin/analytics/risk-scores     # Risk score data
GET  /admin/fines                     # All fines with breakdown
POST /admin/fines/{id}/adjust         # Adjust fine amount
```

### **Member-Specific Endpoints**

```python
# MEMBER 1: Dynamic Fines
GET  /violations/{id}/fine-breakdown  # Detailed fine calculation
POST /violations/grace-period/start   # Start grace period countdown
POST /violations/grace-period/cancel  # Vehicle moved, cancel warning

# MEMBER 2: Junction Safety
GET  /junction/safety-score           # Current LiveSafeScore
GET  /junction/safety-history         # Score over time
GET  /junction/lane-weaving-events    # Recent weaving detections
POST /junction/broadcast-alert        # Send community notification

# MEMBER 3: Traffic Signals
GET  /signal/status                   # Current signal state
POST /signal/simulate-emergency       # "Simulate Ambulance" button
GET  /signal/emergency-log            # Emergency override history
GET  /signal/timing-history           # Fuzzy logic decisions

# MEMBER 4: Risk Prediction
GET  /risk/current-scores             # All vehicle risk scores
GET  /risk/vehicle/{id}               # Specific vehicle risk
GET  /risk/high-risk-vehicles         # Vehicles above threshold
GET  /risk/behavior-log               # Abnormal behavior history
GET  /risk/incidents                  # Auto-generated incident reports
```

---

## 📱 Flutter App Structure

### **Unified Codebase Structure**
```
flutter_app/
├── lib/
│   ├── main.dart                     # Entry point
│   ├── app/
│   │   ├── app.dart                  # App configuration
│   │   └── routes.dart               # Navigation routes
│   │
│   ├── core/
│   │   ├── api/
│   │   │   └── api_service.dart      # FastAPI client
│   │   ├── auth/
│   │   │   ├── admin_auth.dart       # Admin authentication
│   │   │   └── driver_auth.dart      # Driver authentication
│   │   └── theme/
│   │       └── app_theme.dart        # Shared theme
│   │
│   ├── features/
│   │   ├── admin/                    # ADMIN DASHBOARD (Web)
│   │   │   ├── dashboard/
│   │   │   │   └── admin_dashboard_screen.dart
│   │   │   ├── violations/
│   │   │   │   ├── violations_list_screen.dart
│   │   │   │   └── violation_detail_screen.dart
│   │   │   ├── video/
│   │   │   │   └── live_video_screen.dart
│   │   │   ├── fines/
│   │   │   │   └── fines_management_screen.dart
│   │   │   ├── analytics/
│   │   │   │   └── analytics_screen.dart
│   │   │   └── emergency/
│   │   │       └── simulate_emergency_screen.dart
│   │   │
│   │   └── driver/                   # DRIVER APP (Mobile)
│   │       ├── home/
│   │       │   └── driver_home_screen.dart
│   │       ├── safety/
│   │       │   ├── live_safe_score_screen.dart
│   │       │   └── junction_map_screen.dart
│   │       ├── violations/
│   │       │   └── my_violations_screen.dart
│   │       ├── fines/
│   │       │   └── my_fines_screen.dart
│   │       └── alerts/
│   │           └── notifications_screen.dart
│   │
│   ├── shared/
│   │   ├── widgets/
│   │   │   ├── safety_score_gauge.dart
│   │   │   ├── risk_indicator.dart
│   │   │   └── violation_card.dart
│   │   └── models/
│   │       ├── violation.dart
│   │       ├── fine.dart
│   │       ├── junction_safety.dart
│   │       └── risk_score.dart
│   │
│   └── utils/
│       ├── constants.dart
│       └── helpers.dart
│
├── web/                              # Flutter Web assets
├── android/                          # Android config
├── ios/                              # iOS config
└── pubspec.yaml                      # Dependencies
```

---

## 📅 Implementation Timeline

### **Sprint 1 (Weeks 1-2): Core Backend Enhancements**
| Task | Member | Status |
|------|--------|--------|
| Dynamic fine calculation algorithm | Member 1 | 🔲 |
| Grace period warning system | Member 1 | 🔲 |
| LiveSafeScore calculation engine | Member 2 | 🔲 |
| Lane weaving detection algorithm | Member 2 | 🔲 |
| Emergency override API | Member 3 | 🔲 |
| Risk score calculation | Member 4 | 🔲 |
| Database schema migration | All | 🔲 |

### **Sprint 2 (Weeks 3-4): Flutter App Foundation**
| Task | Member | Status |
|------|--------|--------|
| Flutter project setup (unified codebase) | All | 🔲 |
| Admin authentication system | All | 🔲 |
| Driver authentication (phone OTP) | All | 🔲 |
| API service layer | All | 🔲 |
| Shared widgets library | All | 🔲 |

### **Sprint 3 (Weeks 5-6): Admin Dashboard (Flutter Web)**
| Task | Member | Status |
|------|--------|--------|
| Live video streaming page | Member 1 | 🔲 |
| Violations list with plates | Member 1 | 🔲 |
| Fine breakdown view | Member 1 | 🔲 |
| Safety score dashboard | Member 2 | 🔲 |
| Simulate Ambulance button | Member 3 | 🔲 |
| Risk analytics dashboard | Member 4 | 🔲 |

### **Sprint 4 (Weeks 7-8): Driver Mobile App**
| Task | Member | Status |
|------|--------|--------|
| LiveSafeScore display | Member 2 | 🔲 |
| Junction map with scores | Member 2 | 🔲 |
| My violations screen | Member 1 | 🔲 |
| My fines screen | Member 1 | 🔲 |
| Push notifications | All | 🔲 |
| Community alerts feed | Member 2 | 🔲 |

### **Sprint 5 (Weeks 9-10): AI Enhancement & Integration**
| Task | Member | Status |
|------|--------|--------|
| Retrain YOLO with ambulance class | Member 3 | 🔲 |
| 4-way junction UI widget (Flutter) | Member 3 | 🔲 |
| Visual emergency detection logic | Member 3 | 🔲 |
| Simulated lane data generator | Member 3 | 🔲 |
| System integration testing | All | 🔲 |

### **Sprint 6 (Weeks 11-12): Polish & Documentation**
| Task | Member | Status |
|------|--------|--------|
| UI/UX refinement | All | 🔲 |
| Performance optimization | All | 🔲 |
| User documentation | All | 🔲 |
| Demo video recording | All | 🔲 |
| Final presentation prep | All | 🔲 |

---

## 🎯 Success Metrics

### **Member 1: Dynamic Fines & Parking**
| Metric | Target |
|--------|--------|
| Pre-violation warning accuracy | >85% |
| Grace period violation reduction | 40-60% |
| Fine calculation latency | <500ms |
| Traffic impact measurement accuracy | >90% |

### **Member 2: Junction Safety**
| Metric | Target |
|--------|--------|
| Lane weaving detection accuracy | >85% |
| Wrong-way driving detection | 100% |
| LiveSafeScore update latency | <1s |
| Community alert delivery time | <2s |

### **Member 3: Traffic Signals**
| Metric | Target |
|--------|--------|
| Emergency override activation time | <1s |
| Fuzzy logic decision accuracy | >90% |
| Arduino sync latency | <100ms |
| Signal state transition reliability | 99.9% |

### **Member 4: Risk Prediction**
| Metric | Target |
|--------|--------|
| Risk score calculation latency | <200ms |
| High-risk prediction precision | >80% |
| Abnormal behavior detection recall | >85% |
| False positive rate | <15% |

---

## 🚀 Quick Start Commands

```bash
# Backend (existing)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Flutter App Setup (new)
cd flutter_app
flutter pub get
flutter run -d chrome          # Run Web Dashboard
flutter run -d android          # Run Mobile App (Android)
flutter run -d ios              # Run Mobile App (iOS)

# No Arduino - 100% Software System
# Emergency vehicles detected via YOLO (ambulance class)

# Database Migration (new)
python backend/migrate_db.py
```

---

## 📝 Key Decisions Summary

| Decision | Rationale |
|----------|-----------|
| **Flutter for Both Web & Mobile** | Unified codebase = higher marks |
| **No Streamlit** | Flutter Web provides better integration |
| **Digital Twin for RFID** | Avoids hardware complexity, still demonstrates concept |
| **No Weather Sensors** | Supervisor removed this requirement |
| **100% Software (No Arduino)** | Pure AI/Software approach, better for IT degree |
| **Privacy Split (Admin vs Driver)** | Police see plates, public sees aggregate scores |
| **Traffic Impact = Moving Vehicle Count** | Simple, measurable metric |
| **Risk Score = Speed + History (No Weather)** | Clean formula, supervisor approved |

---

## ⚠️ Removed Features (Supervisor Decision)

| Feature | Reason |
|---------|--------|
| ~~Streamlit Dashboard~~ | Replaced with Flutter Web |
| ~~RFID Reader Hardware~~ | Replaced with Visual AI Detection (YOLO) |
| ~~Weather/Rain Sensors~~ | Supervisor canceled |
| ~~Weather Factor in Risk Score~~ | Removed from formula |
| ~~Separate Public Website~~ | Consolidated into Mobile App |
| ~~Arduino/LED Hardware~~ | 100% Software approach, Digital Twin UI |
| ~~Buzzer/Serial Comm~~ | Replaced with TTS audio alerts |

---

**This plan reflects the finalized requirements approved by the team and supervisor. Follow this document as the single source of truth for implementation.**
