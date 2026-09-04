# 🖐️ Hand Gesture Mouse & System Control

A real-time Python application that lets you **control your computer using hand gestures** through a camera stream.

It uses **OpenCV + MediaPipe Hand Landmarker + PyAutoGUI** to detect hand movements and convert them into mouse, scrolling, volume, and brightness controls.

## ✨ Features

* 🖱️ Move the mouse using your index finger
* 👆 Left click using thumb + index finger pinch
* 🤏 Right click using thumb + middle finger pinch
* 👍 Scroll up using thumbs-up gesture
* 👎 Scroll down using thumbs-down gesture
* ✋ Two-hand volume control
* 💡 Two-hand brightness control
* 📷 Supports IP/phone camera streams
* 🎯 Tracks up to 2 hands
* 📊 Live FPS and gesture information
* ⌨️ Keyboard controls for enabling/disabling the system

---

# 🛠️ Requirements

### Hardware

* Computer running Linux
* Camera or Android phone
* Computer and phone should be connected to the same network

### Software

* Python 3
* Git
* OpenCV
* MediaPipe
* PyAutoGUI
* `pactl`
* `brightnessctl`

> **Note:** Volume and brightness control currently depend on Linux system utilities.

---

# 🚀 Installation

## 1. Update your system

This updates the Linux package list before installing dependencies.

```bash
sudo apt update
```

## 2. Install required system packages

This installs Python, virtual-environment support, Git, and the Linux utilities used by the project.

```bash
sudo apt install -y python3 python3-pip python3-venv git pulseaudio-utils brightnessctl
```

## 3. Clone the repository

This downloads the project from GitHub to your computer.

```bash
git clone https://github.com/benu-zukuto/Hand-Gesture-Mouse-Control.git
```

## 4. Enter the project folder

This moves the terminal into the downloaded project directory.

```bash
cd Hand-Gesture-Mouse-Control
```

## 5. Create a virtual environment

This creates an isolated Python environment for the project dependencies.

```bash
python3 -m venv .venv
```

## 6. Activate the virtual environment

This makes Python use the project's isolated environment.

```bash
source .venv/bin/activate
```

## 7. Install Python dependencies

This installs all Python libraries listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

---

# 📦 Download the MediaPipe Model

The project requires the MediaPipe `hand_landmarker.task` model for hand detection.

Run this command inside the project folder:

```bash
curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o hand_landmarker.task
```

Check that the model exists:

```bash
ls -lh hand_landmarker.task
```

The project should now contain:

```text
Hand-Gesture-Mouse-Control/
├── .venv/
├── hand_landmarker.task
├── main.py
├── gesture_recognizer.py
├── mouse_controller.py
├── requirements.txt
└── README.md
```

---

# 📱 Camera Setup

The current application expects an **HTTP video stream** from a phone or IP camera.

The default camera URL in the project is:

```text
http://10.245.186.74:8080/video
```

This IP address is specific to the original setup, so it must be changed when using another phone or camera.

## Using an Android Phone

Install an Android IP-camera application that provides an HTTP video stream.

Start the camera server and find the phone's IP address.

For example:

```text
http://192.168.1.25:8080/video
```

Open the URL in a browser on the computer to verify that the video stream works.

---

# 🔧 Change the Camera URL

Open `main.py`:

```bash
nano main.py
```

Find:

```python
stream_url = "http://10.245.186.74:8080/video"
```

Change it to the phone's address:

```python
stream_url = "http://YOUR_PHONE_IP:8080/video"
```

Example:

```python
stream_url = "http://192.168.1.25:8080/video"
```

Save the file and exit.

---

# ▶️ Run the Project

Make sure the virtual environment is active:

```bash
source .venv/bin/activate
```

Start the application:

```bash
python3 main.py
```

A camera window should open and start detecting hands.

---

# 🖐️ Gesture Controls

## One-Hand Mode

When one hand is detected, the system operates as a virtual mouse.

| Gesture                 | Action         |
| ----------------------- | -------------- |
| ☝️ Pointing             | Move mouse     |
| 🤏 Thumb + Index pinch  | Left click     |
| 🤏 Thumb + Middle pinch | Right click    |
| 👍 Thumbs Up            | Scroll up      |
| 👎 Thumbs Down          | Scroll down    |
| 🤚 Thumb Neutral        | Stop scrolling |

---

## 🖱️ Mouse Movement

Point your index finger while keeping the other fingers curled.

```text
☝️
```

The index-finger position is converted into the mouse cursor position.

Cursor movement is smoothed to reduce unwanted shaking.

---

# 👆 Left Click

Bring your **thumb and index finger** together.

```text
👍 + ☝️
   ↓
 Pinch
```

The pinch is interpreted as a left mouse click.

---

# 🤏 Right Click

Bring your **thumb and middle finger** together.

```text
Thumb + Middle Finger
        ↓
      Pinch
```

