# RoboPong

**Voice-Controlled Autonomous Beer Pong Robot**

Autonomous robot system that plays Beer Pong using voice commands, computer vision (YOLO), and a CherryBot2 robotic arm with slingshot mechanism.

---

## Authors

**Colin Berendt, Yannik Holenstein, Robin Sutter**  
University of St.Gallen (HSG)
Course: Introduction to Robotics

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Voice Commands](#voice-commands)
8. [How It Works](#how-it-works)
9. [YOLO Model Training](#yolo-model-training)
10. [Development & Calibration](#development--calibration)
11. [Troubleshooting](#troubleshooting)

---

## Overview

RoboPong is an autonomous Beer Pong system that combines:
- **Voice Control** via Vosk speech recognition
- **Computer Vision** using YOLOv8 for cup detection
- **Robotic Arm Control** via CherryBot2 API
- **Real-time Video Streaming** from iPad camera

The system automatically detects which cup to target and executes precise shots using a slingshot mechanism controlled by a 6-axis robotic arm.

---

## System Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   iPad      │  HTTPS  │   Flask     │  HTTP   │   Voice     │
│   Camera    ├────────>│   Server    │<────────┤  Controller │
│             │         │   (YOLO)    │         │   (Vosk)    │
└─────────────┘         └──────┬──────┘         └──────┬──────┘
                               │                       │
                               │ Detections            │ Commands
                               │                       │
                               v                       v
                        ┌──────────────────────────────┐
                        │    Robot Integration         │
                        │   (robo_pong.py API)         │
                        └──────────────────────────────┘
                                      │
                                      │ HTTPS
                                      v
                        ┌──────────────────────────────┐
                        │   CherryBot2 Robot Arm       │
                        │          (HSG Lab)           │
                        └──────────────────────────────┘
```

---

## Features

- **Voice-Activated Control**: Natural language commands with "robot" wake-word
- **Automatic Target Detection**: YOLO identifies cups and selects highest-confidence target
- **Precision Shots**: Calibrated trajectories for each of the 6 cup positions
- **Special Shots**: Killshot (high power) and Trickshot (bounces on the table)
- **Real-Time Streaming**: iPad camera feeds live video to Flask server
- **Automatic Reload**: Robot autonomously picks up new balls after each shot
- **Sound Effects**: Audio feedback for actions (shot, pickup, etc.)

---

## Project Structure

```
RoboPong/
│
├── robo_pong.py              # Core robot API (movement, shots, sequences)
├── calibrate_cups.py         # Calibration tool for shot trajectories
│
├── src/
│   ├── web/
│   │   ├── server.py         # Flask server (YOLO inference + streaming)
│   │   └── templates/
│   │       ├── index.html    # iPad camera interface
│   │       └── view.html     # Detection viewer
│   │
│   ├── voice/
│   │   ├── controller.py     # Voice recognition & command processing
│   │   └── robot_integration.py  # Bridge to robot API
│   │
│   ├── utils/
│   │   └── frame_capture.py  # Dataset capture tool
│   │
│   ├── models/
│   │   ├── cup_detection.pt  # YOLOv8 trained model
│   │   └── vosk-en-us/       # Vosk speech recognition model
│   │
│   ├── certs/                # SSL certificates for HTTPS
│   └── requirements.txt      # Python dependencies
│
├── datasets/
│   ├── labeled_set/          # YOLO training dataset
│   │   ├── train/
│   │   ├── valid/
│   │   ├── test/
│   │   └── data.yaml
│   └── stream_captures/      # Raw captured frames
│
├── sounds/                   # Audio effects
│   ├── shot.mp3
│   ├── pick_up.mp3
│   ├── log_on.mp3
│   └── ...
│
└── README.md                 # This file
```

---

## Installation

### Prerequisites

- Python 3.8+
- macOS (for sound effects) or Linux
- iPad with Safari browser (for camera streaming)
- Access to CherryBot2 robot (HSG Lab)

### 1. Clone Repository

```bash
cd "University - HSG/RoboPong"
```

### 2. Install Dependencies

```bash
pip install -r src/requirements.txt
```

**Key Dependencies:**
- `ultralytics` - YOLOv8 for object detection
- `flask` - Web server for streaming
- `vosk` - Offline speech recognition
- `sounddevice` - Audio input for voice commands
- `opencv-python` - Video processing
- `pygame` - Sound effects playback

### 3. Download Vosk Model

```bash
# Download and extract to src/models/
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d src/models/
mv src/models/vosk-model-small-en-us-0.15 src/models/vosk-en-us
```

### 4. Setup SSL Certificates (for iPad Camera)

```bash
# Generate self-signed certificate for your local IP
# Replace 172.20.10.3 with your laptop's IP
openssl req -x509 -newkey rsa:4096 -nodes \
  -out src/certs/172.20.10.3.pem \
  -keyout src/certs/172.20.10.3-key.pem \
  -days 365 \
  -subj "/CN=172.20.10.3"
```

---

## Usage

### Quick Start

**3-Terminal Workflow:**

**Terminal 1: Flask Server (YOLO Detection)**
```bash
cd "/Users/robin/Datenbank/University - HSG/RoboPong"
python src/web/server.py
```

**Terminal 2: Voice Controller**
```bash
cd "/Users/robin/Datenbank/University - HSG/RoboPong"
python src/voice/controller.py
```

**Terminal 3: iPad Camera**
1. Connect iPad to same WiFi as laptop
2. Open Safari on iPad
3. Navigate to `https://<LAPTOP_IP>:5001/`
4. Accept SSL certificate warning
5. Allow camera access
6. Point camera at cups

**Laptop Browser (Optional Viewer):**
```
https://<LAPTOP_IP>:5001/view
```

### Complete Workflow

1. **Start Flask Server** (Terminal 1)
   - Loads YOLO model
   - Starts HTTPS server on port 5001
   - Waits for iPad camera stream

2. **Start Voice Controller** (Terminal 2)
   - Loads Vosk speech model
   - Begins listening for commands
   - Note: Don't initialize robot yet!

3. **Connect iPad Camera**
   - Open `https://<IP>:5001/` on iPad
   - Grant camera permissions
   - Aim at Beer Pong cups
   - Check `/view` endpoint to verify detection

4. **Initialize Robot**
   - Say: **"robot go"**
   - Robot will log in, pick up ball, and load slingshot (~30 sec)

5. **Execute Shots**
   - Say: **"robot shoot"** (normal shot to detected cup)
   - Say: **"robot killshot"** (high-power shot)
   - Say: **"robot trickshot"** (curved trajectory)

6. **Shutdown**
   - Say: **"robot terminate"**
   - Or press Ctrl+C in terminal

---

## Voice Commands

All commands require **"robot"** wake-word prefix:

| Command | Action | Requires Init |
|---------|--------|---------------|
| `robot go` | Initialize robot (log in, pickup ball, load slingshot) | No |
| `robot shoot` | Execute shot to auto-detected cup | Yes |
| `robot killshot` | Execute high-power aggressive shot | Yes |
| `robot trickshot` | Execute a bounce on the table before hitting the cup | Yes |
| `robot goodgame` | Verbal acknowledgment (no action) | No |
| `robot terminate` | Shutdown robot and log off | Yes |

**Example Session:**
```
User: "robot go"
    -> Robot initializes (~30 seconds)
User: "robot shoot"
    -> Detects cup 3, executes shot, auto-reloads
User: "robot shoot"
    -> Detects cup 1, executes shot, auto-reloads
User: "robot killshot"
    -> High-power shot
User: "robot terminate"
    -> Logs off and exits
```

---

## How It Works

### 1. Computer Vision (YOLO)

- **Model**: YOLOv8n trained on custom dataset
- **Classes**: 6 cup positions (cup_1 to cup_6)
- **Training**: 88 labeled images, 150 epochs
- **Inference**: Real-time on iPad camera stream (conf=0.25)
- **Output**: Bounding boxes + confidence scores

### 2. Voice Recognition (Vosk)

- **Model**: vosk-model-small-en-us (offline)
- **Grammar**: Restricted vocabulary for accuracy
- **Wake-word**: "robot" required for all commands
- **Processing**: Real-time audio stream analysis

### 3. Robot Control

**Hardware**: CherryBot2 6-axis robotic arm  
**API**: RESTful HTTPS API (HSG Lab)  
**Mechanism**: Slingshot-style ball launcher  

**Shot Sequence**:
1. `sling_grab()` - Position gripper at slingshot
2. `toggle(255)` - Close gripper (grip slingshot)
3. `diagonal(X)` - Pull back slingshot (calibrated distance)
4. `rotate(Y)` - Adjust horizontal aim (calibrated angle)
5. `toggle(400)` - Release gripper (launch ball)
6. `reload()` - Return to init, pickup new ball, load slingshot

**Calibrated Trajectory Values**:
- **Cup 1** (back left): diagonal=12, rotation=-0.6
- **Cup 2** (back center-left): diagonal=9.3, rotation=0
- **Cup 3** (back center-right): diagonal=9.9, rotation=0.5
- **Cup 4** (back right): diagonal=9.2, rotation=0
- **Cup 5** (front left): diagonal=9, rotation=0.4
- **Cup 6** (front right): diagonal=8.6, rotation=0

---

## YOLO Model Training

### Dataset Creation

```bash
# 1. Start Flask server
python src/web/server.py

# 2. Capture frames (in separate terminal)
python src/utils/frame_capture.py
# Press 'q' when done
```

### Labeling

Use [Roboflow](https://roboflow.com) or [LabelImg](https://github.com/heartexlabs/labelImg):
1. Upload frames to labeling tool
2. Draw bounding boxes around cups
3. Assign class labels (cup_1 to cup_6)
4. Export in YOLO format

### Training

```bash
# Train YOLOv8 model on Apple M4 GPU
cd "/Users/robin/Datenbank/University - HSG/RoboPong"

yolo train \
  data=datasets/labeled_set/data.yaml \
  model=yolov8n.pt \
  epochs=150 \
  imgsz=640 \
  device=mps \
  patience=30 \
  batch=16
```

**Training Results**:
- Located in: `runs/detect/train/`
- Best model: `runs/detect/train/weights/best.pt`
- Copy to: `src/models/cup_detection.pt`

---

## Development & Calibration

### Manual Robot Control

```bash
python robo_pong.py
```

**Commands**:
- `start` - Initialize robot
- `shot_cup_1` to `shot_cup_6` - Test individual cup shots
- `kill_shot` - Test killshot
- `trick_shot` - Test trickshot
- `quit` - Exit

### Shot Calibration Tool

```bash
python calibrate_cups.py
```

**Usage**:
```
Command: start
    -> Robot initializes
Command: shot 9.5 0.3
    -> Test diagonal=9.5, rotation=0.3
    -> Adjust values until accurate
```

Update calibrated values in `robo_pong.py` shot functions.

### View YOLO Detections

```bash
# Start Flask server
python src/web/server.py

# Open in browser
open https://172.20.10.3:5001/view
```

### API Testing

```bash
# Test detections endpoint
curl http://127.0.0.1:5001/detections | jq
```

---

## Troubleshooting

### Voice Recognition Issues
**Problem**: No audio input detected  
**Solution**: 
```bash
# Check available microphones
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### YOLO Detection Issues

**Problem**: No cups detected  
**Solution**:
- Ensure Flask server is running
- Check `/view` endpoint to see what camera sees
- Improve lighting conditions
- Retrain model with more varied data

**Problem**: Low confidence scores  
**Solution**:
- Lower confidence threshold in `server.py`: `conf=0.25` -> `conf=0.15`
- Retrain with more augmented data

### Robot Connection Issues

**Problem**: "Token not received"  
**Solution**: Check HSG lab network connection and credentials in `robo_pong.py`

**Problem**: "Robot not initialized"  
**Solution**: Say "robot go" before any shot commands

### iPad Camera Issues

**Problem**: Camera blocked or denied  
**Solution**:
- Use Safari browser (not Chrome)
- Accept SSL certificate warning
- Grant camera permissions in iOS settings

**Problem**: No stream visible  
**Solution**: 
- Verify laptop IP address is correct
- Check firewall settings
- Ensure both devices on same WiFi

### Flask Server Issues

**Problem**: "SSL certificates not found"  
**Solution**: Generate certificates (see Installation section) or run without HTTPS (camera may not work)

**Problem**: "Model not found"  
**Solution**: Verify `src/models/cup_detection.pt` exists

---

## Technical Notes

### Performance

- **YOLO Inference**: ~30-50 FPS on Apple M4
- **Voice Recognition**: Real-time (<100ms latency)
- **Shot Execution**: ~40 seconds (including reload)

### Accuracy

- **Cup Detection**: ~95% accuracy under good lighting
- **Shot Success Rate**: ~70-80% (depends on calibration)

### Limitations

- Requires consistent lighting conditions
- Cup positions must be visible to camera
- Robot must be calibrated for specific table setup

---

## Future Improvements

- [ ] Multi-camera support for better detection
- [ ] Adaptive calibration (learn from misses)
- [ ] Shot success tracking and statistics
- [ ] Mobile app interface
- [ ] Autonomous opponent tracking

---

## License

Educational project for University of St.Gallen.  
All rights reserved by authors.

---

## Contact

For questions or collaboration:

- **Colin Berendt**: colinwai-loen.berendt@student.unisg.ch
- **Yannik Holenstein**: yannik.holenstein@student.unisg.ch
- **Robin Sutter**: robin.sutter2@student.unisg.ch

---

**Last Updated**: November 2025  
**Version**: 1.0.0
