"""
RoboPong Flask Server
=====================
Handles video streaming from iPad, performs real-time YOLO cup detection,
and provides API endpoints for detection data.

Authors: Colin Berendt, Yannik Holenstein, Robin Sutter
University of St.Gallen (HSG) - Interactions Lab
"""

from flask import Flask, render_template, request, Response, jsonify
import cv2
import numpy as np
import base64
import os
from ultralytics import YOLO

# =====================================================
# MODEL LOADING
# =====================================================

# Try multiple paths for flexible execution from different directories
model_paths = [
    'src/models/cup_detection.pt',
    'models/cup_detection.pt',
    os.path.join(os.path.dirname(__file__), '..', 'models', 'cup_detection.pt')
]

model_path = None
for path in model_paths:
    if os.path.exists(path):
        model_path = path
        break

if not model_path:
    raise FileNotFoundError("Cup detection model not found. Expected at: src/models/cup_detection.pt")

print(f"Loading YOLO model from: {model_path}")
model = YOLO(model_path)

# =====================================================
# FLASK APP SETUP
# =====================================================

app = Flask(__name__)

# Global variables to store latest frames and detections
latest_frame = None              # Raw frame from iPad camera
latest_processed_frame = None    # Frame with YOLO bounding boxes
latest_detections = []           # List of detected cups with confidence scores

# =====================================================
# WEB ROUTES
# =====================================================

@app.route('/')
def index():
    """Serve iPad camera streaming page (sends frames to server)."""
    return render_template('index.html')

@app.route('/view')
def view():
    """Serve laptop viewing page (displays YOLO detection stream)."""
    return render_template('view.html')

@app.route('/stream', methods=['POST'])
def stream():
    """
    Receive frame from iPad, run YOLO inference, store results.
    Called continuously by iPad camera (index.html).
    
    Expected JSON: {"frame": "data:image/jpeg;base64,<base64_data>"}
    Returns: "OK" or "Error"
    """
    global latest_frame, latest_processed_frame, latest_detections
    try:
        # Decode base64 image from request
        data_url = request.json['frame']
        encoded_data = data_url.split(',')[1]
        img_data = base64.b64decode(encoded_data)
        np_data = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

        # Store raw frame (without YOLO annotations)
        latest_frame = frame.copy()

        # Run YOLO inference (conf=0.25 for better detection sensitivity)
        results = model(frame, conf=0.25, verbose=False)
        processed_frame = results[0].plot()  # Draw bounding boxes

        # Store processed frame (with YOLO annotations)
        latest_processed_frame = processed_frame
        
        # Extract and store detection data for /detections endpoint
        detections = []
        num_boxes = len(results[0].boxes)
        print(f"Detected {num_boxes} cups")
        
        for box in results[0].boxes:
            detection = {
                "class_id": int(box.cls[0]),        # 0-5 (cup_1 to cup_6)
                "confidence": float(box.conf[0]),   # Confidence score
                "bbox": {
                    "x1": float(box.xyxy[0][0]),
                    "y1": float(box.xyxy[0][1]),
                    "x2": float(box.xyxy[0][2]),
                    "y2": float(box.xyxy[0][3])
                },
                "center": {
                    "x": float((box.xyxy[0][0] + box.xyxy[0][2]) / 2),
                    "y": float((box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                }
            }
            detections.append(detection)
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        latest_detections = detections

        return "OK"
    except Exception as e:
        print("Error processing frame:", e)
        return "Error", 500

# =====================================================
# VIDEO STREAMING ROUTES
# =====================================================

@app.route('/raw_stream')
def raw_stream():
    """
    Stream raw camera feed without YOLO annotations.
    Returns MJPEG stream for real-time viewing.
    """
    def generate():
        global latest_frame
        while True:
            if latest_frame is not None:
                # Encode frame as JPEG
                _, jpeg = cv2.imencode('.jpg', latest_frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed')
def video_feed():
    """
    Stream camera feed with YOLO detection bounding boxes.
    Returns MJPEG stream for real-time viewing.
    Used by /view page.
    """
    def generate():
        global latest_processed_frame
        while True:
            if latest_processed_frame is not None:
                # Encode frame as JPEG
                _, jpeg = cv2.imencode('.jpg', latest_processed_frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# =====================================================
# API ENDPOINTS
# =====================================================

@app.route('/detections', methods=['GET'])
def get_detections():
    """
    Get current YOLO detections in JSON format.
    
    Used by voice controller to determine target cup.
    Returns list of detected cups sorted by confidence (highest first).
    
    Returns:
        JSON: {
            "status": "ok",
            "num_detections": int,
            "detections": [
                {
                    "class_id": 0-5 (cup_1 to cup_6),
                    "confidence": 0.0-1.0,
                    "bbox": {"x1": float, "y1": float, "x2": float, "y2": float},
                    "center": {"x": float, "y": float}
                },
                ...
            ]
        }
    """
    global latest_detections, latest_processed_frame
    
    if latest_processed_frame is None:
        return jsonify({"error": "No frame processed yet", "detections": []})
    
    return jsonify({
        "status": "ok",
        "num_detections": len(latest_detections),
        "detections": latest_detections
    })
# =====================================================
# SERVER STARTUP
# =====================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("RoboPong Flask Server - YOLO Cup Detection")
    print("="*60)
    print("\nEndpoints:")
    print("  iPad:   https://<Laptop-IP>:5001/")
    print("          (Camera stream sender)")
    print("\n  Laptop: https://<Laptop-IP>:5001/view")
    print("          (YOLO detection viewer)")
    print("\n  API:    http://127.0.0.1:5001/detections")
    print("          (JSON detection data)")
    print("\nStreams:")
    print("  /raw_stream  - Raw camera (no annotations)")
    print("  /video_feed  - YOLO stream (with bounding boxes)")
    print("="*60 + "\n")

    # Try to find SSL certificates for HTTPS (required for iPad camera access)
    cert_paths = [
        ('src/certs/172.20.10.3.pem', 'src/certs/172.20.10.3-key.pem'),
        ('certs/172.20.10.3.pem', 'certs/172.20.10.3-key.pem'),
    ]
    
    ssl_context = None
    for cert, key in cert_paths:
        if os.path.exists(cert) and os.path.exists(key):
            ssl_context = (cert, key)
            print(f"SSL enabled: Using {cert}")
            break
    
    if ssl_context:
        app.run(host='0.0.0.0', port=5001, ssl_context=ssl_context, debug=False)
    else:
        print("WARNING: SSL certificates not found, running without HTTPS")
        print("         iPad camera may not work without HTTPS")
        app.run(host='0.0.0.0', port=5001, debug=False)