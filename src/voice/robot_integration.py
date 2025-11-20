"""
RoboPong Robot Integration
===========================
Bridge between voice controller and robot API (robo_pong.py).
Handles authentication, initialization, and execution of shot sequences.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

import sys
import os

# Add project root to Python path for robo_pong.py import
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# Try to import robo_pong API functions
try:
    from robo_pong import (
        log_on, log_off, start, reload,
        shot_cup_1, shot_cup_2, shot_cup_3,
        shot_cup_4, shot_cup_5, shot_cup_6,
        trick_shot, kill_shot
    )
    ROBOT_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Could not import robo_pong functions: {e}")
    print("         Make sure robo_pong.py is in the project root.")
    ROBOT_AVAILABLE = False

# =====================================================
# ROBOT CONTROLLER CLASS
# =====================================================

class RobotController:
    """
    Robot control interface for voice commands.
    
    Manages robot authentication token, initialization state,
    and provides high-level methods for executing shots.
    """
    
    def __init__(self):
        """Initialize robot controller (does not connect yet)."""
        self.token = None
        self.is_initialized = False
    
    def initialize(self):
        """
        Authenticate with robot API and run full initialization sequence.
        
        Steps:
        1. Log on and obtain authentication token
        2. Run start() sequence (pitch adjustment, ball pickup, slingshot load)
        
        Returns:
            str: Authentication token if successful, None otherwise
        """
        if not ROBOT_AVAILABLE:
            print("ERROR: Robot API not available. Check if robo_pong.py is in root directory.")
            return None
            
        if self.is_initialized:
            print("Robot already initialized.")
            return self.token
            
        try:
            print("Step 1/2: Logging in to robot API...")
            self.token = log_on()
            if not self.token:
                print("ERROR: No token received from log_on()")
                return None
            
            print(f"Token received: {self.token[:20]}...")
            
            print("Step 2/2: Running robot start sequence...")
            print("           (This takes ~30 seconds: pitch -> init -> pickup -> load)")
            start(self.token)
            
            self.is_initialized = True
            print("SUCCESS! Robot fully initialized and ready to shoot!")
            
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        return self.token
    
    def shutdown(self):
        """
        Log off from robot API and close connection.
        Resets token and initialization state.
        """
        if self.token:
            log_off('https://api.interactions.ics.unisg.ch/cherrybot2/operator')
            print("Robot connection closed.")
            self.token = None
            self.is_initialized = False
    
    def execute_shot(self, cup_number, shot_type="normal"):
        """
        Execute a shot to a specific cup (1-6).
        Each cup has calibrated trajectory values in robo_pong.py.
        Automatically reloads after shot.
        
        Args:
            cup_number (int): Target cup (1-6)
            shot_type (str): Shot description (for logging, not used functionally)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("ERROR: Robot not initialized. Say 'robot go' first.")
            return False
        
        if not self.token:
            print("ERROR: No authentication token. Reinitializing...")
            self.initialize()
        
        # Map cup numbers to shot functions
        shot_mapping = {
            1: shot_cup_1,
            2: shot_cup_2,
            3: shot_cup_3,
            4: shot_cup_4,
            5: shot_cup_5,
            6: shot_cup_6,
        }
        
        if cup_number in shot_mapping:
            print(f"Executing {shot_type} shot to cup {cup_number}...")
            try:
                shot_function = shot_mapping[cup_number]
                shot_function(self.token)
                print(f"Shot completed successfully!")
                return True
            except Exception as e:
                print(f"ERROR executing shot: {e}")
                return False
        else:
            print(f"ERROR: Cup {cup_number} is invalid (must be 1-6)")
            return False
    
    def execute_trickshot(self):
        """
        Execute a trick shot (curved trajectory with double rotation).
        Automatically reloads after shot.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("ERROR: Robot not initialized. Say 'robot go' first.")
            return False
        
        print("Executing trick shot...")
        try:
            trick_shot(self.token)
            print("Trick shot completed!")
            return True
        except Exception as e:
            print(f"ERROR executing trick shot: {e}")
            return False
    
    def execute_killshot(self):
        """
        Execute a kill shot (high power, aggressive trajectory).
        Automatically reloads after shot.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("ERROR: Robot not initialized. Say 'robot go' first.")
            return False
        
        print("Executing kill shot...")
        try:
            kill_shot(self.token)
            print("Kill shot completed!")
            return True
        except Exception as e:
            print(f"ERROR executing kill shot: {e}")
            return False
    
    def reload(self):
        """
        Manually trigger reload sequence (pick up ball, load slingshot).
        Note: This is automatically called after each shot.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            print("ERROR: Robot not initialized. Say 'robot go' first.")
            return False
        
        print("Reloading robot...")
        try:
            reload(self.token)
            print("Reload completed!")
            return True
        except Exception as e:
            print(f"ERROR reloading: {e}")
            return False

# =====================================================
# GLOBAL ROBOT INSTANCE
# =====================================================

# Single global robot controller instance shared by voice controller
robot = RobotController()
