# Intelligent Traffic Management System - Implementation Plan
## Feature Integration from Team Proposals

**Project ID:** 25-26J-330  
**Last Updated:** December 22, 2025

---

## 📋 Team Member Proposals Summary

### **IT22925572 - Parking Violation Management (Gunarathna R.P)**
**Focus:** Predictive parking violation detection with dynamic fines and impact-based penalties

### **IT22900890 - LiveSafe Junction Scoring (Randima K.M.G.D)**
**Focus:** Junction-level safety scoring system without ANPR, community-wide feedback

### **IT22363848 - Adaptive Traffic Signal Control (Tennakoon I.M.S.R)**
**Focus:** Fuzzy logic + ML-based adaptive signal timing with emergency vehicle priority

### **IT22337580 - Accident Risk Prediction (Palihakkara P.I)**
**Focus:** Real-time accident risk scoring and interactive dashboard with predictive analytics

---

## ✅ Currently Implemented Features

- ✅ **YOLOv8 Vehicle Detection** - Real-time object detection
- ✅ **DeepSORT Tracking** - Multi-object tracking with persistent IDs
- ✅ **License Plate Detection** - Custom trained best_plate.pt model
- ✅ **EasyOCR Integration** - Text recognition with preprocessing
- ✅ **Parking Duration Estimation** - Per-vehicle parking time tracking
- ✅ **No-Parking Zone Detection** - Polygon-based zone violation detection
- ✅ **Speed Estimation** - Pixel-based motion speed calculation
- ✅ **Basic Violation Penalties** - Parking/speeding violation recording
- ✅ **TTS Voice Warnings** - edge-tts + pyttsx3 audio alerts
- ✅ **SQLite Database** - Local violation persistence
- ✅ **Fuzzy Logic Traffic Controller** - Basic adaptive signal timing
- ✅ **SSE Event Streaming** - Real-time updates to frontend
- ✅ **Auto-Advancing Traffic Signals** - Time-based automatic state transitions

---

## 🎯 NEW FEATURES TO IMPLEMENT

### **Phase 1: Parking Violation Enhancements** (IT22925572)

#### **1.1 Predictive Warning System** 🚨
- [ ] **Pre-Violation Detection**
  - Detect vehicle intent to park before actual violation occurs
  - Analyze vehicle slowing patterns near no-parking zones
  - Trigger early warnings via visual/audio alerts
  
- [ ] **30-Second Grace Period**
  - Implement countdown timer before violation is recorded
  - Escalating alerts (10s warning → 20s warning → 30s final warning)
  - Cancel violation if vehicle moves within grace period

#### **1.2 Dynamic Fine Calculation Algorithm** 💰
```python
Fine = Base_Penalty + (Duration × Rate) + (Traffic_Impact × Cost)
```

**Components to implement:**
- [ ] **Base Penalty Matrix**
  - Violation type-based base fines (no-parking, handicap zone, fire lane)
  - Time-of-day multipliers (peak hours = higher fine)
  - Zone-specific base penalties (hospital zone, school zone)

- [ ] **Duration-Based Penalty**
  - Per-minute rate calculation
  - Progressive rate increase (first 5 min = Rs.10/min, 5-15 min = Rs.20/min, etc.)
  - Maximum duration cap

- [ ] **Traffic Impact Quantification**
  - Lane blockage percentage measurement
  - Queue length caused by violation
  - Speed reduction in affected lane
  - Financial impact formula: `(Vehicles_Affected × Avg_Delay_Seconds × Rs.5_per_second)`

#### **1.3 Arduino LCD/LED Physical Displays** 🖥️
- [ ] **Hardware Integration**
  - Arduino serial communication protocol
  - Multi-zone LED matrix configuration
  - LCD text display for violation details

- [ ] **Display Features**
  - Real-time violation countdown (30s grace period)
  - QR code generation for fine payment
  - Rotating display for multiple violations
  - Vehicle identification by color/type (no plate needed)

