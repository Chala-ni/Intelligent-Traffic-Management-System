# Intelligent Traffic Management System - Frontend Implementation Plan
## Unified Flutter Application (Web + Mobile)

**Project ID:** 25-26J-330  
**Created:** December 23, 2025  
**Status:** 🚀 Ready for Implementation

---

## 📋 Project Overview

Build a **Unified Flutter Application** that serves two purposes based on platform/login:
- **Web (Admin/Police):** High-tech "Traffic Control Center" dashboard
- **Mobile (Driver/Public):** Personal app for drivers and community alerts

---

## 🎨 Design System

### **Theme: Dark Mode Professional Dashboard**

```dart
// Color Palette
class AppColors {
  // Backgrounds
  static const background = Color(0xFF121212);      // Very Dark Grey
  static const surface = Color(0xFF1E1E1E);         // Dark Grey (Cards)
  static const surfaceVariant = Color(0xFF2D2D2D);  // Elevated Surface
  
  // Primary Accent
  static const primary = Color(0xFFFFD700);         // Traffic Yellow
  static const primaryDark = Color(0xFFB8860B);     // Dark Gold
  
  // Status Colors
  static const success = Color(0xFF00C853);         // Green
  static const error = Color(0xFFFF4444);           // Red
  static const warning = Color(0xFFFF9800);         // Orange
  static const info = Color(0xFF2196F3);            // Blue
  
  // Text Colors
  static const textPrimary = Color(0xFFFFFFFF);     // White
  static const textSecondary = Color(0xFFB0B0B0);   // Grey
  static const textDisabled = Color(0xFF666666);   // Dark Grey
  
  // Traffic Light Colors
  static const trafficRed = Color(0xFFFF0000);
  static const trafficYellow = Color(0xFFFFD700);
  static const trafficGreen = Color(0xFF00FF00);
  
  // Risk Level Colors
  static const riskLow = Color(0xFF00C853);
  static const riskMedium = Color(0xFFFF9800);
  static const riskHigh = Color(0xFFFF5722);
  static const riskCritical = Color(0xFFFF0000);
}
```

### **Typography**

```dart
// Google Fonts
// Headings: Poppins (Bold, SemiBold)
// Data/Body: Inter (Regular, Medium)

class AppTypography {
  // Headings (Poppins)
  static const h1 = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 32,
    fontWeight: FontWeight.bold,
    color: AppColors.textPrimary,
  );
  
  static const h2 = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 24,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
  );
  
  static const h3 = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
  );
  
  // Data/Body (Inter)
  static const bodyLarge = TextStyle(
    fontFamily: 'Inter',
    fontSize: 16,
    fontWeight: FontWeight.normal,
    color: AppColors.textPrimary,
  );
  
  static const bodyMedium = TextStyle(
    fontFamily: 'Inter',
    fontSize: 14,
    fontWeight: FontWeight.normal,
    color: AppColors.textSecondary,
  );
  
  static const dataLabel = TextStyle(
    fontFamily: 'Inter',
    fontSize: 12,
    fontWeight: FontWeight.w500,
    color: AppColors.textSecondary,
    letterSpacing: 1.2,
  );
  
  static const dataValue = TextStyle(
    fontFamily: 'Inter',
    fontSize: 28,
    fontWeight: FontWeight.bold,
    color: AppColors.primary,
  );
}
```

### **Component Styling**

```dart
// Buttons
- Primary: Yellow (#FFD700) with dark text
- Secondary: Outlined with yellow border
- Danger: Red (#FF4444)
- Icon Buttons: Circular with subtle glow

// Cards
- Background: #1E1E1E
- Border Radius: 16px
- Box Shadow: subtle glow on hover
- Padding: 24px

// Input Fields
- Background: #2D2D2D
- Border: 1px solid #3D3D3D
- Focus Border: #FFD700
- Border Radius: 12px

// Data Tables
- Header: #2D2D2D
- Rows: Alternating #1E1E1E / #252525
- Hover: Subtle yellow glow
```

---

## 🏗️ Architecture

