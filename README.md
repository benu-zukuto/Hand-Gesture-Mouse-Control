# Hand Gesture Mouse & System Control

A real-time AI-powered virtual mouse and system controller using OpenCV, MediaPipe Tasks API, and PyAutoGUI. The system tracks 21 hand landmarks to translate hand postures into cursor movement, clicks, scrolling, and two-handed volume and brightness adjustments.

---

## Features

* **Single-Hand Mouse Navigation:**
* Cursor tracking via index finger tip with moving-average coordinate smoothing.


* Pinch Left Click (Thumb + Index tip) and Pinch Right Click (Thumb + Middle tip).


* Proportional, velocity-boosted vertical scrolling via Thumbs Up / Thumbs Down gestures.




* **Two-Hand System Control:**
* Pinch both hands and move horizontally (Left–Right) to adjust system volume.


* Pinch both hands and move vertically (North–South) to adjust display brightness.


* Axis-lock engine to prevent diagonal input cross-talk.




* **Low-Latency Streaming:**
* Background thread frame buffer clearance (`ThreadedCamera`) to prevent buffer lag.


* Automatic V4L2 device discovery favoring external USB action cameras.


* Support for local network IP camera streams (Android IP Webcam / RTSP).





---

## Gesture Cheat Sheet

| Mode | Gesture | Action |
| --- | --- | --- |
| **1-Hand** | Pointing (Index finger extended) | Move mouse cursor

 |
| **1-Hand** | Pinch Thumb + Index tip | Left click

 |
| **1-Hand** | Pinch Thumb + Middle tip | Right click

 |
| **1-Hand** | Thumbs Up (Fingers curled) | Scroll Up (speed scales with tilt)

 |
| **1-Hand** | Thumbs Down (Fingers curled) | Scroll Down (speed scales with tilt)

 |
| **2-Hand** | Pinch both hands & move sideways | Volume Control (`pactl`)

 |
| **2-Hand** | Pinch both hands & move up/down | Brightness Control (`brightnessctl`)

 |

**Keyboard Controls:**

* `m`: Toggle mouse and system control ON / OFF.


* `q`: Quit application.



---

## Installation

### 1. System Dependencies (Linux)

Install the required system utilities for display, audio, and camera access:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv brightnessctl pulseaudio-utils libgl1 libglib2.0-0

```

Add your user to the `video` group so you can read USB camera devices without `sudo`:

```bash
sudo usermod -aG video $USER

```

*(Log out and log back in for group permissions to apply.)*

---

### 2. Clone the Repository

```bash
git clone https://github.com/benu-zukuto/Hand-Gesture-Mouse-Control.git
cd Hand-Gesture-Mouse-Control

```

---

### 3. Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

```

Install Python packages:

```bash
pip install --upgrade pip
pip install opencv-python mediapipe pyautogui

```

---

### 4. Download MediaPipe Model Asset

Download the pre-trained MediaPipe Hand Landmarker task model into both folders:

```bash
# Download the model
wget -q -O hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

# Copy into both Webcam and IP-cam directories
cp hand_landmarker.task Webcam/
cp hand_landmarker.task IP-cam/

```

---

## How to Run

### Method 1: Webcam / USB Camera (Recommended)

Navigate to the `Webcam` folder:

```bash
cd Webcam

```

Run using automatic camera detection:

```bash
python3 main.py

```

The script inspects `/sys/class/video4linux` and automatically chooses external action cameras over built-in webcams. If you want to specify a particular camera index or device node manually:

```bash
# Specify index 0
python3 main.py --cam 0

# Specify device node directly
python3 main.py --cam /dev/video2

```

---

### Method 2: IP Camera (Mobile Stream)

1. Install an IP streaming app on your smartphone (e.g., **IP Webcam** from Google Play).
2. Connect your computer and phone to the same Wi-Fi network (or mobile hotspot).
3. Start the stream in the app (note down the IPv4 address shown, e.g., `[http://192.168.1.15:8080/video](http://192.168.1.15:8080/video)`).
4. Open `IP-cam/main.py` and update the `stream_url`:

```python
stream_url = "http://<YOUR_PHONE_IP>:8080/video"

```

5. Navigate to the `IP-cam` folder and launch the program:

```bash
cd ../IP-cam
python3 main.py

```

---

## How It Works

### 1. MediaPipe Tasks Hand Landmarker

The application uses Google MediaPipe's Hand Landmarker model running in `VIDEO` mode. Monotonically increasing millisecond timestamps are fed alongside each frame to enable real-time temporal tracking across up to 2 simultaneous hands. The model outputs 21 3D landmarks ($X, Y, Z$) normalized between 0.0 and 1.0.

```
         8   12  16  20  (Fingertips)
         |   |   |   |
         7   11  15  19
         |   |   |   |
  4      6   10  14  18
   \     |   |   |   |
    3    5---9---13--17  (MCP Knuckles)
     \  /
      2/
      |
      1
      |
      0 (Wrist)

```

### 2. Rotation & Scale Invariant Posture Recognition

* **Scale Invariance:** All gesture thresholds are normalized using the physical distance between Wrist (`0`) and Middle MCP knuckle (`9`). This guarantees consistent recognition regardless of how close or far your hand is from the lens.


* **Rotation Invariance:** Finger extension is determined by comparing each fingertip's Euclidean distance from the wrist against its corresponding PIP knuckle's distance from the wrist. If the tip is closer to the wrist than the PIP joint, the finger is classified as curled, regardless of the hand's tilt angle in 3D space.



### 3. Coordinate Mapping & Jitter Suppression

* **Screen Margin Mapping:** The center 70% of the camera frame maps to 100% of the screen coordinates to allow comfortable edge-to-edge navigation without hand strain.


* **Moving Average Filter:** Cursor coordinates pass through a sliding historical window to eliminate tremor and sensor jitter while retaining fast response times.



### 4. Non-Blocking Dual-Axis System Control

When two hands are in view and both index fingers pinch their respective thumbs, the system computes the distance delta ($\Delta X$ and $\Delta Y$) between both pinch midpoints. The dominant movement axis is locked during the pinch stroke to isolate volume from brightness adjustments. Commands are dispatched asynchronously via `subprocess.Popen` to Linux system utilities (`pactl` and `brightnessctl`) to keep the frame loop running smoothly.

---

## Author

* **Canon Rikesh Benu** ([@benu-zukuto](https://www.google.com/search?q=https://github.com/benu-zukuto))[cite: 8]
