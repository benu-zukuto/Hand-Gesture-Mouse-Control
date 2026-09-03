# Hand Gesture Mouse & System Control

A real-time computer control system that uses a camera stream and **MediaPipe Hand Landmarker** to recognize hand gestures and control the desktop without a physical mouse.

The project supports:

- 🖱️ Single-hand mouse movement
- 👆 Left click using an index-finger pinch
- 🤏 Right click using a middle-finger pinch
- 👍👎 Dynamic scrolling using thumb gestures
- ✋ Two-hand volume control
- ✋ Two-hand screen-brightness control
- 📷 Live hand-landmark visualization
- ⚡ Threaded camera capture for reduced stream-buffer delay

## Features

### Single-Hand Mode

When one hand is detected, the system uses the index finger and gesture state to control the mouse.

| Gesture / Action | Result |
|---|---|
| Pointing | Move the mouse cursor |
| Thumb + Index pinch | Left click |
| Thumb + Middle-finger pinch | Right click |
| Thumbs Up | Scroll up |
| Thumbs Down | Scroll down |
| Thumb Neutral | Pause scrolling |

The cursor movement is smoothed and mapped from the camera frame to the full screen.

### Two-Hand Mode

When two hands are detected, mouse control is temporarily frozen and the system switches to system-control mode.

| Gesture | Movement | Result |
|---|---|---|
| Pinch both hands | Horizontal / left-right | Volume |
| Pinch both hands | Vertical / north-south | Screen brightness |

The system locks onto the dominant movement axis during a pinch gesture to reduce accidental diagonal input.

## How It Works

```text
Phone Camera / IP Camera
          │
          ▼
   Threaded Video Stream
          │
          ▼
      OpenCV Frame
          │
          ▼
   MediaPipe Hand Landmarker
          │
          ▼
   21 Hand Landmarks / Hand
          │
          ├───────────────┐
          ▼               ▼
   Gesture Recognizer   Two-Hand Controller
          │               │
          ▼               ├── Horizontal → Volume
   Mouse Controller       └── Vertical → Brightness
          │
          ├── Cursor movement
          ├── Left click
          ├── Right click
          └── Scrolling
```

## Project Structure

```text
.
├── main.py
├── gesture_recognizer.py
├── mouse_controller.py
├── hand_landmarker.task
└── README.md
```

### `main.py`

The main application loop.

Responsibilities:

- Connects to the camera/IP video stream
- Captures frames in a background thread
- Runs MediaPipe Hand Landmarker
- Supports up to two detected hands
- Sends one-hand gestures to `MouseController`
- Sends two-hand gestures to `TwoHandController`
- Displays the live camera window and status information
- Handles keyboard controls

The application initializes MediaPipe with `num_hands=2` and uses VIDEO running mode.

### `gesture_recognizer.py`

Contains the `GestureRecognizer` class.

It analyzes MediaPipe's 21 hand landmarks and identifies:

- `Thumbs Up`
- `Thumbs Down`
- `Thumb Neutral`
- `Open Palm`
- `Pointing`
- `Unknown`
- `None`

The recognition logic uses landmark distances and palm scale rather than relying directly on the absolute camera position. This helps make the gesture checks more tolerant of changes in hand size and orientation.

### `mouse_controller.py`

Contains two controllers:

#### `MouseController`

Handles:

- Cursor movement
- Cursor smoothing
- Left-click detection
- Right-click detection
- Dynamic scrolling
- Gesture state/reset handling

#### `TwoHandController`

Handles:

- Two-hand pinch detection
- Horizontal movement → volume
- Vertical movement → brightness
- Dominant-axis locking
- Movement deadzone
- Accumulated movement for smoother system adjustments

## Requirements

### Software

- Python 3
- OpenCV
- MediaPipe
- PyAutoGUI
- MediaPipe `hand_landmarker.task` model
- Linux desktop environment for the included volume/brightness commands

Python dependencies:

```bash
pip install opencv-python mediapipe pyautogui
```

System utilities used by the current implementation:

```text
pactl
brightnessctl
```

On Linux, make sure both commands are available in the system `PATH`.

## Camera Setup

The current application expects an HTTP video stream.

The configured stream in `main.py` is:

```text
http://10.245.186.74:8080/video
```

This address is specific to the current setup.

Before running the project, change `stream_url` in `main.py` if the camera/phone has a different IP address or video-stream endpoint.

Example:

```python
stream_url = "http://YOUR_CAMERA_IP:8080/video"
```

The computer and phone/camera should normally be reachable from the same local network.

## MediaPipe Model

The application loads:

```text
hand_landmarker.task
```

from the current working directory.

Make sure the model file exists before starting the application.

The current MediaPipe configuration is:

```text
Running mode: VIDEO
Maximum hands: 2
Minimum detection confidence: 0.5
Minimum hand presence confidence: 0.5
Minimum tracking confidence: 0.5
```

## Running the Project

Place all required files in the same project directory:

```text
main.py
gesture_recognizer.py
mouse_controller.py
hand_landmarker.task
```

Then run:

```bash
python3 main.py
```