### **Tech Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Flutter 3.16+ | Cross-platform UI |
| State Management | Provider | Reactive state |
| Networking | http + dio | API calls |
| Local Storage | shared_preferences | JWT tokens |
| Video | flutter_mjpeg | Live MJPEG stream |
| Charts | fl_chart | Analytics graphs |
| Maps | google_maps_flutter | Junction map |
| Fonts | google_fonts | Poppins + Inter |

### **Project Structure**

```
flutter_app/
├── lib/
│   ├── main.dart                           # Entry point
│   │
│   ├── core/
│   │   ├── config/
│   │   │   ├── app_config.dart             # API URLs, constants
│   │   │   └── routes.dart                 # Named routes
│   │   │
│   │   ├── theme/
│   │   │   ├── app_colors.dart             # Color palette
│   │   │   ├── app_typography.dart         # Text styles
│   │   │   └── app_theme.dart              # ThemeData
│   │   │
│   │   ├── network/
│   │   │   ├── api_client.dart             # HTTP client with JWT
│   │   │   ├── api_endpoints.dart          # Endpoint constants
│   │   │   └── api_response.dart           # Response models
│   │   │
│   │   └── utils/
│   │       ├── validators.dart             # Form validation
│   │       ├── formatters.dart             # Date/currency formatting
│   │       └── responsive.dart             # Screen size helpers
│   │
│   ├── models/
│   │   ├── user.dart                       # Admin/Driver user
│   │   ├── violation.dart                  # Violation model
│   │   ├── fine.dart                       # Fine with breakdown
│   │   ├── junction_safety.dart            # LiveSafeScore
│   │   ├── risk_score.dart                 # Vehicle risk
│   │   ├── community_alert.dart            # Public alerts
│   │   ├── signal_state.dart               # Traffic signal
│   │   └── dashboard_stats.dart            # Admin stats
│   │
│   ├── providers/
│   │   ├── auth_provider.dart              # Authentication state
│   │   ├── admin/
│   │   │   ├── dashboard_provider.dart     # Dashboard stats
│   │   │   ├── violations_provider.dart    # Violation list
│   │   │   ├── signal_provider.dart        # Traffic signals
│   │   │   └── analytics_provider.dart     # Charts data
│   │   │
│   │   └── driver/
│   │       ├── profile_provider.dart       # Driver profile
│   │       ├── my_violations_provider.dart # Personal violations
│   │       ├── safety_provider.dart        # Junction scores
│   │       └── alerts_provider.dart        # Notifications
│   │
│   ├── screens/
│   │   ├── splash_screen.dart              # Animated splash
│   │   ├── platform_router.dart            # Web vs Mobile routing
│   │   │
│   │   ├── auth/
│   │   │   ├── admin_login_screen.dart     # Professional admin login
│   │   │   ├── driver_login_screen.dart    # Phone + plate login
│   │   │   └── driver_register_screen.dart # Driver registration
│   │   │
│   │   ├── admin/                          # WEB DASHBOARD
│   │   │   ├── admin_shell.dart            # Sidebar + content layout
│   │   │   ├── dashboard/
│   │   │   │   └── admin_dashboard_screen.dart
│   │   │   ├── live_feed/
│   │   │   │   └── live_video_screen.dart
│   │   │   ├── violations/
│   │   │   │   ├── violations_list_screen.dart
│   │   │   │   └── violation_detail_screen.dart
│   │   │   ├── drivers/
│   │   │   │   ├── drivers_list_screen.dart
│   │   │   │   └── driver_detail_screen.dart
│   │   │   ├── signals/
│   │   │   │   └── traffic_signals_screen.dart
│   │   │   ├── analytics/
│   │   │   │   └── analytics_screen.dart
│   │   │   └── settings/
│   │   │       └── admin_settings_screen.dart
│   │   │
│   │   └── driver/                         # MOBILE APP
│   │       ├── driver_shell.dart           # Bottom nav layout
│   │       ├── home/
│   │       │   └── driver_home_screen.dart
│   │       ├── safety/
│   │       │   ├── junction_score_screen.dart
│   │       │   └── junction_map_screen.dart
│   │       ├── violations/
│   │       │   ├── my_violations_screen.dart
│   │       │   └── violation_detail_screen.dart
│   │       ├── fines/
│   │       │   └── my_fines_screen.dart
│   │       ├── alerts/
│   │       │   └── alerts_screen.dart
│   │       └── profile/
│   │           └── driver_profile_screen.dart
│   │
│   └── widgets/
│       ├── common/
│       │   ├── app_button.dart             # Styled buttons
│       │   ├── app_card.dart               # Dark card container
│       │   ├── app_text_field.dart         # Styled input
│       │   ├── loading_overlay.dart        # Loading state
│       │   └── error_widget.dart           # Error display
│       │
│       ├── admin/
│       │   ├── sidebar_menu.dart           # Navigation sidebar
│       │   ├── stat_card.dart              # Dashboard stat box
│       │   ├── traffic_light_widget.dart   # 4-way junction display
│       │   ├── violation_table.dart        # Data table
│       │   ├── risk_badge.dart             # Risk level indicator
│       │   └── video_player_card.dart      # MJPEG player
│       │
│       └── driver/
│           ├── safety_score_gauge.dart     # Circular gauge
│           ├── violation_card.dart         # Violation list item
│           ├── fine_card.dart              # Fine with breakdown
│           ├── alert_tile.dart             # Notification item
│           └── junction_marker.dart        # Map marker
│
├── assets/
│   ├── images/
│   │   ├── logo.png                        # App logo
│   │   ├── admin_bg.png                    # Login background
│   │   └── icons/                          # Custom icons
│   │
│   └── animations/
│       ├── loading.json                    # Lottie loading
│       └── success.json                    # Lottie success
│
├── web/
│   └── index.html                          # Web configuration
│
├── android/
│   └── ...                                 # Android config
│
├── ios/
│   └── ...                                 # iOS config
│
└── pubspec.yaml                            # Dependencies
```

