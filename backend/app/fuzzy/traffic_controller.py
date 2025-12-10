"""
Intelligent Traffic Management System - Fuzzy Logic Traffic Controller
Uses fuzzy logic to determine optimal green light duration based on traffic conditions.

Research Component for University Grading
==========================================
This module demonstrates fuzzy inference systems for traffic signal optimization.
Uses scikit-fuzzy for fuzzy set operations and rule-based inference.
"""

import numpy as np

try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("⚠️ scikit-fuzzy not installed. Run: pip install scikit-fuzzy")


class FuzzyTrafficController:
    """
    Fuzzy logic controller for adaptive traffic signal timing.
    
    Input: Vehicle count at intersection
    Output: Green light duration in seconds
    
    Fuzzy Rules:
    - Low traffic (0-5 vehicles) → Short green (10-20s)
    - Medium traffic (5-15 vehicles) → Medium green (20-40s)
    - High traffic (15+ vehicles) → Long green (40-60s)
    """
    
    def __init__(self, min_green: int = 10, max_green: int = 60):
        """
        Initialize the fuzzy controller.
        
        Args:
            min_green: Minimum green light duration (seconds)
            max_green: Maximum green light duration (seconds)
        """
        self.min_green = min_green
        self.max_green = max_green
        self.simulation = None
        
        if FUZZY_AVAILABLE:
            self._setup_fuzzy_system()
        else:
            print("⚠️ Running in fallback mode (linear interpolation)")
    
    def _setup_fuzzy_system(self):
        """Set up the fuzzy inference system."""
        # Define fuzzy variables
        
        # Input: Vehicle count (0 to 30)
        self.vehicle_count = ctrl.Antecedent(np.arange(0, 31, 1), 'vehicle_count')
        
        # Output: Green light duration (10 to 60 seconds)
        self.green_duration = ctrl.Consequent(np.arange(self.min_green, self.max_green + 1, 1), 'green_duration')
        
        # Define membership functions for vehicle count
        self.vehicle_count['low'] = fuzz.trimf(self.vehicle_count.universe, [0, 0, 8])
        self.vehicle_count['medium'] = fuzz.trimf(self.vehicle_count.universe, [5, 12, 20])
        self.vehicle_count['high'] = fuzz.trimf(self.vehicle_count.universe, [15, 30, 30])
        
        # Define membership functions for green duration
        self.green_duration['short'] = fuzz.trimf(self.green_duration.universe, 
                                                   [self.min_green, self.min_green, 25])
        self.green_duration['medium'] = fuzz.trimf(self.green_duration.universe, 
                                                    [20, 35, 50])
        self.green_duration['long'] = fuzz.trimf(self.green_duration.universe, 
                                                  [40, self.max_green, self.max_green])
        
        # Define fuzzy rules
        rule1 = ctrl.Rule(self.vehicle_count['low'], self.green_duration['short'])
        rule2 = ctrl.Rule(self.vehicle_count['medium'], self.green_duration['medium'])
        rule3 = ctrl.Rule(self.vehicle_count['high'], self.green_duration['long'])
        
        # Create control system
        self.traffic_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
        self.simulation = ctrl.ControlSystemSimulation(self.traffic_ctrl)
        
        print("✅ Fuzzy traffic controller initialized")
    
    def compute_green_duration(self, vehicle_count: int) -> int:
        """
        Compute optimal green light duration based on vehicle count.
        
        Args:
            vehicle_count: Number of vehicles waiting at intersection
            
        Returns:
            Green light duration in seconds
        """
        # Clamp vehicle count to valid range
        vehicle_count = max(0, min(30, vehicle_count))
        
        if self.simulation is not None:
            try:
                self.simulation.input['vehicle_count'] = vehicle_count
                self.simulation.compute()
                duration = int(self.simulation.output['green_duration'])
                return max(self.min_green, min(self.max_green, duration))
            except Exception as e:
                print(f"⚠️ Fuzzy computation error: {e}")
        
        # Fallback: Linear interpolation
        return self._linear_fallback(vehicle_count)
    
    def _linear_fallback(self, vehicle_count: int) -> int:
        """Fallback linear interpolation if fuzzy system unavailable."""
        # Map 0-30 vehicles to min_green-max_green seconds
        ratio = vehicle_count / 30.0
        duration = self.min_green + ratio * (self.max_green - self.min_green)
        return int(duration)
    
    def get_traffic_level(self, vehicle_count: int) -> str:
        """
        Get traffic level classification.
        
        Args:
            vehicle_count: Number of vehicles
            
        Returns:
            Traffic level: 'low', 'medium', or 'high'
        """
        if vehicle_count <= 5:
            return 'low'
        elif vehicle_count <= 15:
            return 'medium'
        else:
            return 'high'
    
    def get_signal_recommendation(self, vehicle_count: int) -> dict:
        """
        Get full signal recommendation with all details.
        
        Args:
            vehicle_count: Number of vehicles at intersection
            
        Returns:
            Dictionary with duration, traffic_level, and recommendation details
        """
        duration = self.compute_green_duration(vehicle_count)
        traffic_level = self.get_traffic_level(vehicle_count)
        
        return {
            "vehicle_count": vehicle_count,
            "traffic_level": traffic_level,
            "green_duration_sec": duration,
            "yellow_duration_sec": 3,  # Standard yellow light
            "red_duration_sec": max(10, 70 - duration),  # Remaining time for cross traffic
            "cycle_time_sec": duration + 3 + max(10, 70 - duration),
            "fuzzy_available": FUZZY_AVAILABLE,
        }


