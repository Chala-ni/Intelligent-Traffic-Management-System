"""
Intelligent Traffic Management System - Signal Control Router
API endpoints for traffic signal control using fuzzy logic.
"""

from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.fuzzy.traffic_controller import (
    FuzzyTrafficController,
    TrafficSignal,
    get_signal,
    FUZZY_AVAILABLE,
)

router = APIRouter(prefix="/signal", tags=["Signal Control"])


# =============================================================================
# Pydantic Models
# =============================================================================

class SignalUpdateRequest(BaseModel):
    """Request model for updating signal timing."""
    vehicle_count: int
    signal_id: Optional[str] = "main"


class SignalStateRequest(BaseModel):
    """Request model for setting signal state."""
    state: str  # 'red', 'yellow', 'green'
    duration: Optional[int] = None


class SignalResponse(BaseModel):
    """Response model for signal status."""
    signal_id: str
    state: str
    remaining_time: int
    green_duration: int
    yellow_duration: int
    red_duration: int
    vehicle_count: int
    traffic_level: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status", summary="Get signal status")
async def get_signal_status():
    """Get current traffic signal status."""
    signal = get_signal()
    return signal.get_status()


@router.post("/update", summary="Update signal timing based on traffic")
async def update_signal(request: SignalUpdateRequest):
    """
    Update signal timing based on vehicle count using fuzzy logic.
    
    This endpoint:
    1. Takes the current vehicle count
    2. Runs fuzzy inference to determine optimal green duration
    3. Updates the signal timing parameters
    
    The fuzzy rules:
    - Low traffic (0-5 vehicles) → Short green (~10-20s)
    - Medium traffic (5-15 vehicles) → Medium green (~20-40s)
    - High traffic (15+ vehicles) → Long green (~40-60s)
    """
    signal = get_signal()
    recommendation = signal.update_timing(request.vehicle_count)
    
    return {
        "message": "Signal timing updated",
        "recommendation": recommendation,
        "signal_status": signal.get_status(),
    }


@router.post("/set-state", summary="Manually set signal state")
async def set_signal_state(request: SignalStateRequest):
    """
    Manually set the traffic signal state.
    
    States: 'red', 'yellow', 'green'
    Optionally provide duration in seconds.
    """
    signal = get_signal()
    
    try:
        signal.set_state(request.state, request.duration)
    except ValueError as e:
        return {"error": str(e)}
    
    return {
        "message": f"Signal set to {request.state}",
        "signal_status": signal.get_status(),
    }


@router.post("/tick", summary="Advance signal timer")
async def tick_signal(seconds: int = Query(1, ge=1, le=60)):
    """
    Advance the signal timer by specified seconds.
    Simulates time passing for demo purposes.
    """
    signal = get_signal()
    state_changed = signal.tick(seconds)
    
    return {
        "state_changed": state_changed,
        "signal_status": signal.get_status(),
    }


@router.get("/compute", summary="Compute green duration without changing state")
async def compute_duration(vehicle_count: int = Query(..., ge=0, le=100)):
    """
    Compute the recommended green light duration for a given vehicle count.
    This is a read-only endpoint that doesn't modify the signal state.
    """
    controller = FuzzyTrafficController()
    return controller.get_signal_recommendation(vehicle_count)


@router.get("/fuzzy-status", summary="Check fuzzy system status")
async def fuzzy_status():
    """Check if scikit-fuzzy is available and the fuzzy system is working."""
    return {
        "fuzzy_available": FUZZY_AVAILABLE,
        "message": "Fuzzy inference system is ready" if FUZZY_AVAILABLE else "Running in fallback mode (linear interpolation)",
    }


@router.get("/simulation", summary="Get simulation HTML page", response_class=HTMLResponse)
async def get_simulation_page():
    """
    Redirect to the traffic light simulation page.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic Signal Simulation</title>
        <meta http-equiv="refresh" content="0; url=/static/simulation.html">
    </head>
    <body>
        <p>Redirecting to simulation...</p>
        <a href="/static/simulation.html">Click here if not redirected</a>
    </body>
    </html>
    """