---

## 📱 Screen Designs

### **1. Admin Login Screen (Professional)**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │
│     ░░                                                        ░░     │
│     ░░     🚦  TRAFFIC CONTROL CENTER                        ░░     │
│     ░░         Intelligent Management System                  ░░     │
│     ░░                                                        ░░     │
│     ░░    ┌────────────────────────────────────────────┐     ░░     │
│     ░░    │  ┌──────────────────────────────────────┐  │     ░░     │
│     ░░    │  │ 👤  Admin Username                   │  │     ░░     │
│     ░░    │  └──────────────────────────────────────┘  │     ░░     │
│     ░░    │                                            │     ░░     │
│     ░░    │  ┌──────────────────────────────────────┐  │     ░░     │
│     ░░    │  │ 🔒  Password                     👁️  │  │     ░░     │
│     ░░    │  └──────────────────────────────────────┘  │     ░░     │
│     ░░    │                                            │     ░░     │
│     ░░    │  ┌──────────────────────────────────────┐  │     ░░     │
│     ░░    │  │          🔐 ACCESS SYSTEM            │  │     ░░     │
│     ░░    │  └──────────────────────────────────────┘  │     ░░     │
│     ░░    │                                            │     ░░     │
│     ░░    │        Authorized Personnel Only           │     ░░     │
│     ░░    └────────────────────────────────────────────┘     ░░     │
│     ░░                                                        ░░     │
│     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │
│                                                                      │
│     © 2025 Intelligent Traffic Management System                    │
└─────────────────────────────────────────────────────────────────────┘

