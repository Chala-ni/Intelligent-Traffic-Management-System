"""
Driver API Router - Protected endpoints for driver mobile app
Requires JWT authentication with driver role.
"""

from datetime import datetime
from typing import List, Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from google.cloud.firestore_v1 import FieldFilter

from app.config import get_settings
from app.db.firestore_client import get_db, Collections
from app.routers.auth import get_current_driver, UserInfo, decode_token

settings = get_settings()
router = APIRouter(prefix="/driver", tags=["Driver App"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class DriverProfile(BaseModel):
    user_id: str
    phone: str
    name: Optional[str]
    plate_number: str
    current_score: int
    risk_level: str
    total_violations: int
    total_fines: float
    member_since: str


class ViolationRecord(BaseModel):
    violation_id: str
    violation_type: str
    timestamp: str
    location: Optional[str]
    fine_amount: float
    points_deducted: int
    status: str
    evidence_path: Optional[str]


class FineRecord(BaseModel):
    fine_id: int
    violation_type: str
    amount: float
    issued_date: str
    due_date: Optional[str]
    status: str  # 'unpaid', 'paid', 'overdue'
    breakdown: Optional[dict]


class NotificationRecord(BaseModel):
    notification_id: int
    title: str
    message: str
    notification_type: str  # 'warning', 'violation', 'info'
    timestamp: str
    read: bool


class FcmTokenRequest(BaseModel):
    fcm_token: str
    platform: str = "android"  # 'android' or 'ios'


class ProfileUpdate(BaseModel):
    """Request model for updating driver profile."""
    name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and len(v) < 2:
                raise ValueError('Name must be at least 2 characters')
            if len(v) > 100:
                raise ValueError('Name must be at most 100 characters')
            return v if v else None
        return None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.match(r'^[\+]?[0-9\s\-]{10,15}$', v):
                raise ValueError('Invalid phone number format')
            return v if v else None
        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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


async def get_plate_from_token(user: UserInfo) -> str:
    """Extract plate number from user token data."""
    db = get_db()
    doc = await db.collection(Collections.DRIVER_USERS).document(str(user.user_id)).get()
    if doc.exists:
        return doc.to_dict().get("plate_number", "")
    return ""


# =============================================================================
# DRIVER PROFILE ENDPOINTS
# =============================================================================

@router.get("/me", response_model=DriverProfile, summary="Get driver profile")
async def get_driver_profile(user: UserInfo = Depends(get_current_driver)):
    """
    Get the current driver's profile including:
    - Personal details
    - Current safety score
    - Total violations and fines
    """
    db = get_db()

    # Get driver user details
    doc = await db.collection(Collections.DRIVER_USERS).document(str(user.user_id)).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    driver_user = doc.to_dict()
    plate_number = driver_user.get("plate_number", "")

    # Get score from drivers collection
    driver_doc = await db.collection(Collections.DRIVERS).document(plate_number).get()
    if driver_doc.exists:
        ds = driver_doc.to_dict()
        current_score = ds.get("current_score", 100)
        total_violations = ds.get("total_violations", 0)
        total_fines = ds.get("total_fines", 0.0)
    else:
        current_score = 100
        total_violations = 0
        total_fines = 0.0

    return DriverProfile(
        user_id=doc.id,
        phone=driver_user.get("phone", ""),
        name=driver_user.get("name"),
        plate_number=plate_number,
        current_score=current_score,
        risk_level=get_risk_level(current_score),
        total_violations=total_violations,
        total_fines=total_fines,
        member_since=driver_user.get("created_at") or datetime.now().isoformat(),
    )


@router.put("/me", response_model=DriverProfile, summary="Update driver profile")
async def update_driver_profile(
    data: ProfileUpdate,
    user: UserInfo = Depends(get_current_driver),
):
    """
    Update the current driver's profile.
    Currently supports updating: name, phone.
    """
    db = get_db()

    doc = await db.collection(Collections.DRIVER_USERS).document(str(user.user_id)).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    update_fields = {}

    if data.name is not None:
        update_fields["name"] = data.name

    if data.phone is not None and data.phone != doc.to_dict().get("phone"):
        # Check phone uniqueness
        phone_query = (
            db.collection(Collections.DRIVER_USERS)
            .where(filter=FieldFilter("phone", "==", data.phone))
            .limit(1)
        )
        async for existing in phone_query.stream():
            if existing.id != str(user.user_id):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number already in use by another account"
                )
        update_fields["phone"] = data.phone

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields["updated_at"] = datetime.utcnow().isoformat()
    await db.collection(Collections.DRIVER_USERS).document(str(user.user_id)).update(update_fields)

    # Return updated profile
    return await get_driver_profile(user)


@router.get("/my-violations", summary="Get driver's violation history")
async def get_my_violations(
    user: UserInfo = Depends(get_current_driver),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Get list of violations for the logged-in driver.
    Filtered by the driver's plate number.
    """
    plate_number = await get_plate_from_token(user)
    db = get_db()

    # Query violations where driver_id or license_plate matches
    all_violations = []
    # Query by driver_id
    q1 = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("driver_id", "==", plate_number)
    ).order_by("timestamp", direction="DESCENDING")
    async for doc in q1.stream():
        d = doc.to_dict()
        d["_id"] = doc.id
        all_violations.append(d)

    # Query by license_plate (avoid duplicates)
    seen_ids = {v["_id"] for v in all_violations}
    q2 = db.collection(Collections.VIOLATIONS).where(
        filter=FieldFilter("license_plate", "==", plate_number)
    ).order_by("timestamp", direction="DESCENDING")
    async for doc in q2.stream():
        if doc.id not in seen_ids:
            d = doc.to_dict()
            d["_id"] = doc.id
            all_violations.append(d)

    # Sort combined results by timestamp desc
    all_violations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    total = len(all_violations)
    page = all_violations[offset: offset + limit]

    return {
        "violations": [
            {
                "violation_id": v.get("violation_id", v["_id"]),
                "violation_type": v.get("violation_type", ""),
                "timestamp": v.get("timestamp", ""),
                "location": v.get("location"),
                "fine_amount": v.get("fine_amount", 0),
                "points_deducted": v.get("points_deducted", 0),
                "evidence_path": v.get("snapshot_path"),
                "notes": v.get("notes"),
                "status": "recorded",
            }
            for v in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/my-fines", summary="Get driver's unpaid fines")
async def get_my_fines(
    user: UserInfo = Depends(get_current_driver),
    status_filter: Optional[str] = Query(default=None, description="Filter by: unpaid, paid, all"),
):
    """
    Get list of fines for the logged-in driver.
    Default shows unpaid fines only.
    """
    plate_number = await get_plate_from_token(user)
    db = get_db()

    fines = []

    # Query from dynamic_fines collection
    q = db.collection(Collections.DYNAMIC_FINES).where(
        filter=FieldFilter("plate_number", "==", plate_number)
    ).order_by("created_at", direction="DESCENDING")
    async for doc in q.stream():
        f = doc.to_dict()
        fines.append({
            "fine_id": doc.id,
            "violation_type": f.get("zone_type", ""),
            "amount": f.get("total_fine", 0),
            "issued_date": f.get("created_at", ""),
            "due_date": None,
            "status": "unpaid",
            "breakdown": {
                "base": f.get("base_penalty", 0),
                "duration": f.get("duration_penalty", 0),
                "impact": f.get("impact_penalty", 0),
            },
        })

    # Also get fines from violations collection
    for field_name in ("driver_id", "license_plate"):
        q2 = db.collection(Collections.VIOLATIONS).where(
            filter=FieldFilter(field_name, "==", plate_number)
        ).order_by("timestamp", direction="DESCENDING")
        async for doc in q2.stream():
            v = doc.to_dict()
            if v.get("fine_amount", 0) > 0:
                fines.append({
                    "fine_id": hash(doc.id) % 10000,
                    "violation_type": v.get("violation_type", ""),
                    "amount": v.get("fine_amount", 0),
                    "issued_date": v.get("timestamp", ""),
                    "due_date": None,
                    "status": "unpaid",
                    "breakdown": None,
                })

    # Deduplicate by fine_id
    seen = set()
    unique_fines = []
    for f in fines:
        fid = f["fine_id"]
        if fid not in seen:
            seen.add(fid)
            unique_fines.append(f)
    fines = unique_fines

    total_unpaid = sum(f["amount"] for f in fines if f["status"] == "unpaid")

    return {
        "fines": fines,
        "total_count": len(fines),
        "total_unpaid_amount": total_unpaid,
        "currency": "LKR",
    }


@router.get("/notifications", summary="Get driver notifications")
async def get_notifications(
    user: UserInfo = Depends(get_current_driver),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, le=50),
):
    """
    Get personal notifications/alerts for the driver.
    Includes warnings, violation notices, and system messages.
    """
    plate_number = await get_plate_from_token(user)
    db = get_db()

    notifications = []

    # Query from driver_notifications collection
    q = db.collection(Collections.DRIVER_NOTIFICATIONS).where(
        filter=FieldFilter("plate_number", "==", plate_number)
    )
    if unread_only:
        q = q.where(filter=FieldFilter("read", "==", False))
    q = q.order_by("timestamp", direction="DESCENDING").limit(limit)

    async for doc in q.stream():
        n = doc.to_dict()
        notifications.append({
            "notification_id": doc.id,
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "notification_type": n.get("notification_type", "info"),
            "timestamp": n.get("timestamp", ""),
            "read": bool(n.get("read", False)),
        })

    # Generate notifications from recent violations
    for field_name in ("driver_id", "license_plate"):
        vq = db.collection(Collections.VIOLATIONS).where(
            filter=FieldFilter(field_name, "==", plate_number)
        ).order_by("timestamp", direction="DESCENDING").limit(10)
        async for doc in vq.stream():
            v = doc.to_dict()
            notifications.append({
                "notification_id": hash(f"{v.get('timestamp','')}{v.get('violation_type','')}") % 100000,
                "title": f"{v.get('violation_type','').replace('_', ' ').title()} Recorded",
                "message": f"A {v.get('violation_type','')} violation was recorded. Fine: LKR {v.get('fine_amount',0):.2f}",
                "notification_type": "violation",
                "timestamp": v.get("timestamp", ""),
                "read": False,
            })

    # Sort by timestamp desc and limit
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    notifications = notifications[:limit]

    return {
        "notifications": notifications,
        "unread_count": sum(1 for n in notifications if not n["read"]),
        "total_count": len(notifications),
    }


@router.post("/notifications/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notification_id: str,
    user: UserInfo = Depends(get_current_driver),
):
    """Mark a specific notification as read."""
    db = get_db()
    await db.collection(Collections.DRIVER_NOTIFICATIONS).document(notification_id).update(
        {"read": True}
    )
    return {"status": "marked_read", "notification_id": notification_id}


@router.get("/score-history", summary="Get driver's score history")
async def get_score_history(
    user: UserInfo = Depends(get_current_driver),
    days: int = Query(default=30, le=90),
):
    """
    Get driver's safety score history over time.
    Shows how score has changed with each violation.
    """
    plate_number = await get_plate_from_token(user)
    db = get_db()

    # Get violations with points to calculate historical scores
    violations = []
    for field_name in ("driver_id", "license_plate"):
        q = db.collection(Collections.VIOLATIONS).where(
            filter=FieldFilter(field_name, "==", plate_number)
        ).order_by("timestamp")
        async for doc in q.stream():
            d = doc.to_dict()
            d["_id"] = doc.id
            violations.append(d)

    # Deduplicate and sort by timestamp ascending
    seen = set()
    unique = []
    for v in violations:
        if v["_id"] not in seen:
            seen.add(v["_id"])
            unique.append(v)
    unique.sort(key=lambda x: x.get("timestamp", ""))

    # Build score history
    score_history = []
    current_score = 100
    for v in unique:
        pts = v.get("points_deducted", 0)
        current_score = max(0, current_score - pts)
        score_history.append({
            "timestamp": v.get("timestamp", ""),
            "score": current_score,
            "change": -pts,
            "reason": v.get("violation_type", ""),
        })

    # Get current score from drivers collection
    driver_doc = await db.collection(Collections.DRIVERS).document(plate_number).get()
    final_score = driver_doc.to_dict().get("current_score", current_score) if driver_doc.exists else current_score

    return {
        "current_score": final_score,
        "history": score_history[-50:],
        "trend": "stable" if len(score_history) < 2 else (
            "improving" if score_history[-1]["score"] > score_history[0]["score"] else "declining"
        ),
    }


# =============================================================================
# FCM TOKEN REGISTRATION
# =============================================================================

@router.post("/fcm-token", summary="Register FCM push token")
async def register_fcm_token(
    body: FcmTokenRequest,
    user: UserInfo = Depends(get_current_driver),
):
    """
    Register or update the driver's FCM push notification token.
    Called by the mobile app on startup and token refresh.
    """
    plate_number = await get_plate_from_token(user)
    if not plate_number:
        raise HTTPException(status_code=404, detail="Driver not found")

    db = get_db()
    # Use plate_number as document ID for uniqueness (upsert)
    await db.collection(Collections.DRIVER_FCM_TOKENS).document(plate_number).set({
        "plate_number": plate_number,
        "fcm_token": body.fcm_token,
        "platform": body.platform,
        "updated_at": datetime.now().isoformat(),
    })

    return {"status": "ok", "message": "FCM token registered"}


@router.delete("/fcm-token", summary="Remove FCM push token")
async def remove_fcm_token(
    user: UserInfo = Depends(get_current_driver),
):
    """Remove driver's FCM token (e.g. on logout)."""
    plate_number = await get_plate_from_token(user)

    db = get_db()
    await db.collection(Collections.DRIVER_FCM_TOKENS).document(plate_number).delete()

    return {"status": "ok", "message": "FCM token removed"}