#### **1.4 Web Payment Portal** 🌐
- [ ] **QR-Linked Violation Pages**
  - Unique QR code per violation
  - Photo evidence display
  - Vehicle characteristics (color, type, timestamp)
  - Fine breakdown (base + duration + impact)
  - Mock payment interface (Stripe/PayHere integration)

---

### **Phase 2: Junction Safety Scoring** (IT22900890)

#### **2.1 LiveSafeScore System** 🎯
- [ ] **Junction-Level Safety Score (0-100)**
  - Calculate real-time safety score based on violations detected
  - Weighted violation severity matrix:
    - Lane weaving: -5 points
    - Wrong-way driving: -15 points
    - Improper stopping: -8 points
    - Speeding: -10 points
    - Running red light: -20 points

- [ ] **Score Decay Algorithm**
  - Time-based score recovery (no violations = +2 points per minute)
  - Maximum recovery rate limits
  - Historical average calculation

#### **2.2 Community-Wide Feedback** 📢
- [ ] **Digital Display Boards**
  - Real-time junction safety score display
  - Recent violation types with anonymized data
  - Traffic flow health indicators

- [ ] **Mobile Push Notifications**
  - Broadcast warnings when score drops below thresholds:
    - Score < 70: "Caution - High violation activity"
    - Score < 50: "Danger - Junction unsafe"
    - Score < 30: "Critical - Avoid if possible"
  
- [ ] **No ANPR Approach**
  - Privacy-preserving community alerts
  - Focus on aggregate safety, not individual punishment
  - Vehicle type/color-based tracking (no plate reading required)

#### **2.3 Context-Aware Violation Detection** 🧠
- [ ] **Time-of-Day Weighting**
  - School zones: higher severity during 7-9 AM, 2-4 PM
  - Hospital zones: 24/7 critical monitoring
  - Business districts: peak hour emphasis

- [ ] **Traffic Density Adjustment**
  - High traffic: lane change violations weighted higher
  - Low traffic: speeding violations weighted higher
  - Adaptive severity calculation

- [ ] **Weather/Visibility Integration**
  - Rain detection (image processing or API)
  - Reduced visibility penalty adjustments
  - Night-time violation severity increase

#### **2.4 Violation Classification** 🏷️
- [ ] **Lane Weaving Detection**
  - Track vehicle trajectory across lanes
  - Detect frequent lane changes (>3 changes in 30s)
  - Calculate weaving severity score

- [ ] **Wrong-Way Driving Detection**
  - Lane direction mapping
  - Heading vector analysis
  - Immediate high-priority alert

- [ ] **Improper Bus Stop Violations**
  - Detect non-bus vehicles in bus-only zones
  - Time-based violations (parking >30s at bus stop)
  - Bus arrival detection (skip penalty when bus present)

---

### **Phase 3: Enhanced Fuzzy Logic Traffic Control** (IT22363848)

#### **3.1 Advanced Adaptive Signal Control** 🚦
- [ ] **Multi-Sensor Data Integration**
  - **Already have:** Vehicle count from YOLOv8
  - **To add:**
    - Ultrasonic distance sensors (vehicle queue length)
    - RFID readers (emergency vehicle detection)
    - Speed sensors (average approach speed)

- [ ] **Enhanced Fuzzy Membership Functions**
  - Traffic volume: Very Low, Low, Medium, High, Very High
  - Queue length: Short, Medium, Long, Critical
  - Waiting time: Acceptable, Long, Excessive
  - Emergency status: None, Approaching, Present

- [ ] **Advanced Fuzzy Rules**
  ```
  IF traffic_volume = "High" AND queue_length = "Critical" 
     THEN green_duration = "Maximum"
  
  IF emergency_vehicle = "Present" 
     THEN override_signal = "Green" AND clear_path = True
  
  IF traffic_volume = "Very Low" AND time = "Night" 
     THEN yellow_duration = "Short" AND cycle_time = "Minimal"
  ```

#### **3.2 Emergency Vehicle Priority (RFID)** 🚑
- [ ] **RFID Tag Detection**
  - RFID readers at junction approaches (100m, 50m, 20m zones)
  - Emergency vehicle tag database
  - Real-time tag authentication