Design Notes:
- Full-screen dark gradient background with subtle animated particles
- Glowing yellow border on focus
- Animated traffic light icon in logo
- Subtle pulsing effect on login button
- Frosted glass card effect
```

### **2. Admin Dashboard (Control Center)**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🚦 TRAFFIC CONTROL CENTER                              👤 Admin ▼  🔔 5     │
├──────────┬───────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│ 📊 Dash  │   SYSTEM OVERVIEW                               🟢 ONLINE        │
│          │  ─────────────────────────────────────────────────────────────   │
│ 📹 Live  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│          │  │ VIOLATIONS │ │  VEHICLES  │ │ AVG RISK   │ │ LIVE SCORE │     │
│ ⚠️ Viols │  │    📈 24   │ │   🚗 156   │ │  ⚡ 42.5   │ │   🛡️ 78    │     │
│          │  │   Today    │ │   Active   │ │   Score    │ │  Junction  │     │
│ 👥 Drvrs │  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│          │                                                                   │
│ 🚦 Sigs  │  ┌────────────────────────────┐ ┌────────────────────────────┐   │
│          │  │      LIVE VIDEO FEED       │ │     4-WAY JUNCTION         │   │
│ 📈 Stats │  │                            │ │                            │   │
│          │  │   ┌────────────────────┐   │ │          NORTH             │   │
│ ⚙️ Sett  │  │   │                    │   │ │         🔴 (15)            │   │
│          │  │   │   MJPEG STREAM     │   │ │            │               │   │
│          │  │   │   WITH OVERLAYS    │   │ │   WEST ────┼──── EAST      │   │
│          │  │   │                    │   │ │   🔴(8)    │    🟢(12)     │   │
│          │  │   │                    │   │ │            │               │   │
│          │  │   └────────────────────┘   │ │         SOUTH              │   │
│          │  │                            │ │         🔴 (6)             │   │
│          │  │  ▶️ Playing | 30 FPS       │ │   Green: EAST | 25s        │   │
│          │  └────────────────────────────┘ └────────────────────────────┘   │
│          │                                                                   │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │  RECENT VIOLATIONS                                    ➕   │  │
│          │  ├──────────┬───────────┬────────────┬──────────┬───────────┤  │
│          │  │ PLATE    │ TYPE      │ TIME       │ FINE     │ STATUS    │  │
│          │  ├──────────┼───────────┼────────────┼──────────┼───────────┤  │
│          │  │ CAB-1234 │ Parking   │ 10:45 AM   │ LKR 1500 │ 🔴 Unpaid │  │
│          │  │ WP-5678  │ Speeding  │ 10:32 AM   │ LKR 2000 │ 🟡 Pending│  │
│          │  │ SP-9012  │ Lane Weav │ 10:28 AM   │ LKR 800  │ 🟢 Paid   │  │
│          │  └──────────┴───────────┴────────────┴──────────┴───────────┘  │
│          │                                                                   │
│──────────│  ┌──────────────────────┐                                        │
│ 🚨 EMERG │  │  🚑 SIMULATE AMBULANCE │  ← Emergency Override Button         │
│──────────│  └──────────────────────┘                                        │
│          │                                                                   │
└──────────┴───────────────────────────────────────────────────────────────────┘

Design Notes:
- Collapsible sidebar with icons + labels
- Stat cards with subtle glow and animated counters
- Live video with overlay controls
- 4-way junction with animated lights
- Data table with row hover effects
- Emergency button with pulsing red glow
```

### **3. Driver Mobile App - Home Screen**

```
┌─────────────────────────────────┐
│  9:41                    📶 🔋  │
├─────────────────────────────────┤
│                                 │
│   Good Morning, Dinesh! 👋      │
│   CAB-1234                      │
│                                 │
│   ┌─────────────────────────┐   │
│   │    YOUR SAFE SCORE      │   │
│   │                         │   │
│   │      ╭───────────╮      │   │
│   │     ╱  ██████    ╲     │   │
│   │    │   ██████     │     │   │
│   │    │     85       │     │   │
│   │     ╲  ██████    ╱     │   │
│   │      ╰───────────╯      │   │
│   │                         │   │
│   │      🟢 EXCELLENT       │   │
│   │    ↑ +5 this week       │   │
│   └─────────────────────────┘   │
│                                 │
│   JUNCTION SAFETY               │
│   ┌─────────────────────────┐   │
│   │  Main Junction    🟢 78 │   │
│   │  Good conditions        │   │
│   │  📍 500m away           │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌──────────┐  ┌──────────┐   │
│   │⚠️ 2      │  │💰 1       │   │
│   │Violations│  │Unpaid    │   │
│   │This Month│  │Fine      │   │
│   └──────────┘  └──────────┘   │
│                                 │
│   COMMUNITY ALERTS              │
│   ┌─────────────────────────┐   │
│   │ ⚠️ High traffic at Main │   │
│   │    Junction - 15 min ago│   │
│   └─────────────────────────┘   │
│                                 │
├─────────────────────────────────┤
│  🏠    🗺️    ⚠️    💰    👤   │
│ Home  Map  Alerts Fines Profile │
└─────────────────────────────────┘

Design Notes:
- Large circular gauge with animated fill
- Color-coded score (Green/Yellow/Red)
- Glowing card effects
- Quick stat boxes
- Bottom navigation with icons
```

