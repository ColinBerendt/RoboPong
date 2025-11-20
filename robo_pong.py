"""
RoboPong Robot API
==================
Core API for controlling the CherryBot2 robot arm for Beer Pong.
Provides low-level movement functions, gripper control, and predefined shot sequences.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

import requests
import time
import numpy as np
import json
import pygame

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# =====================================================
# CONFIGURATION
# =====================================================

BASE_URL = 'https://api.interactions.ics.unisg.ch/cherrybot2'
LOGIN_URL = f'{BASE_URL}/operator'
TCP_URL = f'{BASE_URL}/tcp'
MOVEMENT_URL = f'{BASE_URL}/tcp/target'
GRIPPER_URL = f'{BASE_URL}/gripper'

USER_DATA = {
    "name": "Colin Berendt, Yannik Holenstein, Robin Sutter",
    "email": "colinwai-loen.berendt@student.unisg.ch, yannik.holenstein@student.unisg.ch, robin.sutter@student.unisg.ch"
}

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def play_sound(filename):
    """Play a sound effect from the sounds/ folder."""
    try:
        sound = pygame.mixer.Sound(f"sounds/{filename}")
        sound.play()
    except Exception as e:
        print(f"Could not play sound: {e}")

def catch_clause(response):
    """Check API response status and print result."""
    if response.status_code == 200:
        print("Success in moving robot")
    else:
        print(f"Error: {response.status_code}")

# =====================================================
# AUTHENTICATION
# =====================================================

def log_on():
    """
    Authenticate with the robot API and obtain access token.
    Automatically logs off any existing session first.
    
    Returns:
        str: Authentication token for API requests
    """
    log_off(LOGIN_URL)
    print("Connecting to robot API...")

    time.sleep(1)
    response = requests.post(LOGIN_URL, json=USER_DATA)
    catch_clause(response)

    time.sleep(1)
    response = requests.get(LOGIN_URL)
    data = response.json()
    token = data.get('token')
    print(f"Successfully authenticated. Token: {token[:20]}...")
    return token

def log_off(url):
    """
    Log off from the robot API and end the current session.
    
    Args:
        url (str): API login URL
    """
    play_sound("log_off.mp3")
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        token = data.get('token')

        if token:
            time.sleep(1)
            url_token = f"{url}/{token}"
            header = {'accept': '*/*'}
            requests.delete(url_token, headers=header)
            print("Logged off successfully.")

# =====================================================
# POSITION & MOVEMENT
# =====================================================

def get_position(token):
    """
    Get current TCP (Tool Center Point) position and rotation of the robot arm.
    
    Args:
        token (str): Authentication token
        
    Returns:
        tuple: (x, y, z, roll, pitch, yaw) coordinates and rotations
    """
    headers = {
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    response = requests.get(TCP_URL, headers=headers)
    data = response.json()

    x = data["coordinate"]["x"]
    y = data["coordinate"]["y"]
    z = data["coordinate"]["z"]

    roll = data["rotation"]["roll"]
    pitch = data["rotation"]["pitch"]
    yaw = data["rotation"]["yaw"]

    return x, y, z, roll, pitch, yaw

def change_pitch(token, param):
    """
    Change the pitch angle of the robot arm while maintaining current position.
    
    Args:
        token (str): Authentication token
        param (int): Pitch angle change in degrees (positive = down, negative = up)
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)
    x, y, z, roll, pitch, yaw = get_position(token)

    data = {
        'target': {
            'coordinate': {
                'x': x,
                'y': y,
                'z': z
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch + int(param),
                'yaw': yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def init(token):
    """
    Move robot arm to initialization/home position.
    This is the default safe position above the table.
    
    Args:
        token (str): Authentication token
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }

    time.sleep(1)
    data = {
        'target': {
            'coordinate': {
                'x': 0,
                'y': -410,
                'z': 295
            },
            'rotation': {
                'roll': -180,
                'pitch': 0,
                'yaw': -90
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def toggle(token, param=None):
    """
    Control gripper open/close state.
    
    Args:
        token (str): Authentication token
        param (int, optional): Gripper strength (0-400)
                               255 = closed (gripping)
                               370 = semi-closed (ball grip)
                               400 = fully open (default)
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }

    time.sleep(1)

    if param is not None:
        grip_strength = json.dumps(int(param))
        print(f"Setting gripper to {param}...")
    else:
        grip_strength = json.dumps(int(400))
        print("Setting gripper to default (400 = open)...")
    
    time.sleep(1)
    response = requests.put(GRIPPER_URL, headers=header, data=grip_strength)
    catch_clause(response)

def rotate(token, param):
    """
    Rotate the robot arm around the Z-axis (horizontal rotation).
    Both position and yaw angle are adjusted to maintain consistent orientation.
    
    Args:
        token (str): Authentication token
        param (float): Rotation angle in degrees
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    x, y, z, roll, pitch, yaw = get_position(token)

    param = float(param)
    
    # Convert angle to radians and apply rotation matrix
    param_radian = np.radians(param)
    rotation_matrix = np.array([
        [np.cos(param_radian), -np.sin(param_radian)],
        [np.sin(param_radian), np.cos(param_radian)]
    ])
    new_position = np.dot(rotation_matrix, np.array([x, y]))
    new_yaw = yaw + param

    data = {
        'target': {
            'coordinate': {
                'x': new_position[0],
                'y': new_position[1],
                'z': z,
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch,
                'yaw': new_yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def diagonal(token, param, angle=56):
    """
    Move robot arm diagonally in the Y-Z plane (for shot release positioning).
    This is used to pull back the slingshot mechanism before releasing.
    
    Args:
        token (str): Authentication token
        param (float): Movement distance multiplier (scaled by 10)
        angle (int, optional): Angle in degrees for diagonal trajectory (default: 56)
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    x, y, z, roll, pitch, yaw = get_position(token)

    param = float(param)
    angle_radians = np.radians(float(angle))
    
    # Calculate diagonal movement in Y-Z plane at specified angle
    # X remains fixed; distribute distance across Y and Z components
    diagonal_distance = 10 * param
    delta_y = diagonal_distance * np.cos(angle_radians)
    delta_z = diagonal_distance * np.sin(angle_radians)
    
    data = {
        'target': {
            'coordinate': {
                'x': x,
                'y': y + delta_y,
                'z': z - delta_z
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

# =====================================================
# BALL HANDLING & SETUP
# =====================================================

def ball_pickup_init(token):
    """
    Move to ball pickup preparation position (above ball).
    
    Args:
        token (str): Authentication token
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    data = {
        'target': {
            'coordinate': {
                'x': -270,
                'y': -255,
                'z': 30
            },
            'rotation': {
                'roll': -180,
                'pitch': 0,
                'yaw': -180
            }
        },
        'speed': 100
    }

    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def ball_pickup(token):
    """
    Lower gripper to ball level and prepare to grab.
    
    Args:
        token (str): Authentication token
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    data = {
        'target': {
            'coordinate': {
                'x': -270,
                'y': -255,
                'z': 10
            },
            'rotation': {
                'roll': -180,
                'pitch': 0,
                'yaw': -180
            }
        },
        'speed': 100
    }

    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def sling_grab(token):
    """
    Move to slingshot grab position (before shot).
    This positions the gripper to pull back the slingshot mechanism.
    
    Args:
        token (str): Authentication token
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    data = {
        'target': {
            'coordinate': {
                'x': 0,
                'y': -540,
                'z': 215
            },
            'rotation': {
                'roll': 180,
                'pitch': -57,
                'yaw': -90
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def setup_ball(token):
    """
    Move ball into shooting position (in slingshot).
    
    Args:
        token (str): Authentication token
    """
    header = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }
    time.sleep(1)

    data = {
        'target': {
            'coordinate': {
                'x': 0,
                'y': -560,
                'z': 300
            },
            'rotation': {
                'roll': 180,
                'pitch': 0,
                'yaw': -90
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=header, json=data)
    catch_clause(response)

def change_x(token, param):
    """
    Move robot along X-axis (left/right) while maintaining orientation.
    
    Args:
        token (str): Authentication token
        param (int): Distance to move in mm (positive = right, negative = left)
    """
    x, y, z, roll, pitch, yaw = get_position(token)
    
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }

    data = {
        'target': {
            'coordinate': {
                'x': x + int(param),
                'y': y,
                'z': z
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=headers, json=data)
    catch_clause(response)

def change_y(token, param):
    """
    Move robot along Y-axis (forward/backward) while maintaining orientation.
    
    Args:
        token (str): Authentication token
        param (int): Distance to move in mm (positive = forward, negative = backward)
    """
    x, y, z, roll, pitch, yaw = get_position(token)

    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }

    data = {
        'target': {
            'coordinate': {
                'x': x,
                'y': y - int(param),
                'z': z
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=headers, json=data)
    catch_clause(response)

def change_z(token, param):
    """
    Move robot along Z-axis (up/down) while maintaining orientation.
    
    Args:
        token (str): Authentication token
        param (int): Distance to move in mm (positive = up, negative = down)
    """
    x, y, z, roll, pitch, yaw = get_position(token)

    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
        'Authentication': token
    }

    data = {
        'target': {
            'coordinate': {
                'x': x,
                'y': y,
                'z': z + int(param)
            },
            'rotation': {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw
            }
        },
        'speed': 100
    }

    time.sleep(1)
    response = requests.put(MOVEMENT_URL, headers=headers, json=data)
    catch_clause(response)

# =====================================================
# HIGH-LEVEL SEQUENCES
# =====================================================

def l_movement(token):
    """
    Perform L-shaped movement (used for celebration/emote).
    
    Args:
        token (str): Authentication token
    """
    change_z(token, 400)
    time.sleep(4)
    change_z(token, -350)
    time.sleep(4)
    change_x(token, 225)

def reload(token):
    """
    Complete reload sequence: return to init, pick up new ball, load into slingshot.
    This is called automatically after each shot.
    
    Args:
        token (str): Authentication token
    """
    init(token)
    time.sleep(1)
    toggle(token)
    time.sleep(1)
    ball_pickup_init(token)
    time.sleep(1)
    ball_pickup(token)
    time.sleep(5)
    toggle(token, 370)
    time.sleep(1)
    init(token)
    time.sleep(1)
    setup_ball(token)
    time.sleep(4)
    toggle(token)
    init(token)

def start(token):
    """
    Complete robot initialization sequence.
    Performs: pitch adjustment -> init position -> ball pickup -> load slingshot.
    Should be called once after log_on() before any shots.
    
    Args:
        token (str): Authentication token
    """
    play_sound("log_on.mp3")
    change_pitch(token, -90)
    time.sleep(4)
    init(token)
    time.sleep(4)
    ball_pickup_init(token)
    time.sleep(4)
    ball_pickup(token)
    time.sleep(4)
    toggle(token, 370)
    init(token)
    time.sleep(4)
    setup_ball(token)
    time.sleep(3)
    toggle(token)
    init(token)

def emote(token):
    """
    Perform celebration/emote animation (L-movement).
    
    Args:
        token (str): Authentication token
    """
    change_pitch(token, -90)
    time.sleep(4)
    l_movement(token)

def pickup_ball(token):
    """
    Standalone ball pickup sequence without full reload.
    
    Args:
        token (str): Authentication token
    """
    toggle(token, 400)
    ball_pickup_init(token)
    time.sleep(4)
    ball_pickup(token)
    time.sleep(4)
    toggle(token, 370)
    play_sound("pick_up.mp3")
    init(token)
    time.sleep(5)
    setup_ball(token)
    time.sleep(3)
    toggle(token)
    init(token)

# =====================================================
# SHOT SEQUENCES (Cup 1-6)
# =====================================================
# Each cup has calibrated diagonal and rotation values
# These values were determined through testing for accuracy 

def shot_cup_1(token):
    """
    Execute shot to Cup 1 (back left).
    Calibrated values: diagonal=12, rotation=-0.6
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 12)
    time.sleep(1)
    rotate(token, -0.6)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

def shot_cup_2(token):
    """
    Execute shot to Cup 2 (back center-left).
    Calibrated values: diagonal=9.3, rotation=0
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 9.3)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

def shot_cup_3(token):
    """
    Execute shot to Cup 3 (back center-right).
    Calibrated values: diagonal=9.9, rotation=0.5
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 9.9)
    time.sleep(1)
    rotate(token, 0.5)
    time.sleep(1)
    toggle(token, 400)
    time.sleep(1)
    reload(token)

def shot_cup_4(token):
    """
    Execute shot to Cup 4 (back right).
    Calibrated values: diagonal=9.2, rotation=0
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 9.2)
    time.sleep(1)
    rotate(token, 0)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

def shot_cup_5(token):
    """
    Execute shot to Cup 5 (front left).
    Calibrated values: diagonal=9, rotation=0.4
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 9)
    time.sleep(1)
    rotate(token, 0.4)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

def shot_cup_6(token):
    """
    Execute shot to Cup 6 (front right).
    Calibrated values: diagonal=8.6, rotation=0
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 8.6)
    time.sleep(1)
    rotate(token, 0)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

# =====================================================
# SPECIAL SHOTS
# =====================================================

def kill_shot(token):
    """
    Execute aggressive kill shot (high power, longer diagonal pull).
    Calibrated values: diagonal=14, rotation=0
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 14)
    time.sleep(1)
    rotate(token, 0)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

def trick_shot(token):
    """
    Execute trick shot with curved trajectory (double rotation).
    Calibrated values: diagonal=9, rotation=0.4 then 0
    """
    sling_grab(token)
    time.sleep(1)
    toggle(token, 255)
    time.sleep(1)
    diagonal(token, 9)
    time.sleep(1)
    rotate(token, 0.4)
    time.sleep(1)
    rotate(token, 0)
    time.sleep(1)
    toggle(token, 400)
    play_sound("shot.mp3")
    time.sleep(1)
    reload(token)

# =====================================================
# MAIN PROGRAM (for standalone testing)
# =====================================================

def main():
    """
    Command-line interface for manual robot control.
    Use this for testing and calibration.
    """
    token = None
    
    print("\n" + "="*50)
    print("RoboPong Robot Control - Manual Mode")
    print("="*50)
    print("Available commands:")
    print("  start, pickup_ball, shot_cup_1-6,")
    print("  kill_shot, trick_shot, emote, quit")
    print("="*50 + "\n")
    
    while True:
        command = input("Command: ").lower().strip()

        match command:
            case "start":
                token = log_on()
                start(token)
            case "pickup_ball":
                if token:
                    pickup_ball(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_1":
                if token:
                    shot_cup_1(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_2":
                if token:
                    shot_cup_2(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_3":
                if token:
                    shot_cup_3(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_4":
                if token:
                    shot_cup_4(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_5":
                if token:
                    shot_cup_5(token)
                else:
                    print("ERROR: Run 'start' first")
            case "shot_cup_6":
                if token:
                    shot_cup_6(token)
                else:
                    print("ERROR: Run 'start' first")
            case "kill_shot":
                if token:
                    kill_shot(token)
                else:
                    print("ERROR: Run 'start' first")
            case "trick_shot":
                if token:
                    trick_shot(token)
                else:
                    print("ERROR: Run 'start' first")
            case "emote":
                if token:
                    emote(token)
                else:
                    print("ERROR: Run 'start' first")
            case "quit":
                if token:
                    log_off(LOGIN_URL)
                print("Logging off... Goodbye!")
                return 0
            case _:
                print("Unknown command. Please try again.")

if __name__ == "__main__":
    main()