- [ ] **Priority Protocol**
  1. Detect RFID tag at 100m → Pre-empt next cycle
  2. Detect at 50m → Force current green phase extension
  3. Detect at 20m → Immediate all-red + emergency green
  4. Clear cross-traffic for safe passage
  5. Resume normal operation after vehicle passes

- [ ] **Visual/Audio Alerts**
  - LED strobe lights on signal poles
  - Audio siren ("Emergency vehicle approaching")
  - Dashboard emergency mode activation

#### **3.3 Machine Learning Optimization** 🤖
- [ ] **Historical Pattern Learning**
  - Collect hourly traffic patterns (7 days minimum)
  - Peak hour identification
  - Seasonal trend analysis

- [ ] **Predictive Signal Timing**
  - Forecast traffic volume 5-10 minutes ahead
  - Pre-adjust signal timing before congestion builds
  - Adaptive learning from feedback

- [ ] **Multi-Junction Coordination**
  - Green wave optimization
  - Progressive signal timing (30 mph green wave)
  - Minimize stop-and-go traffic

#### **3.4 Physical LED Prototype** 💡
- [ ] **Arduino-Controlled Traffic Lights**
  - 4-way junction LED model
  - Red, yellow, green LEDs per direction
  - Synchronized with software simulation
  - Real-time state visualization

---

### **Phase 4: Accident Risk Prediction & Dashboard** (IT22337580)

#### **4.1 Real-Time Risk Score Calculation** ⚠️
```python
Risk_Score = (Speed_Risk × 0.4) + (Distance_Risk × 0.3) + 
             (Violation_Risk × 0.2) + (Behavior_Risk × 0.1)
```

**Components:**
- [ ] **Speed Risk Assessment**
  - Calculate deviation from speed limit
  - Time-to-collision estimation
  - Excessive speed weighting

- [ ] **Distance Risk (Following Distance)**
  - Measure inter-vehicle distance
  - Calculate safe following distance based on speed
  - Tailgating detection and scoring

- [ ] **Violation Risk**
  - Recent violation history per vehicle
  - Violation recency weighting (recent = higher risk)
  - Accumulative violation score

- [ ] **Behavior Risk (Abnormal Driving)**
  - Sudden stops detection (rapid deceleration)
  - Harsh braking events
  - Lane drifting (vehicle position variance)
  - Erratic steering patterns

#### **4.2 Abnormal Driving Behavior Detection** 🚗
- [ ] **Sudden Stop Detection**
  - Track vehicle velocity changes
  - Threshold: >50% speed reduction in <2 seconds
  - Log incident with timestamp and location

- [ ] **Harsh Braking Detection**
  - Deceleration rate calculation
  - Threshold: >8 m/s² deceleration
  - Proximity analysis (potential collision avoidance)

- [ ] **Lane Drifting Detection**
  - Track vehicle centroid position
  - Detect lane boundary crossings without signaling
  - Weaving pattern recognition

- [ ] **Wrong-Way Driving Detection**
  - Lane direction validation
  - Heading vector mismatch
  - Immediate critical alert

#### **4.3 Interactive Streamlit Dashboard** 📊
- [ ] **Real-Time Monitoring Panel**
  - Live video feed with risk overlays
  - Current accident risk score (color-coded: Green <30, Yellow 30-70, Red >70)
  - Active alerts panel
  - Vehicle count and speed statistics

- [ ] **Predictive Risk Visualization**
  - Risk score graph (last 60 seconds)
  - Heatmap of high-risk zones
  - Time-series risk trend analysis

- [ ] **Traffic Heatmaps**
  - Speed heatmap (color by speed zones)
  - Violation density heatmap
  - Accident-prone area highlighting
  - Historical incident overlay

- [ ] **Live Data Visualizations**
  - Speed distribution histogram
  - Vehicle type breakdown (pie chart)
  - Violation type frequency (bar chart)
  - Hourly traffic patterns (line graph)