---

## 🗓️ Sprint Plan

### **Sprint 0: Project Setup (1 Day)**
**Goal:** Initialize Flutter project with architecture

| Task | Priority | Estimate |
|------|----------|----------|
| Create Flutter project with folder structure | 🔴 High | 1h |
| Add dependencies to pubspec.yaml | 🔴 High | 30m |
| Implement AppColors, AppTypography, AppTheme | 🔴 High | 2h |
| Create API client with JWT handling | 🔴 High | 2h |
| Set up Provider architecture | 🔴 High | 1h |
| Create base widgets (AppButton, AppCard, AppTextField) | 🟡 Med | 2h |

**Deliverable:** Runnable Flutter app with theme applied

---

### **Sprint 1: Authentication (2 Days)**
**Goal:** Complete login/logout for Admin and Driver

| Task | Priority | Estimate |
|------|----------|----------|
| AuthProvider with JWT storage | 🔴 High | 2h |
| **Admin Login Screen** (professional design) | 🔴 High | 4h |
| - Animated background | 🟡 Med | 1h |
| - Glowing form fields | 🟡 Med | 1h |
| - Login API integration | 🔴 High | 1h |
| **Driver Login Screen** | 🔴 High | 3h |
| - Phone + Plate input | 🔴 High | 1h |
| - Login API integration | 🔴 High | 1h |
| **Driver Register Screen** | 🟡 Med | 2h |
| Platform Router (Web → Admin, Mobile → Driver) | 🔴 High | 2h |
| Splash Screen with animation | 🟡 Med | 1h |

**Deliverable:** Working auth flow for both user types

---

### **Sprint 2: Admin Shell & Dashboard (3 Days)**
**Goal:** Admin sidebar navigation + main dashboard

| Task | Priority | Estimate |
|------|----------|----------|
| **Admin Shell** (sidebar + content area) | 🔴 High | 3h |
| - Collapsible sidebar | 🔴 High | 2h |
| - Navigation highlighting | 🟡 Med | 1h |
| **Dashboard Provider** (stats API) | 🔴 High | 2h |
| **Admin Dashboard Screen** | 🔴 High | 6h |
| - Stat Cards (animated counters) | 🔴 High | 2h |
| - Live Video Player (MJPEG) | 🔴 High | 3h |
| - 4-Way Junction Widget | 🔴 High | 4h |
| - Recent Violations Table | 🟡 Med | 2h |
| Emergency Button (Simulate Ambulance) | 🔴 High | 2h |

**Deliverable:** Functional admin dashboard with live data

---

### **Sprint 3: Admin Violations & Drivers (2 Days)**
**Goal:** Violation management and driver lookup

| Task | Priority | Estimate |
|------|----------|----------|
| **Violations List Screen** | 🔴 High | 4h |
| - Data table with sorting | 🔴 High | 2h |
| - Filters (type, date, status) | 🟡 Med | 2h |
| - Search by plate | 🟡 Med | 1h |
| **Violation Detail Screen** | 🔴 High | 3h |
| - Evidence images | 🔴 High | 1h |
| - Fine breakdown card | 🔴 High | 1h |
| - OCR result display | 🟡 Med | 1h |
| **Drivers List Screen** | 🟡 Med | 3h |
| **Driver Detail Screen** (violation history) | 🟡 Med | 2h |

**Deliverable:** Complete violation management system

---

### **Sprint 4: Admin Signals & Analytics (2 Days)**
**Goal:** Traffic signal control and analytics charts

