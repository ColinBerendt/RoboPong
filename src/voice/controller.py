"""
RoboPong Voice Controller
=========================
Voice-controlled robot interface using Vosk speech recognition.
Recognizes commands, detects target cups via YOLO, and executes shots.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

import queue
import sounddevice as sd
import json
import time
import requests
from vosk import Model, KaldiRecognizer
from robot_integration import robot

# =====================================================
# CONFIGURATION
# =====================================================

VOSK_MODEL_PATH = "src/models/vosk-en-us"
SAMPLE_RATE = 16000

# Grammar restricts recognition to these words only (faster and more accurate)
# All commands must start with "robot" wake-word
GRAMMAR = '["robot", "go", "shoot", "killshot", "trickshot", "goodgame", "good", "game", "terminate"]'

# =====================================================
# AUDIO SETUP
# =====================================================

q = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    """Callback for audio input stream (pushes audio data to queue)."""
    if status:
        print(status)
    q.put(bytes(indata))

# =====================================================
# CUP DETECTION
# =====================================================

def detect_target_cup():
    """
    Get target cup from YOLO detection via Flask server.
    
    Queries the Flask server's /detections endpoint and returns the cup
    with the highest confidence score. Falls back to cup 2/3 on errors.
    
    Returns:
        int: Cup number (1-6) to target
    """
    print("Getting detections from Flask server...")
    try:
        response = requests.get('http://127.0.0.1:5001/detections', timeout=2)
        
        if response.status_code != 200:
            print(f"WARNING: Failed to get detections (status {response.status_code})")
            return 2  # Fallback
        
        data = response.json()
        detections = data.get('detections', [])
        
        if not detections:
            print("WARNING: No cups detected in frame")
            return 2  # Fallback
        
        # Get detection with highest confidence (already sorted by Flask server)
        best_detection = detections[0]
        confidence = best_detection['confidence']
        class_id = best_detection['class_id']
        
        # Map class_id (0-5) to cup_number (1-6)
        cup_number = class_id + 1
        
        print(f"Detection: {len(detections)} cups found")
        print(f"Target: Cup {cup_number} (class_id={class_id}, confidence={confidence:.2f})")
        
        return cup_number
        
    except requests.exceptions.Timeout:
        print("WARNING: Timeout connecting to Flask server")
        return 3  # Fallback
    except requests.exceptions.ConnectionError:
        print("WARNING: Could not connect to Flask server. Is it running?")
        return 3  # Fallback
    except Exception as e:
        print(f"WARNING: Error detecting cup: {e}")
        return 3  # Fallback

# =====================================================
# MAIN PROGRAM
# =====================================================

def main():
    """
    Main voice control loop.
    
    Workflow:
    1. Initialize Vosk speech recognition
    2. Listen for voice commands with "robot" wake-word
    3. Process commands and control robot accordingly
    4. Auto-detect target cups via YOLO for shots
    """
    print("\n" + "="*60)
    print("RoboPong Voice Control - Starting...")
    print("="*60)
    print(f"VOSK Model: {VOSK_MODEL_PATH}")
    print("="*60 + "\n")
    
    # Load Vosk model for speech recognition
    model = Model(VOSK_MODEL_PATH)
    
    # Create recognizer with grammar (restricts to defined words only)
    if GRAMMAR:
        rec = KaldiRecognizer(model, SAMPLE_RATE, GRAMMAR)
    else:
        rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(True)

    ready_mode = False  # Tracks whether robot has been initialized

    # Start audio stream and begin listening
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("\n" + "="*60)
        print("RoboPong Voice Control - Ready")
        print("="*60)
        print("Available Commands (must start with 'robot'):")
        print("  'robot go'         - Initialize robot")
        print("  'robot shoot'      - Execute shot to detected cup")
        print("  'robot killshot'   - Execute aggressive killshot")
        print("  'robot trickshot'  - Execute trick shot")
        print("  'robot goodgame'   - Celebration (no action)")
        print("  'robot terminate'  - Shutdown robot\n")
        print("NOTE: Target cup is automatically detected via YOLO.")
        print("      Make sure Flask server is running!")
        print("="*60 + "\n")
        
        while True:
            # Get audio data from queue
            data = q.get()
            
            # Process audio chunk through Vosk
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                if not text:
                    continue
                
                print(f"\n>>> Heard: '{text}'")

                # Wake-word check: all commands must contain "robot"
                if "robot" not in text:
                    print("    -> Ignored (no 'robot' wake-word)")
                    continue
                
                print("    -> Processing command...")
                
                # =====================================
                # COMMAND: TERMINATE
                # =====================================
                if "robot terminate" in text:
                    print("Shutting down robot...")
                    robot.shutdown()
                    print("Robot terminated. Goodbye!")
                    break
                
                # =====================================
                # COMMAND: GOOD GAME (celebration)
                # =====================================
                elif "robot goodgame" in text or ("robot" in text and "good" in text and "game" in text):
                    print("GG! Well played!")
                    continue
                
                # =====================================
                # COMMAND: GO (initialize robot)
                # =====================================
                elif "robot go" in text:
                    print("=== INITIALIZING ROBOT ===")
                    result = robot.initialize()
                    if result:
                        ready_mode = True
                        print("SUCCESS: Robot initialized and ready to shoot!")
                    else:
                        print("FAILED: Robot initialization failed!")
                        ready_mode = False
                
                # =====================================
                # COMMAND: TRICKSHOT
                # =====================================
                elif "robot trickshot" in text:
                    if not ready_mode:
                        print("ERROR: Robot not initialized. Say 'robot go' first.")
                        continue
                    print("Executing trickshot...")
                    robot.execute_trickshot()
                
                # =====================================
                # COMMAND: KILLSHOT
                # =====================================
                elif "robot killshot" in text:
                    if not ready_mode:
                        print("ERROR: Robot not initialized. Say 'robot go' first.")
                        continue
                    target_cup = detect_target_cup()
                    print(f"Executing killshot to cup {target_cup}...")
                    robot.execute_shot(target_cup, "killshot")
                
                # =====================================
                # COMMAND: SHOOT
                # =====================================
                elif "robot shoot" in text:
                    if not ready_mode:
                        print("ERROR: Robot not initialized. Say 'robot go' first.")
                        continue
                    
                    # Auto-detect target cup via YOLO
                    target_cup = detect_target_cup()
                    print(f"Executing shot to cup {target_cup}...")
                    robot.execute_shot(target_cup, "normal")

if __name__ == "__main__":
    main()