#### **4.4 Incident Logging & Reporting** 📝
- [ ] **Comprehensive Incident Database**
  - Timestamp, location, vehicle ID
  - Risk score at time of incident
  - Contributing factors (speed, behavior, violations)
  - Photo/video evidence

- [ ] **Automatic Report Generation**
  - Daily incident summary (PDF/CSV export)
  - Weekly trend analysis
  - Monthly safety metrics report
  - Executive dashboard summaries

- [ ] **Auditing Tools**
  - Search incidents by date/location/type
  - Filter by risk score threshold
  - Export filtered data for analysis
  - Generate charts from historical data

---

## 🛠️ Technical Implementation Details

### **Database Schema Updates**

```sql
-- New tables required

CREATE TABLE dynamic_fines (
    id INTEGER PRIMARY KEY,
    violation_id INTEGER REFERENCES violations(id),
    base_penalty REAL,
    duration_penalty REAL,
    traffic_impact_penalty REAL,
    total_fine REAL,
    lane_blockage_percent REAL,
    vehicles_affected INTEGER,
    avg_delay_seconds REAL,
    calculated_at TIMESTAMP
);

CREATE TABLE junction_safety_scores (
    id INTEGER PRIMARY KEY,
    junction_id TEXT,
    safety_score INTEGER,  -- 0-100
    violation_count_last_hour INTEGER,
    last_violation_type TEXT,
    last_violation_severity INTEGER,
    timestamp TIMESTAMP
);

CREATE TABLE accident_risk_scores (
    id INTEGER PRIMARY KEY,
    vehicle_id INTEGER,
    risk_score REAL,  -- 0-100
    speed_risk REAL,
    distance_risk REAL,
    violation_risk REAL,
    behavior_risk REAL,
    abnormal_behavior TEXT,  -- JSON: {sudden_stop: True, harsh_brake: False}
    timestamp TIMESTAMP
);

CREATE TABLE incident_log (
    id INTEGER PRIMARY KEY,
    incident_type TEXT,  -- 'near_miss', 'harsh_brake', 'lane_drift', etc.
    risk_score REAL,
    vehicle_id INTEGER,
    location TEXT,
    timestamp TIMESTAMP,
    evidence_path TEXT,  -- path to video/image
    contributing_factors TEXT  -- JSON
);

CREATE TABLE emergency_vehicle_log (
    id INTEGER PRIMARY KEY,
    rfid_tag TEXT,
    vehicle_type TEXT,  -- 'ambulance', 'fire_truck', 'police'
    detection_distance INTEGER,  -- meters from junction
    signal_override_duration INTEGER,  -- seconds
    timestamp TIMESTAMP
);
```

### **New API Endpoints**

```python
# Parking violation enhancements
POST /violations/predict-warning  # Pre-violation alert
GET  /violations/{id}/fine-breakdown  # Dynamic fine calculation
GET  /violations/qr/{code}  # QR-linked payment page

# Junction safety
GET  /junction/safety-score  # Current LiveSafeScore
POST /junction/broadcast-alert  # Community notification
GET  /junction/violation-stats  # Aggregate violation data

# Traffic signal control
POST /signal/emergency-override  # RFID emergency activation
GET  /signal/coordination-status  # Multi-junction sync status
PUT  /signal/ml-optimize  # Trigger ML optimization

# Accident risk prediction
GET  /risk/current-score  # Real-time risk assessment
GET  /risk/heatmap  # Risk zone heatmap data
GET  /incidents/log  # Incident history
POST /incidents/report  # Auto-generate report
GET  /dashboard/stats  # Streamlit dashboard data feed
```

### **Hardware Integration Requirements**

**Arduino Components:**
- Arduino Mega 2560 (for multiple I/O pins)
- 16x2 LCD Display (violation text)
- 8x8 LED Matrix (QR code display)
- RFID Reader Module (RC522)
- Traffic Light LEDs (Red, Yellow, Green x 4 directions)
- Ultrasonic Sensors (HC-SR04 for queue length)
- Buzzer (audio alerts)