| Task | Priority | Estimate |
|------|----------|----------|
| **Traffic Signals Screen** | 🔴 High | 4h |
| - Large 4-way junction display | 🔴 High | 2h |
| - Real-time signal states | 🔴 High | 1h |
| - Emergency override controls | 🔴 High | 1h |
| **Analytics Screen** | 🟡 Med | 5h |
| - Violation trends chart (line) | 🟡 Med | 2h |
| - Violation types chart (pie) | 🟡 Med | 1h |
| - Risk score distribution | 🟡 Med | 1h |
| - Peak hours heatmap | 🟢 Low | 1h |

**Deliverable:** Signal control center + analytics

---

### **Sprint 5: Driver App Shell & Home (2 Days)**
**Goal:** Driver mobile app navigation + home screen

| Task | Priority | Estimate |
|------|----------|----------|
| **Driver Shell** (bottom navigation) | 🔴 High | 2h |
| **Driver Profile Provider** | 🔴 High | 1h |
| **Safety Score Gauge Widget** | 🔴 High | 3h |
| - Circular progress animation | 🔴 High | 2h |
| - Color gradient based on score | 🟡 Med | 1h |
| **Driver Home Screen** | 🔴 High | 4h |
| - Safety score display | 🔴 High | 1h |
| - Quick stats cards | 🟡 Med | 1h |
| - Nearby junction preview | 🟡 Med | 1h |
| - Community alerts preview | 🟡 Med | 1h |

**Deliverable:** Driver home screen with live data

---

### **Sprint 6: Driver Violations & Fines (2 Days)**
**Goal:** Personal violation history and fine details

| Task | Priority | Estimate |
|------|----------|----------|
| **My Violations Screen** | 🔴 High | 3h |
| - Violation cards list | 🔴 High | 2h |
| - Filter by date/type | 🟡 Med | 1h |
| **Violation Detail Screen** (driver view) | 🟡 Med | 2h |
| **My Fines Screen** | 🔴 High | 3h |
| - Unpaid fines list | 🔴 High | 1h |
| - Fine breakdown view | 🔴 High | 1h |
| - Payment history | 🟡 Med | 1h |
| **Score History Screen** | 🟡 Med | 2h |

**Deliverable:** Personal violation/fine tracking

---

### **Sprint 7: Driver Safety & Alerts (2 Days)**
**Goal:** Junction safety and community features

| Task | Priority | Estimate |
|------|----------|----------|
| **Junction Score Screen** | 🔴 High | 3h |
| - Large gauge display | 🔴 High | 1h |
| - Safety tips | 🟡 Med | 1h |
| - Recent alerts | 🟡 Med | 1h |
| **Junction Map Screen** | 🟡 Med | 4h |
| - Google Maps integration | 🟡 Med | 2h |
| - Junction markers with scores | 🟡 Med | 1h |
| - Tap for details | 🟡 Med | 1h |
| **Alerts Screen** | 🔴 High | 2h |
| - Notification list | 🔴 High | 1h |
| - Mark as read | 🟡 Med | 30m |
| - Community alerts | 🟡 Med | 30m |

**Deliverable:** Safety awareness features

---

### **Sprint 8: Polish & Responsive (2 Days)**
**Goal:** UI refinement and responsive testing

| Task | Priority | Estimate |
|------|----------|----------|
| Responsive testing (phone/tablet/desktop) | 🔴 High | 3h |
| LayoutBuilder refinements | 🔴 High | 2h |
| Animation polish | 🟡 Med | 2h |
| Loading states for all screens | 🟡 Med | 2h |
| Error handling improvements | 🟡 Med | 2h |
| Accessibility improvements | 🟢 Low | 1h |
| Performance optimization | 🟡 Med | 2h |

**Deliverable:** Production-ready app

---

### **Sprint 9: Testing & Deployment (2 Days)**
**Goal:** Final testing and build

| Task | Priority | Estimate |
|------|----------|----------|
| Integration testing | 🔴 High | 3h |
| Web build and hosting | 🔴 High | 2h |
| Android APK build | 🔴 High | 2h |
| iOS build (if Mac available) | 🟡 Med | 2h |
| Demo video recording | 🟡 Med | 2h |
| Documentation | 🟡 Med | 2h |

