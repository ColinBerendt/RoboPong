"""
RoboPong Frame Capture Utility
===============================
Captures frames from Flask server's raw stream for dataset creation.
Saves images at regular intervals for YOLO training data collection.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

import cv2
import time
import os

# =====================================================
# CONFIGURATION
# =====================================================

STREAM_URL = "https://172.20.10.3:5001/raw_stream"  # Change to your laptop's IP
SAVE_DIR = "datasets/stream_captures"
INTERVAL = 4  # Seconds between captures

# =====================================================
# SETUP
# =====================================================

# Enable OpenCV optimizations
cv2.setUseOptimized(True)

# Create output directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)

# =====================================================
# MAIN CAPTURE LOOP
# =====================================================

print("\n" + "="*60)
print("RoboPong Frame Capture Tool")
print("="*60)
print(f"Stream URL: {STREAM_URL}")
print(f"Save Directory: {SAVE_DIR}")
print(f"Capture Interval: {INTERVAL} seconds")
print("="*60 + "\n")

print("Connecting to stream...")
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("ERROR: Could not open stream.")
    print("       Check if Flask server is running and IP address is correct.")
    exit()

print("Connected! Press 'q' to quit.\n")

counter = 0
last_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("WARNING: No frame received - check connection.")
        time.sleep(1)
        continue

    # Display live feed
    cv2.imshow("Live Stream Capture", frame)

    # Auto-save at specified interval
    if time.time() - last_time >= INTERVAL:
        filename = f"{SAVE_DIR}/frame_{counter:04d}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Saved: {filename}")
        
        # Play sound effect (macOS only)
        os.system('afplay /System/Library/Sounds/Hero.aiff &')
        
        counter += 1
        last_time = time.time()

    # Check for quit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

print(f"\n" + "="*60)
print(f"Capture Complete: {counter} images saved to '{SAVE_DIR}'")
print("="*60)