**Communication Protocol:**
- Serial USB connection (9600 baud)
- JSON message format: `{"type": "violation", "vehicle_id": 123, "countdown": 30}`
- Bi-directional updates (Arduino → PC for sensor data, PC → Arduino for display commands)

---

## 📅 Implementation Timeline

### **Sprint 1 (Weeks 1-2): Parking Violation Enhancements**
- Dynamic fine calculation algorithm
- Pre-violation detection logic
- 30-second grace period implementation
- Traffic impact quantification

### **Sprint 2 (Weeks 3-4): Arduino Integration**
- LCD/LED display hardware setup
- Serial communication protocol
- QR code generation
- Web payment portal (mock)

### **Sprint 3 (Weeks 5-6): Junction Safety Scoring**
- LiveSafeScore calculation engine
- Community broadcast notifications
- Context-aware violation weighting
- No-ANPR vehicle tracking

### **Sprint 4 (Weeks 7-8): Enhanced Traffic Signals**
- RFID emergency vehicle detection
- ML-based traffic prediction
- Multi-junction coordination
- Physical LED prototype

### **Sprint 5 (Weeks 9-10): Accident Risk Prediction**
- Risk score calculation algorithm
- Abnormal behavior detection
- Incident logging database
- Streamlit dashboard (basic)

### **Sprint 6 (Weeks 11-12): Dashboard & Reporting**
- Complete Streamlit dashboard
- Heatmap visualizations
- Automatic report generation
- System integration testing

---

## 🎯 Success Metrics

### **Parking Violation Module (IT22925572)**
- 40-60% reduction in illegal parking through warnings alone
- 90%+ accuracy in traffic impact calculation
- <2s pre-violation warning latency

### **Junction Safety Module (IT22900890)**
- Junction safety score correlation >0.8 with actual accident rates
- 100% violation detection rate for critical infractions (wrong-way, red light)
- <1s broadcast notification delay

### **Traffic Signal Module (IT22363848)**
- 30-50% reduction in average wait time during peak hours
- 95%+ emergency vehicle priority activation success rate
- <3s signal override response time for emergencies

### **Accident Risk Module (IT22337580)**
- 85%+ accuracy in high-risk event prediction
- <500ms risk score calculation latency
- 90%+ precision in abnormal behavior detection

---

## 🔧 Development Tools & Technologies

### **Backend**
- Python 3.11+
- FastAPI (existing)
- YOLOv8 (existing)
- DeepSORT (existing)
- scikit-fuzzy (existing)
- **NEW:** scikit-learn (ML models)
- **NEW:** TensorFlow/PyTorch (advanced ML)
- **NEW:** qrcode (QR generation)
- **NEW:** pyserial (Arduino communication)

### **Frontend**
- **NEW:** Streamlit (dashboard)
- **NEW:** Plotly/Dash (visualizations)
- **NEW:** Leaflet/Folium (heatmaps)

### **Hardware**
- Arduino IDE
- Fritzing (circuit design)
- RFID libraries

### **Database**
- SQLite (existing) or upgrade to PostgreSQL for production

---

## 📝 Notes for Implementation

1. **Modular Design**: Each component should be independent and testable
2. **Backward Compatibility**: Don't break existing features
3. **Configuration**: All thresholds/parameters should be configurable via config.py
4. **Logging**: Comprehensive logging for debugging and auditing
5. **Testing**: Unit tests for each new module
6. **Documentation**: Update README.md and API docs as features are added

---

## 🚀 Quick Start for Developers

```bash
# Install new dependencies
pip install streamlit plotly qrcode pyserial scikit-learn

# Run Streamlit dashboard
streamlit run backend/app/dashboard/streamlit_app.py

# Test Arduino connection
python backend/app/hardware/arduino_test.py

# Generate QR codes
python backend/app/violations/qr_generator.py

# Run ML training
python backend/app/ml/train_risk_predictor.py
```

---

**This plan integrates all four team member proposals into a cohesive implementation roadmap. Prioritize features based on demo requirements and available time.**