**Deliverable:** Deployed applications

---

## 📦 Dependencies (pubspec.yaml)

```yaml
name: traffic_control_app
description: Intelligent Traffic Management System - Flutter App

publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # State Management
  provider: ^6.1.1
  
  # Networking
  http: ^1.1.0
  dio: ^5.4.0
  
  # Local Storage
  shared_preferences: ^2.2.2
  
  # Video
  flutter_mjpeg: ^3.0.0
  
  # Charts
  fl_chart: ^0.66.0
  
  # Maps
  google_maps_flutter: ^2.5.3
  
  # UI Components
  google_fonts: ^6.1.0
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  
  # Animations
  lottie: ^3.0.0
  animated_text_kit: ^4.2.2
  
  # Utilities
  intl: ^0.18.1
  url_launcher: ^6.2.2
  
  # Icons
  font_awesome_flutter: ^10.6.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/animations/
  
  fonts:
    - family: Poppins
      fonts:
        - asset: assets/fonts/Poppins-Regular.ttf
        - asset: assets/fonts/Poppins-Medium.ttf
          weight: 500
        - asset: assets/fonts/Poppins-SemiBold.ttf
          weight: 600
        - asset: assets/fonts/Poppins-Bold.ttf
          weight: 700
    - family: Inter
      fonts:
        - asset: assets/fonts/Inter-Regular.ttf
        - asset: assets/fonts/Inter-Medium.ttf
          weight: 500
        - asset: assets/fonts/Inter-Bold.ttf
          weight: 700
```

---

## 🔗 API Integration Map

### **Auth Endpoints**
| Flutter Screen | API Endpoint | Method |
|----------------|--------------|--------|
| Admin Login | `/auth/admin/login` | POST |
| Driver Login | `/auth/driver/login` | POST |
| Driver Register | `/auth/driver/register` | POST |

### **Admin Endpoints**
| Flutter Screen | API Endpoint | Method |
|----------------|--------------|--------|
| Dashboard Stats | `/admin/dashboard/stats` | GET |
| Violations List | `/admin/violations` | GET |
| Violation Detail | `/admin/violations/{id}` | GET |
| Drivers List | `/admin/drivers` | GET |
| Driver Detail | `/admin/drivers/{id}` | GET |
| Signal Status | `/signal/four-way-status` | GET |
| Emergency Trigger | `/admin/emergency/trigger` | POST |
| Analytics Trends | `/admin/analytics/violation-trends` | GET |
| Video Stream | `/video/detect-stream` | GET (MJPEG) |

### **Driver Endpoints**
| Flutter Screen | API Endpoint | Method |
|----------------|--------------|--------|
| Profile | `/driver/me` | GET |
| My Violations | `/driver/my-violations` | GET |
| My Fines | `/driver/my-fines` | GET |
| Notifications | `/driver/notifications` | GET |
| Score History | `/driver/score-history` | GET |

### **Public Endpoints**
| Flutter Screen | API Endpoint | Method |
|----------------|--------------|--------|
| Junction Score | `/community/junction-score` | GET |
| Community Alerts | `/community/alerts` | GET |
| Safety Tips | `/community/safety-tips` | GET |

---

## ✅ Success Criteria

| Feature | Metric |
|---------|--------|
| Admin Login | < 2s response, JWT stored |
| Dashboard Load | < 3s with all stats |
| Video Stream | 30 FPS, < 1s latency |
| Signal Updates | Real-time (< 500ms) |
| Driver App Load | < 2s first paint |
| Score Animation | Smooth 60 FPS |
| Responsive Design | Works on all screen sizes |

---

## 🚀 Quick Start Commands

```bash
# Create Flutter project
flutter create traffic_control_app
cd traffic_control_app

# Add dependencies
flutter pub get

# Run on Chrome (Admin Dashboard)
flutter run -d chrome

# Run on Android (Driver App)
flutter run -d android

# Build Web
flutter build web

# Build APK
flutter build apk --release
```

---

**This plan serves as the single source of truth for Flutter frontend implementation. Follow the sprint schedule and check off tasks as completed.**
