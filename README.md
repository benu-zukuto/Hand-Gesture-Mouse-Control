# Hand Gesture Recognition & Virtual Mouse Control

A Python application using OpenCV, MediaPipe (v1.0+ Tasks API), and PyAutoGUI to detect hand gestures from a webcam in real-time and control your computer's mouse.

## Features
- **Real-time hand landmark detection** (21 keypoints) using the new MediaPipe Tasks API.
- **Gesture classification** based on relative joint coordinates.
- **Virtual Mouse Control** using smooth cursor mapping, click hysteresis, and gesture triggers.
- **Visual Debug UI Overlay** displaying real-time FPS, detected gesture, current mouse action, and color-coded pinch distance bars.
- **Mouse toggle safety switch** to easily enable/disable mouse control using the keyboard.

## Supported Gestures & Mouse Actions

| Gesture / Input | Mouse Action | How to Trigger |
|-----------------|--------------|----------------|
| ☝️ **Index finger tip** | **Cursor Movement** | Move index finger tip around camera frame |
| 🤏 **Thumb + Index pinch** | **Left Click** | Bring thumb and index tip close together (<0.08) |
| 🤏 **Thumb + Middle pinch** | **Right Click** | Bring thumb and middle tip close together (<0.08) |
| ✌️ **Peace Sign / Victory** | **Scrolling** | Move hand up or down with index + middle fingers up |
| ✊ **Fist** | **Double Click** | Close all fingers into a fist |
| ✋ **Open Palm** | *(None / Idle)* | All 5 fingers extended |
| 👆 **Pointing** | *(None / Idle)* | Only index finger extended |

## Setup

1. **Set up Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Required Assets**:
   The app automatically downloads the MediaPipe model asset file `hand_landmarker.task` to the root folder. If it is missing, you can download it from [Google's Storage API](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task).

## How to Run

Make sure your virtual environment is active:
```bash
python main.py
```

## Controls

- Press **`m`** to toggle mouse control ON/OFF.
- Press **`q`** to quit the application.
- **Safety Failsafe**: Move your real mouse to any corner of the screen to trigger PyAutoGUI's failsafe and abort execution.