# =============================================================================
# Traffic Signal State Machine
# =============================================================================

class TrafficSignal:
    """
    Traffic signal state machine with timing control.
    """
    
    STATES = ['red', 'yellow', 'green']
    
    def __init__(self, signal_id: str = "main"):
        self.signal_id = signal_id
        self.state = 'red'
        self.remaining_time = 30  # Default red duration
        self.green_duration = 30
        self.yellow_duration = 3
        self.red_duration = 30
        self.controller = FuzzyTrafficController()
        self.last_update = None
        self.vehicle_count = 0
    
    def update_timing(self, vehicle_count: int):
        """Update signal timing based on vehicle count."""
        self.vehicle_count = vehicle_count
        recommendation = self.controller.get_signal_recommendation(vehicle_count)
        
        self.green_duration = recommendation['green_duration_sec']
        self.red_duration = recommendation['red_duration_sec']
        
        return recommendation
    
    def set_state(self, state: str, duration: int = None):
        """Set signal state with optional duration override."""
        if state not in self.STATES:
            raise ValueError(f"Invalid state: {state}. Must be one of {self.STATES}")
        
        self.state = state
        
        if duration is not None:
            self.remaining_time = duration
        else:
            if state == 'green':
                self.remaining_time = self.green_duration
            elif state == 'yellow':
                self.remaining_time = self.yellow_duration
            else:
                self.remaining_time = self.red_duration
        
        import time
        self.last_update = time.time()
    
    def tick(self, elapsed_seconds: int = 1) -> bool:
        """
        Advance the signal timer.
        
        Args:
            elapsed_seconds: Time elapsed since last tick
            
        Returns:
            True if state changed, False otherwise
        """
        self.remaining_time -= elapsed_seconds
        
        if self.remaining_time <= 0:
            # State transition
            if self.state == 'green':
                self.set_state('yellow')
            elif self.state == 'yellow':
                self.set_state('red')
            else:  # red
                self.set_state('green')
            return True
        
        return False
    
    def get_status(self) -> dict:
        """Get current signal status."""
        return {
            "signal_id": self.signal_id,
            "state": self.state,
            "remaining_time": self.remaining_time,
            "green_duration": self.green_duration,
            "yellow_duration": self.yellow_duration,
            "red_duration": self.red_duration,
            "vehicle_count": self.vehicle_count,
            "traffic_level": self.controller.get_traffic_level(self.vehicle_count),
        }


# Global signal instance
_signal: TrafficSignal = None


def get_signal() -> TrafficSignal:
    """Get or create the global traffic signal instance."""
    global _signal
    if _signal is None:
        _signal = TrafficSignal()
    return _signal


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    print("🚦 Fuzzy Traffic Controller Test\n")
    
    controller = FuzzyTrafficController()
    
    # Test with different vehicle counts
    test_counts = [0, 3, 5, 8, 10, 15, 20, 25, 30]
    
    print("Vehicle Count | Traffic Level | Green Duration")
    print("-" * 50)
    
    for count in test_counts:
        rec = controller.get_signal_recommendation(count)
        print(f"    {count:2d}        |    {rec['traffic_level']:6s}     |     {rec['green_duration_sec']:2d}s")
    
    print("\n✅ Fuzzy controller test complete!")