The gesture is interpreted as a right mouse click.

---

# 👍 Scroll Up

Show a thumbs-up gesture:

```text
👍
```

The system scrolls upward.

---

# 👎 Scroll Down

Show a thumbs-down gesture:

```text
👎
```

The system scrolls downward.

---

# ✋ Two-Hand Controls

When two hands are detected, mouse control is temporarily frozen and the system switches to system-control mode.

## 🔊 Volume Control

1. Show both hands.
2. Pinch thumb + index finger on both hands.
3. Move both hands horizontally.
4. Horizontal movement changes volume.

```text
←────────────→
    VOLUME
```

The project uses `pactl` for Linux audio control.

---

# 💡 Brightness Control

1. Show both hands.
2. Pinch thumb + index finger on both hands.
3. Move both hands vertically.
4. Vertical movement changes screen brightness.

```text
      ↑
      │
 BRIGHTNESS
      │
      ↓
```

The project uses `brightnessctl` for Linux brightness control.

---

# ⌨️ Keyboard Controls

| Key | Action                                  |
| --- | --------------------------------------- |
| `m` | Enable/disable mouse and system control |
| `q` | Quit application                        |

### Disable Control

Press:

```text
m
```

This is useful when you need to temporarily stop gesture-controlled actions.

### Exit

Press:

```text
q
```

This closes the application.

---

# 🧠 How It Works

```text
             📱 Phone / IP Camera
                     │
                     ▼
              HTTP Video Stream
                     │
                     ▼
                  OpenCV
                     │
                     ▼
          MediaPipe Hand Landmarker
                     │
                     ▼
              21 Hand Landmarks
                     │
             ┌───────┴───────┐
             ▼               ▼
     Gesture Recognizer   Two-Hand Controller
             │               │
             ▼               ├── Horizontal → Volume
      Mouse Controller       └── Vertical → Brightness
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
    Cursor  Click  Scroll
```

The application processes the camera frames, detects hand landmarks, identifies gestures, and sends the corresponding control commands to the operating system.

---

# 📁 Project Structure

```text
Hand-Gesture-Mouse-Control/
│
├── main.py
├── gesture_recognizer.py
├── mouse_controller.py
├── requirements.txt
├── hand_landmarker.task
├── README.md
└── .gitignore
```

### `main.py`

The main application that connects the camera, MediaPipe, gesture recognition, and controllers.

### `gesture_recognizer.py`

Detects gestures such as pointing, thumbs up, thumbs down, and thumb neutral using MediaPipe hand landmarks.

### `mouse_controller.py`

Controls cursor movement, clicking, scrolling, volume, and brightness.

### `requirements.txt`

Contains the Python packages required by the project.

### `hand_landmarker.task`

The MediaPipe model used to detect hand landmarks.

---

# 🔬 Hand Detection

MediaPipe provides **21 landmarks for each detected hand**.

```text
0   Wrist

1   Thumb CMC
2   Thumb MCP
3   Thumb IP
4   Thumb Tip

5   Index MCP
6   Index PIP
7   Index DIP
8   Index Tip

9   Middle MCP
10  Middle PIP
11  Middle DIP
12  Middle Tip

13  Ring MCP
14  Ring PIP
15  Ring DIP
16  Ring Tip

17  Pinky MCP
18  Pinky PIP
19  Pinky DIP
20  Pinky Tip
```

The gesture recognizer uses these landmarks to determine finger positions and gestures.

---

# ⚙️ MediaPipe Configuration

The current application uses:

```text
Running Mode: VIDEO
Maximum Hands: 2
Detection Confidence: 0.5
Hand Presence Confidence: 0.5
Tracking Confidence: 0.5
```

The application processes up to two hands at the same time.

---

# 🖱️ Cursor Smoothing

Cursor movement uses smoothing to reduce shaking caused by small changes in hand position.

The current controller uses:

```python
MouseController(smoothing=2)
```

If the cursor feels too sensitive, increase the smoothing value.

For example:

```python
MouseController(smoothing=4)
```

---

# 🐢 Camera Latency

The project uses a separate camera thread to continuously capture the latest frame.

This helps reduce delay when using an IP camera stream.

The camera buffer is configured to:

```python
cv2.CAP_PROP_BUFFERSIZE = 1
```

---

# 🔊 Linux Volume Requirements

Check whether `pactl` is available:

```bash
pactl --version
```

Check the current default audio device:

```bash
pactl get-default-sink
```

If `pactl` is unavailable, install the required package:

```bash
sudo apt install -y pulseaudio-utils
```

---

# 💡 Linux Brightness Requirements

Check whether `brightnessctl` is installed:

```bash
brightnessctl
```

If it is missing:

```bash
sudo apt install -y brightnessctl
```

Brightness support depends on whether the Linux system exposes a controllable display backlight.

---

# 🧪 Troubleshooting

## ❌ Camera Does Not Connect

Check whether the phone camera server is running.

