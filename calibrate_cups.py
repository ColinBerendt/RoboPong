"""
RoboPong Calibration Tool
=========================
Interactive tool for calibrating shot trajectories.
Use to determine optimal diagonal and rotation values for each cup position.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

import time
import pygame
from robo_pong import log_on, log_off, init, sling_grab, toggle, diagonal, rotate, reload, change_pitch

# Initialize pygame mixer for sound effects
pygame.mixer.init()

token = None

def play_sound(filename):
    """Play a sound effect from the sounds/ folder."""
    try:
        sound = pygame.mixer.Sound(f"sounds/{filename}")
        sound.play()
    except Exception as e:
        print(f"Could not play sound: {e}")

def main():
    """
    Calibration command-line interface.
    
    Commands:
        start                  - Initialize robot
        shot <diagonal> <rotate> - Test shot with given parameters
        quit                   - Exit and log off
    
    Example:
        Command: start
        Command: shot 9.5 0.3
        Command: shot 10.2 0.5
        Command: quit
    """
    global token
    
    print("\n" + "="*60)
    print("RoboPong Calibration Mode")
    print("="*60)
    print("Commands:")
    print("  start              - Initialize robot")
    print("  shot <diag> <rot>  - Test shot (e.g. 'shot 9.5 0.3')")
    print("  quit               - Exit")
    print("="*60 + "\n")
    
    while True:
        command = input("\nCommand: ").strip().lower()
        
        if not command:
            continue
            
        command_split = command.split()
        cmd = command_split[0]
        
        try:
            # =====================================
            # COMMAND: START (Initialize Robot)
            # =====================================
            if cmd == "start":
                print("Logging in to robot API...")
                token = log_on()
                print("Moving to init position...")
                change_pitch(token, -90)
                time.sleep(4)
                init(token)
                print("Ready for calibration!")
                
            # =====================================
            # COMMAND: SHOT (Test Trajectory)
            # =====================================
            elif cmd == "shot" or cmd == "shoot":
                if token is None:
                    print("ERROR: Please run 'start' first")
                    continue
                if len(command_split) != 3:
                    print("ERROR: Invalid syntax")
                    print("Usage: shot <diagonal> <rotate>")
                    print("Example: shot 9.3 0.5")
                    continue
                
                diagonal_val = float(command_split[1])
                rotate_val = float(command_split[2])
                
                print(f"\nTesting: diagonal={diagonal_val}, rotation={rotate_val}")
                print("Step 1/6: Grabbing slingshot...")
                sling_grab(token)
                time.sleep(1)
                
                print("Step 2/6: Closing gripper...")
                toggle(token, 255)
                time.sleep(1)
                
                print(f"Step 3/6: Diagonal movement ({diagonal_val})...")
                diagonal(token, diagonal_val)
                time.sleep(1)
                
                print(f"Step 4/6: Rotation ({rotate_val})...")
                rotate(token, rotate_val)
                time.sleep(1)
                
                print("Step 5/6: Releasing...")
                toggle(token, 400)
                play_sound("shot.mp3")
                time.sleep(1)
                
                print("Step 6/6: Reloading... (not implemented in calibration)")
                print("Shot complete! Observe result and adjust values.\n")
                
            # =====================================
            # COMMAND: QUIT
            # =====================================
            elif cmd == "quit":
                if token is not None:
                    print("Logging off...")
                    log_off('https://api.interactions.ics.unisg.ch/cherrybot2/operator')
                print("Goodbye!")
                return
            else:
                print("Unknown command. Try: start, shot <diag> <rot>, quit")
                
        except ValueError:
            print("ERROR: Invalid number format. Use decimals like 9.3 or 0.5")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    main()

