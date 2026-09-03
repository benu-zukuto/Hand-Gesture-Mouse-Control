```markdown
# Hand Gesture Recognition, Virtual Mouse & System Control

A real-time computer vision application using OpenCV, MediaPipe Tasks API (v1.0+), and PyAutoGUI to track hand landmarks from a local webcam or phone IP camera feed, providing single-hand mouse control and two-hand system adjustments (volume and brightness)[cite: 2, 5].

---

## Features

- **Low-Latency Threaded Capture**: Bypasses OpenCV's internal network stream buffer using a non-blocking frame consumer thread to prevent video lag[cite: 2].
- **Rotation- & Scale-Invariant Gestures**: Hand geometries are calculated relative to palm scale and wrist position, maintaining tracking stability regardless of camera distance or hand orientation[cite: 1, 5].
- **Dynamic Physics Scrolling**: Thumbs Up and Thumbs Down gestures feature an analog throttle curve and twist velocity tracking for smooth crawling or high-speed scrolling without jitter.
- **Safe Neutral Resting State**: Holding the thumb centered while fingers are curled pauses scrolling without triggering phantom pinch clicks.
- **Two-Hand Control Clutch**: Pinching both hands simultaneously switches into system adjustment mode—adjust volume horizontally or screen brightness vertically.
- **Corner Crash Protection**: Clamps cursor coordinates within safety margins and handles desktop hot corners to avoid unexpected OS traps.

---

## Gesture Reference

### Single-Hand Mode (Mouse & Scrolling)

| Gesture | Action | Description |
| :--- | :--- | :--- |
| **Index Pointing** | **Cursor Movement** | Moves cursor smoothly across screen dimensions[cite: 2, 5]. |
| **Thumb + Index Pinch** | **Left Click** | Closes thumb and index tips together (<0.07 norm distance)[cite: 2, 5]. |
| **Thumb + Middle Pinch** | **Right Click** | Closes thumb and middle tips together (<0.07 norm distance)[cite: 2, 5]. |
| **Thumbs Up** | **Auto Scroll Up** | Tilt thumb upward with fingers curled. Angle controls speed. |
| **Thumbs Down** | **Auto Scroll Down** | Tilt thumb downward with fingers curled. Angle controls speed. |
| **Thumb Neutral** | **Scroll Idle** | Thumb in center with fingers curled. Pauses scrolling cleanly. |

### Two-Hand Mode (System Adjustments)

Automatically activates when two hands are detected in the frame. Cursor movement freezes to allow control adjustments.

| Gesture | Action | Description |
| :--- | :--- | :--- |
| **Both Pinch (Thumb + Index)** | **Adjustment Clutch** | Engages control mode. Release pinch to lock levels. |
| **Spread / Contract Horizontally** | **Volume Up / Down** | Move pinched hands apart horizontally to raise volume; bring together to lower. |
| **Spread / Contract Vertically** | **Brightness Up / Down** | Move pinched hands apart vertically to increase brightness; bring together to dim. |

---

## Prerequisites (Linux)

To support direct system control for volume and screen brightness, install the required audio and brightness utilities:

```bash
sudo apt update
sudo apt install brightnessctl pulseaudio-utils

```

Ensure your user account has permission to adjust brightness via `brightnessctl`:

```bash
sudo usermod -aG video $USER

```

---

## Setup & Installation

1. **Clone the repository & navigate to project directory**:
```bash
git clone <repository-url>
cd Hand-Gesture

```


2. **Create and activate a virtual environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate

```


3. **Install dependencies**:
```bash
pip install opencv-python mediapipe pyautogui

```


4. **MediaPipe Model File**:
Ensure `hand_landmarker.task` is located in the root project directory. If missing, download it via:


```bash
wget -q [https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task)

```



---

## Configuration & Running

1. Open `main.py` and verify your camera stream endpoint:
* For an **IP Webcam stream**: set `stream_url = "http://<PHONE_IP>:8080/video"`.
* For a **local USB webcam**: set `stream_url = 0`.


2. Launch the application:
```bash
python3 main.py

```



---

## Keyboard Shortcuts

* **`m`**: Toggle mouse and system control ON/OFF.


* **`q`**: Exit application and release video stream.



```

```
