"""
Admin API Router - Protected endpoints for admin dashboard
Requires JWT authentication with admin role.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from google.cloud.firestore_v1 import FieldFilter

from app.config import get_settings
from app.db.firestore_client import get_db, Collections
from app.routers.auth import get_current_admin, UserInfo
from app.fuzzy.traffic_controller import get_four_way_controller

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# =============================================================================
# VIDEO SNAPSHOT FOR ZONE EDITOR
# =============================================================================

@router.get("/video/snapshot", summary="Get video snapshot for zone editor")
async def get_admin_video_snapshot(user: UserInfo = Depends(get_current_admin)):
    """
    Get a CLEAN snapshot from the video feed for the Zone Editor.
    This returns a frame WITHOUT detection boxes or zone overlays.
    Lazy-starts the video worker if not already running.
    """
    # Import here to avoid circular imports
    from app.routers.video import _video_state, start_video_worker
    
    # Lazy start: Start worker if not running
    if not _video_state.running:
        start_video_worker()
        # Wait up to 15 seconds for first frame (YOLO models take time to load)
        for _ in range(150):  # Max 15 seconds (model loading can take 5-10s)
            await asyncio.sleep(0.1)
            if _video_state.get_snapshot() is not None:
                break
    
    snapshot = _video_state.get_snapshot()
    
    if snapshot is None:
        raise HTTPException(status_code=503, detail="No snapshot available yet. Video stream starting...")
    
    return Response(
        content=snapshot,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        }
    )


@router.post("/video/snapshot/refresh", summary="Refresh zone editor snapshot")
async def refresh_admin_video_snapshot(user: UserInfo = Depends(get_current_admin)):
    """
    Request a fresh clean snapshot for Zone Editor.
    Captures the next video frame as a clean image without any overlays.
    """
    from app.routers.video import _video_state
    
    _video_state.request_new_snapshot()
    
    # Wait for new snapshot (max 2 seconds)
    for _ in range(20):
        await asyncio.sleep(0.1)
        if _video_state.raw_frame_captured:
            break
    
    return {"status": "refreshed", "message": "New clean snapshot captured"}


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class DashboardStats(BaseModel):
    violations_today: int
    violations_this_week: int
    average_risk_score: float
    current_traffic_level: str
    active_junctions: int
    total_vehicles_today: int
    pending_fines: float
    emergency_mode: bool


class ViolationDetail(BaseModel):
    violation_id: str
    driver_id: str
    license_plate: Optional[str]
    violation_type: str
    timestamp: str
    location: Optional[str]
    fine_amount: float
    points_deducted: int
    evidence_path: Optional[str]
    notes: Optional[str]


class DriverSummary(BaseModel):
    driver_id: str
    current_score: int
    total_violations: int
    total_fines: float
    last_violation: Optional[str]


class EmergencyResponse(BaseModel):
    status: str
    message: str
    affected_junctions: List[str]
    timestamp: str


# =============================================================================
# DASHBOARD STATISTICS
# =============================================================================

@router.get("/dashboard/stats", response_model=DashboardStats, summary="Get dashboard statistics")
async def get_dashboard_stats(user: UserInfo = Depends(get_current_admin)):
    """
    Get comprehensive dashboard statistics including:
    - Violations count (today and week)
    - Average risk score across all drivers
    - Traffic level estimation
    - Active junction count
    """
    db = get_db()

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Violations today
    violations_today = 0
    q = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("timestamp", ">=", today)
    )
    async for _ in q.stream():
        violations_today += 1

    # Violations this week
    violations_week = 0
    q = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("timestamp", ">=", week_ago)
    )
    async for _ in q.stream():
        violations_week += 1

    # Average risk score from drivers
    scores = []
    async for doc in db.collection(Collections.DRIVERS).stream():
        d = doc.to_dict()
        scores.append(d.get("current_score", 100))
    avg_score = sum(scores) / len(scores) if scores else 100.0

    # Get junction safety score
    traffic_level = "normal"
    q = db.collection(Collections.JUNCTION_SAFETY).order_by(
        "updated_at", direction="DESCENDING"
    ).limit(1)
    async for doc in q.stream():
        js = doc.to_dict()
        current_risk = 100 - js.get("safety_score", 50)
        if current_risk > 70:
            traffic_level = "high"
        elif current_risk > 40:
            traffic_level = "moderate"
        else:
            traffic_level = "low"

    # Pending fines
    pending_fines = 0.0
    async for doc in db.collection(Collections.VIOLATIONS).stream():
        v = doc.to_dict()
        fa = v.get("fine_amount", 0)
        if fa and fa > 0:
            pending_fines += fa

    # Check emergency mode
    emergency_mode = False
    eq = db.collection(Collections.EMERGENCY_STATUS).order_by(
        "triggered_at", direction="DESCENDING"
    ).limit(1)
    async for doc in eq.stream():
        emergency_mode = bool(doc.to_dict().get("active", False))

    return DashboardStats(
        violations_today=violations_today,
        violations_this_week=violations_week,
        average_risk_score=round(100 - avg_score, 2),
        current_traffic_level=traffic_level,
        active_junctions=1,
        total_vehicles_today=violations_today * 10,
        pending_fines=pending_fines,
        emergency_mode=emergency_mode,
    )


# =============================================================================
# VIOLATION MANAGEMENT
# =============================================================================

@router.get("/violations", summary="Get all violations")
async def get_all_violations(
    user: UserInfo = Depends(get_current_admin),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    violation_type: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
):
    """
    Get paginated list of all violations with optional filters.
    Admin only endpoint.
    """
    db = get_db()

    # Build query with filters
    q = db.collection(Collections.VIOLATIONS)
    if violation_type:
        q = q.where(filter=FieldFilter("violation_type", "==", violation_type))
    if date_from:
        q = q.where(filter=FieldFilter("timestamp", ">=", date_from))
    if date_to:
        q = q.where(filter=FieldFilter("timestamp", "<=", date_to + " 23:59:59"))

    q = q.order_by("timestamp", direction="DESCENDING")

    # Collect all matching docs for total count + pagination
    all_docs = []
    async for doc in q.stream():
        all_docs.append((doc.id, doc.to_dict()))

    total = len(all_docs)
    page = all_docs[offset: offset + limit]

    return {
        "violations": [
            {
                "violation_id": doc_id,
                "driver_id": v.get("driver_id", ""),
                "license_plate": v.get("license_plate", v.get("driver_id", "")),
                "violation_type": v.get("violation_type", ""),
                "timestamp": v.get("timestamp", ""),
                "location": v.get("location") or "Unknown",
                "fine_amount": v.get("fine_amount", 0) or 0,
                "points_deducted": v.get("points_deducted", 0),
                "evidence_path": v.get("evidence_path") or v.get("snapshot_path"),
                "notes": f"Severity: {v['severity']}" if v.get("severity") else None,
                "status": v.get("status") or "pending",
            }
            for doc_id, v in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters_applied": {
            "violation_type": violation_type,
            "date_from": date_from,
            "date_to": date_to,
        }
    }


@router.get("/violations/{violation_id}", summary="Get violation details")
async def get_violation_details(
    violation_id: str,
    user: UserInfo = Depends(get_current_admin),
):  
    """Get detailed information about a specific violation."""
    db = get_db()
    doc = await db.collection(Collections.VIOLATIONS).document(violation_id).get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Violation not found")

    v = doc.to_dict()
    return {
        "violation_id": doc.id,
        "driver_id": v.get("driver_id", ""),
        "license_plate": v.get("license_plate", v.get("driver_id", "")),
        "violation_type": v.get("violation_type", ""),
        "timestamp": v.get("timestamp", ""),
        "location": v.get("location") or "Unknown",
        "fine_amount": v.get("fine_amount", 0) or 0,
        "severity": v.get("severity"),
        "status": v.get("status") or "pending",
        "evidence_path": v.get("evidence_path") or v.get("snapshot_path"),
    }


@router.delete("/violations/{violation_id}", summary="Delete a violation")
async def delete_violation(
    violation_id: str,
    user: UserInfo = Depends(get_current_admin),
):
    """Delete a violation record (admin only)."""
    db = get_db()
    doc = await db.collection(Collections.VIOLATIONS).document(violation_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Violation not found")

    await db.collection(Collections.VIOLATIONS).document(violation_id).delete()
    return {"status": "deleted", "violation_id": violation_id}


# =============================================================================
# DRIVER MANAGEMENT
# =============================================================================

@router.get("/drivers", summary="Get all drivers")
async def get_all_drivers(
    user: UserInfo = Depends(get_current_admin),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="current_score", description="Sort by: current_score, total_violations, total_fines"),
    order: str = Query(default="asc", description="Order: asc, desc"),
):
    """Get paginated list of all drivers with their scores."""
    db = get_db()

    valid_sorts = ["current_score", "total_violations", "total_fines", "driver_id"]
    if sort_by not in valid_sorts:
        sort_by = "current_score"

    direction = "DESCENDING" if order.lower() == "desc" else "ASCENDING"

    # Get all drivers sorted
    all_drivers = []
    q = db.collection(Collections.DRIVERS).order_by(sort_by, direction=direction)
    async for doc in q.stream():
        d = doc.to_dict()
        d["_driver_id"] = doc.id
        all_drivers.append(d)

    total = len(all_drivers)
    page = all_drivers[offset: offset + limit]

    # Lookup driver_users for name/phone
    result = []
    for d in page:
        driver_id = d.get("driver_id", d["_driver_id"])
        # Find matching driver_user by plate_number
        name = "Unknown Driver"
        phone = None
        uq = db.collection(Collections.DRIVER_USERS).where(
            filter=FieldFilter("plate_number", "==", driver_id)
        ).limit(1)
        async for udoc in uq.stream():
            u = udoc.to_dict()
            name = u.get("name") or "Unknown Driver"
            phone = u.get("phone")

        result.append({
            "driver_id": driver_id,
            "name": name,
            "phone": phone,
            "current_score": d.get("current_score", 100),
            "total_violations": d.get("total_violations", 0),
            "total_fines": d.get("total_fines", 0.0),
            "last_violation": d.get("updated_at"),
            "risk_level": get_risk_level(d.get("current_score", 100)),
        })

    return {
        "drivers": result,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/drivers/{driver_id}", summary="Get driver details")
async def get_driver_details(
    driver_id: str,
    user: UserInfo = Depends(get_current_admin),
):
    """Get detailed information about a specific driver."""
    db = get_db()

    doc = await db.collection(Collections.DRIVERS).document(driver_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver = doc.to_dict()

    # Get user details
    name = "Unknown Driver"
    phone = None
    uq = db.collection(Collections.DRIVER_USERS).where(
        filter=FieldFilter("plate_number", "==", driver_id)
    ).limit(1)
    async for udoc in uq.stream():
        u = udoc.to_dict()
        name = u.get("name") or "Unknown Driver"
        phone = u.get("phone")

    # Get recent violations
    vq = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("driver_id", "==", driver_id)
    ).order_by("timestamp", direction="DESCENDING").limit(20)

    violations = []
    async for vdoc in vq.stream():
        v = vdoc.to_dict()
        violations.append({
            "violation_id": vdoc.id,
            "violation_type": v.get("violation_type", ""),
            "timestamp": v.get("timestamp", ""),
            "fine_amount": v.get("fine_amount", 0) or 0,
            "location": v.get("location"),
        })

    return {
        "driver_id": driver_id,
        "name": name,
        "phone": phone,
        "current_score": driver.get("current_score", 100),
        "total_violations": driver.get("total_violations", 0),
        "total_fines": driver.get("total_fines", 0.0),
        "last_violation": driver.get("updated_at"),
        "recent_violations": violations,
    }


# =============================================================================
# EMERGENCY CONTROL
# =============================================================================

@router.post("/emergency/trigger", response_model=EmergencyResponse, summary="Trigger emergency mode")
async def trigger_emergency(
    junction_id: str = Query(default="main", description="Junction to trigger emergency for"),
    emergency_type: str = Query(default="ambulance", description="Type: ambulance, fire, police"),
    lane: str = Query(default="north", description="Lane to force GREEN"),
):
    """
    Trigger emergency mode for a junction.
    This simulates an ambulance/emergency vehicle approach.
    All signals will be set to allow emergency vehicle passage.
    """
    controller = get_four_way_controller()
    if controller:
        controller.activate_emergency_mode(lane=lane)
        print(f"[ADMIN] 🚑 Emergency mode activated - Lane: {lane}")
    else:
        print(f"[ADMIN] ⚠️ Traffic controller not available for emergency mode")

    db = get_db()
    now = datetime.now().isoformat()
    await db.collection(Collections.EMERGENCY_STATUS).add({
        "junction_id": junction_id,
        "emergency_type": emergency_type,
        "active": True,
        "triggered_by": "admin",
        "triggered_at": now,
        "resolved_at": None,
    })

    return EmergencyResponse(
        status="triggered",
        message=f"Emergency mode activated for {emergency_type} at junction {junction_id}",
        affected_junctions=[junction_id],
        timestamp=now,
    )


@router.post("/emergency/clear", summary="Clear emergency mode")
async def clear_emergency(
    user: UserInfo = Depends(get_current_admin),
    junction_id: str = Query(default="main"),
):
    """Clear emergency mode and return to normal operation."""
    controller = get_four_way_controller()
    if controller:
        controller.deactivate_emergency_mode()
        print(f"[ADMIN] ✅ Emergency mode deactivated by {user.identifier}")

    db = get_db()
    now = datetime.now().isoformat()
    # Find active emergencies for this junction and deactivate
    q = db.collection(Collections.EMERGENCY_STATUS).where(
        filter=FieldFilter("junction_id", "==", junction_id)
    ).where(filter=FieldFilter("active", "==", True))
    async for doc in q.stream():
        await doc.reference.update({"active": False, "resolved_at": now})

    return {
        "status": "cleared",
        "message": f"Emergency mode cleared for junction {junction_id}",
        "timestamp": now,
    }


# =============================================================================
# ANALYTICS
# =============================================================================

@router.get("/analytics/violation-trends", summary="Get violation trends")
async def get_violation_trends(
    user: UserInfo = Depends(get_current_admin),
    days: int = Query(default=7, le=30),
):
    """Get violation trends over the specified number of days."""
    db = get_db()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Get violations since start_date
    q = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("timestamp", ">=", start_date)
    ).order_by("timestamp")

    trends = {}
    async for doc in q.stream():
        v = doc.to_dict()
        ts = v.get("timestamp", "")
        date = ts[:10] if len(ts) >= 10 else ts  # Extract YYYY-MM-DD
        vtype = v.get("violation_type", "unknown")
        if date not in trends:
            trends[date] = {"date": date, "total": 0, "by_type": {}}
        trends[date]["by_type"][vtype] = trends[date]["by_type"].get(vtype, 0) + 1
        trends[date]["total"] += 1

    return {
        "period_days": days,
        "start_date": start_date,
        "trends": list(trends.values()),
    }


@router.get("/analytics/hotspots", summary="Get violation hotspots")
async def get_violation_hotspots(
    user: UserInfo = Depends(get_current_admin),
):
    """Get locations with highest violation counts."""
    db = get_db()

    location_stats = {}
    async for doc in db.collection(Collections.VIOLATIONS).stream():
        v = doc.to_dict()
        loc = v.get("location")
        if loc:
            if loc not in location_stats:
                location_stats[loc] = {"violation_count": 0, "total_fines": 0.0}
            location_stats[loc]["violation_count"] += 1
            location_stats[loc]["total_fines"] += v.get("fine_amount", 0) or 0

    # Sort by violation count desc, take top 10
    hotspots = sorted(
        [{"location": k, **v} for k, v in location_stats.items()],
        key=lambda x: x["violation_count"],
        reverse=True,
    )[:10]

    return {"hotspots": hotspots}


def get_risk_level(score: int) -> str:
    """Get risk level string from score."""
    if score >= 90:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    elif score >= 30:
        return "poor"
    else:
        return "critical"