Then test the stream in a browser:

```text
http://YOUR_PHONE_IP:8080/video
```

If it does not open, check:

* Phone and computer are on the same network.
* Phone IP address is correct.
* Camera server is running.
* Port `8080` is not blocked.
* The video endpoint is `/video`.

---

## ❌ `hand_landmarker.task` Not Found

Check whether the file exists:

```bash
ls -lh hand_landmarker.task
```

If it does not exist, download it again:

```bash
curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o hand_landmarker.task
```

---

## ❌ Python Module Not Found

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then reinstall the dependencies:

```bash
pip install -r requirements.txt
```

---

## ❌ Volume Does Not Change

Test:

```bash
pactl get-default-sink
```

If this command fails, the Linux audio system may not provide the expected PulseAudio/PipeWire compatibility.

---

## ❌ Brightness Does Not Change

Test:

```bash
brightnessctl
```

If no controllable backlight is detected, brightness control may not work with the current hardware or desktop environment.

---

## ❌ Cursor Is Too Sensitive

Open:

```bash
nano mouse_controller.py
```

Find:

```python
MouseController(smoothing=2)
```

Increase the value:

```python
MouseController(smoothing=4)
```

Higher smoothing generally produces slower but steadier cursor movement.

---

## ❌ Repeated Clicks

The controller already uses separate pinch-close and pinch-release thresholds plus a click cooldown to reduce accidental repeated clicks.

Current values:

```text
Pinch Close:    0.07
Pinch Release:  0.09
Click Cooldown: 0.35 seconds
```

These values can be adjusted inside `mouse_controller.py`.

---

# ⚡ Quick Start

For someone who already has Python and Git installed:

```bash
git clone https://github.com/benu-zukuto/Hand-Gesture-Mouse-Control.git
```

Clone the project.

```bash
cd Hand-Gesture-Mouse-Control
```

Enter the project directory.

```bash
python3 -m venv .venv
```

Create the Python virtual environment.

```bash
source .venv/bin/activate
```

Activate the environment.

```bash
pip install -r requirements.txt
```

Install Python dependencies.

```bash
curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o hand_landmarker.task
```

Download the MediaPipe hand model.

```bash
python3 main.py
```

Start the application.

---

# 🔄 Run Again Later

After the project has already been installed, only these commands are normally required:

```bash
cd Hand-Gesture-Mouse-Control
```

Open the project directory.

```bash
source .venv/bin/activate
```

Activate the Python environment.

```bash
python3 main.py
```

Start the hand-control system.

---

# ⚠️ Safety

This application sends **real mouse and system-control events** to the operating system.

Before using it:

* Keep the application window accessible.
* Use `m` to disable controls when necessary.
* Use `q` to exit.
* Be aware that gestures can trigger real clicks.
* Avoid using the system near important buttons or destructive actions until the gestures are working reliably.

---

# 🚧 Current Limitations

The current implementation does not include:

* Gesture customization through a configuration file
* GUI settings panel
* Gesture recording/training
* Multi-monitor-specific cursor mapping
* Windows/macOS system-control backends
* Persistent user profiles
* Calibration UI
* Voice control
* Gesture history logging

The current system is primarily designed around **Linux + IP camera streaming**.

---

# 🔮 Future Improvements

Possible improvements include:

* 🎯 Gesture calibration
* ⚙️ Custom gesture mapping
* 🎚️ Sensitivity controls
* 📱 Camera URL configuration
* 🖥️ Multi-monitor support
* 🪟 Windows support
* 🍎 macOS support
* ✋ Additional gestures
* 📊 Gesture confidence indicators
* 📈 Performance settings
* 📦 Standalone executable
* 🎥 Direct USB webcam support

---

# 🧩 Technologies Used

| Technology      | Purpose                        |
| --------------- | ------------------------------ |
| Python          | Main programming language      |
| OpenCV          | Camera and video processing    |
| MediaPipe       | Hand landmark detection        |
| PyAutoGUI       | Mouse and keyboard interaction |
| NumPy           | Numerical calculations         |
| `pactl`         | Linux volume control           |
| `brightnessctl` | Linux brightness control       |

---

# 📜 License

No license is currently specified for this project.

If the project is intended for public reuse or contribution, add a `LICENSE` file and specify the chosen license.

---

# 📊 Project Status

**Status: Functional Prototype**

The current implementation provides:

* Real-time hand tracking
* Gesture recognition
* Mouse movement
* Left clicking
* Right clicking
* Scrolling
* Two-hand volume control
* Two-hand brightness control
* Live camera visualization
* Keyboard safety controls

---

# 👨‍💻 Author

**benu-zukuto**

GitHub Repository:

[Benu](https://github.com/benu-zukuto)

---

# ⭐ Support

If this project is useful, consider giving the repository a ⭐ on GitHub.

Contributions, improvements, bug reports, and new gesture ideas are welcome.