If the project uses a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python mediapipe pyautogui
python3 main.py
```

## Keyboard Controls

While the application is running:

| Key | Function |
|---|---|
| `q` | Quit the application |
| `m` | Toggle mouse/system control ON or OFF |

The live window also displays the detected gesture, current action, system state, and FPS.

## Gesture Details

### Pointing

With one hand detected:

```text
Index finger extended
Middle finger curled
Ring finger curled
Pinky finger curled
```

Result:

```text
Move Cursor
```

### Left Click

Bring the thumb tip and index fingertip close together.

The current pinch-close threshold is:

```text
0.07
```

A release is detected above:

```text
0.09
```

A click cooldown is also used to reduce repeated accidental clicks.

### Right Click

Bring the thumb tip and middle fingertip close together.

The same close/release thresholds are used for right-click detection.

### Dynamic Scroll

The recognizer identifies:

```text
Thumbs Up
Thumbs Down
Thumb Neutral
```

The scroll controller applies filtering, a deadzone, and an acceleration mechanism so that stronger thumb movement can produce faster scrolling.

### Two-Hand Volume

1. Show both hands.
2. Pinch the thumb and index finger on both hands.
3. Move the pinch points horizontally.
4. The horizontal movement controls volume.

The controller uses `pactl` and PyAutoGUI for volume adjustment.

### Two-Hand Brightness

1. Show both hands.
2. Pinch the thumb and index finger on both hands.
3. Move the pinch points vertically.
4. The vertical movement controls screen brightness.

The controller uses `brightnessctl` and PyAutoGUI for brightness adjustment.

## Technical Details

### Hand Landmarks

MediaPipe provides 21 landmarks for each detected hand:

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

The gesture recognizer uses these landmarks to calculate distances and determine finger extension/curl states.

### Cursor Smoothing

Cursor movement uses a small history buffer to smooth the normalized index-finger position before converting it to screen coordinates.

The current controller is initialized with:

```python
MouseController(smoothing=2)
```

### Camera Buffer Handling

`ThreadedCamera` continuously reads frames in a daemon thread and keeps the most recent frame.

The capture buffer is configured with:

```python
cv2.CAP_PROP_BUFFERSIZE = 1
```

This is intended to reduce visible delay when using an IP camera stream.

## Linux System Controls

The current implementation is designed around Linux desktop utilities.

### Volume

The controller can call:

```bash
pactl set-sink-volume @DEFAULT_SINK@ ...
```

and also sends volume keys through PyAutoGUI.

### Brightness

The controller can call:

```bash
brightnessctl set ...
```

and also sends brightness keys through PyAutoGUI.

If these utilities are unavailable or unsupported by the desktop environment, mouse and gesture recognition can still work, but the corresponding system-control actions may not.

## Troubleshooting

### Camera connection failed

If the application reports:

```text
Error: Could not connect to phone stream
```

Check:

1. The phone/camera streaming application is running.
2. The IP address in `main.py` is correct.
3. The computer can reach the phone over the network.
4. The video endpoint is correct.
5. No firewall is blocking the stream port.

### `hand_landmarker.task` not found

Make sure the model file is in the project directory or update:

```python
model_asset_path='hand_landmarker.task'
```

with the correct path.

### Volume does not change

Check that `pactl` works manually:

```bash
pactl get-default-sink
```

Then test the relevant volume command on the system.

### Brightness does not change

Check:

```bash
brightnessctl
```

If the display or desktop environment does not expose a controllable backlight, `brightnessctl` may not be able to change the screen brightness.

### Cursor feels too sensitive

Adjust:

```python
self.frame_margin = 0.15
```

or change:

```python
MouseController(smoothing=2)
```

to a larger smoothing value.

### Clicks trigger repeatedly

The controller already uses separate close/release thresholds and a cooldown:

```text
PINCH_CLOSE    = 0.07
PINCH_RELEASE  = 0.09
CLICK_COOLDOWN = 0.35
```

These can be tuned for different cameras, lighting conditions, or hand positions.

## Performance Notes

The application:

- Processes frames continuously from an IP stream
- Resizes frames to `640 × 360`
- Uses MediaPipe VIDEO mode
- Tracks up to two hands
- Uses a background camera thread
- Uses lightweight geometric gesture classification
- Displays the current FPS

Actual performance depends on the computer, camera stream, network latency, lighting, and MediaPipe processing speed.

## Safety / Control Notes

This application sends real mouse and system-control events to the operating system.

Before using it:

- Keep the mouse-control window accessible.
- Use `m` to disable control when needed.
- Use `q` to exit the application.
- Be aware that detected gestures can trigger real clicks, scrolling, volume changes, and brightness changes.

## Current Limitations

The current implementation is focused on the functionality present in the supplied source code.

Not currently implemented in the provided modules:

- Gesture customization through a configuration file
- GUI settings panel
- Gesture recording/training
- Multi-monitor-specific cursor mapping
- Windows/macOS-specific system-control backends
- Persistent user profiles
- Calibration UI
- Voice control
- Gesture history logging

## Future Improvements

Possible future development areas:

- Add a calibration screen
- Add configurable gesture mappings
- Add sensitivity controls
- Add configurable camera URLs
- Add multi-monitor support
- Add Windows and macOS backends
- Add more gestures
- Add gesture confidence indicators
- Add an FPS/performance settings panel
- Package the project as a standalone application

## License

No license information is currently specified in the provided source files.

If this project will be published publicly, add an appropriate license file such as:

```text
LICENSE
```

and update this section accordingly.

## Project Status

**Current status:** Functional prototype

The supplied implementation provides live hand tracking, gesture recognition, mouse control, scrolling, and two-hand volume/brightness control through a camera stream.
