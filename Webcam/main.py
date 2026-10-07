"""
Hand Gesture Recognition + Mouse & Two-Hand System Control (Direct USB / V4L2)
Supports single-hand mouse control and two-hand Volume/Brightness adjustments.
Compatible with any Linux laptop and USB UVC Action Cameras.
"""

import os
import sys
import argparse
import time
import threading
import cv2
import mediapipe as mp
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController, TwoHandController


def get_linux_video_devices():
    """Detects active V4L2 capture nodes on Linux from sysfs."""
    devices = []
    base_path = "/sys/class/video4linux"
    if os.path.exists(base_path):
        for node in sorted(os.listdir(base_path)):
            node_dir = os.path.join(base_path, node)
            index_path = os.path.join(node_dir, "index")
            name_path = os.path.join(node_dir, "name")

            # UVC metadata streams use index > 0; capture streams use index 0
            if os.path.exists(index_path):
                try:
                    with open(index_path, "r") as f:
                        if f.read().strip() != "0":
                            continue
                except Exception:
                    pass

            name = "USB Camera"
            if os.path.exists(name_path):
                try:
                    with open(name_path, "r") as f:
                        name = f.read().strip()
                except Exception:
                    pass

            try:
                dev_idx = int(node.replace("video", ""))
                devices.append((dev_idx, name))
            except ValueError:
                pass
    return devices


def select_camera(requested_source=None):
    """Selects the best camera index, prioritizing external USB action cameras."""
    if requested_source is not None:
        if isinstance(requested_source, str) and requested_source.isdigit():
            return int(requested_source)
        return requested_source

    devices = get_linux_video_devices()
    if devices:
        print("\nDetected Video Devices:")
        for idx, name in devices:
            print(f"  [{idx}] /dev/video{idx} - {name}")

        # If multiple cameras exist, prefer external devices over integrated laptop cams
        if len(devices) > 1:
            external = [
                idx for idx, name in devices
                if not any(k in name.lower() for k in ["integrated", "builtin", "built-in", "internal"])
            ]
            chosen = external[-1] if external else devices[-1][0]
            print(f"-> Auto-selected external action camera at index {chosen}\n")
            return chosen
        return devices[0][0]

    # Fallback probing if sysfs inspection is unavailable
    for idx in [2, 0, 1]:
        test_cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if test_cap.isOpened():
            test_cap.release()
            return idx
    return 0


class ThreadedCamera:
    """Pulls frames in a background thread to prevent buffer lag on Linux."""
    def __init__(self, src):
        if isinstance(src, int) or (isinstance(src, str) and src.isdigit()):
            cam_idx = int(src)
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(cam_idx)
        elif isinstance(src, str) and src.startswith("/dev/video"):
            self.cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(src)
        else:
            self.cap = cv2.VideoCapture(src)

        # Linux V4L2 performance optimizations
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.status = False
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()

        if self.cap.isOpened():
            self.status, self.frame = self.cap.read()
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()

    def _update(self):
        while not self.stopped:
            if self.cap.isOpened():
                status, frame = self.cap.read()
                if status:
                    with self.lock:
                        self.frame = frame
                        self.status = status
                else:
                    time.sleep(0.005)
            else:
                time.sleep(0.01)

    def isOpened(self):
        return self.cap.isOpened()

    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.status, self.frame.copy()
            return self.status, None

    def release(self):
        self.stopped = True
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.cap.release()


def draw_landmarks(img, landmarks, connections=None):
    """Draw hand landmarks and connections on the image."""
    h, w, _ = img.shape
    points = []
    for lm in landmarks:
        cx, cy = int(lm.x * w), int(lm.y * h)
        points.append((cx, cy))

    if connections:
        for start, end in connections:
            if start < len(points) and end < len(points):
                cv2.line(img, points[start], points[end], (0, 200, 0), 2)

    for cx, cy in points:
        cv2.circle(img, (cx, cy), 4, (0, 0, 255), cv2.FILLED)


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

COLOR_CYAN = (255, 255, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_ORANGE = (0, 165, 255)
COLOR_GRAY = (120, 120, 120)


def main():
    parser = argparse.ArgumentParser(description="Hand Gesture Control (Action Camera / USB)")
    parser.add_argument(
        "--cam", "--source", dest="source", default=None,
        help="Camera index (e.g. 0, 2), device node (/dev/video2), or stream URL"
    )
    args = parser.parse_args()

    camera_source = select_camera(args.source)
    print(f"Connecting to camera: {camera_source}...")

    cap = ThreadedCamera(camera_source)
    if not cap.isOpened():
        print(f"\nError: Could not open camera source [{camera_source}].")
        print("Linux Action Camera Checklist:")
        print("  1. Ensure the camera mode is set to 'PC Camera' / 'Webcam' on the action camera screen.")
        print("  2. Check data cable connection using: ls /dev/video*")
        print("  3. Ensure your user has V4L permissions: sudo usermod -aG video $USER")
        return

    time.sleep(0.5)

    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    landmarker = HandLandmarker.create_from_options(options)
    recognizer = GestureRecognizer()
    mouse = MouseController(smoothing=2)
    two_hand = TwoHandController()

    pTime = 0
    start_time = time.time()
    mouse_enabled = True

    print("=" * 55)
    print("  Hand Gesture Mouse & System Control (USB Cam)")
    print("=" * 55)
    print("  [1 Hand Mode]")
    print("    - Pointing        -> Move cursor")
    print("    - Pinch Index     -> Left click")
    print("    - Pinch Middle    -> Right click")
    print("    - Thumb Up/Down   -> Dynamic Scroll")
    print("  [2 Hand Mode]")
    print("    - Pinch Both & Move Horizontal -> Volume")
    print("    - Pinch Both & Move Vertical   -> Brightness")
    print("-" * 55)
    print("  Press 'q' to quit | 'm' to toggle control")
    print("=" * 55)

    while True:
        success, img = cap.read()
        if not success or img is None:
            time.sleep(0.005)
            continue

        img = cv2.flip(img, 1)
        img = cv2.resize(img, (640, 360))
        h, w, _ = img.shape

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        current_timestamp_ms = int((time.time() - start_time) * 1000)
        result = landmarker.detect_for_video(mp_image, current_timestamp_ms)

        gesture = "None"
        action = ""
        hand_count = len(result.hand_landmarks) if result.hand_landmarks else 0

        if hand_count > 0:
            for landmarks in result.hand_landmarks:
                draw_landmarks(img, landmarks, HAND_CONNECTIONS)

        # --- 2-HAND MODE (Volume & Brightness) ---
        if hand_count >= 2:
            mouse.reset()
            h1 = result.hand_landmarks[0]
            h2 = result.hand_landmarks[1]

            ctrl_data = two_hand.update(h1, h2)
            gesture = "Two-Hand Control"
            action = ctrl_data["action"]

            pt1 = (int(ctrl_data["p1"][0] * w), int(ctrl_data["p1"][1] * h))
            pt2 = (int(ctrl_data["p2"][0] * w), int(ctrl_data["p2"][1] * h))

            if ctrl_data["both_pinched"]:
                line_color = COLOR_CYAN if ctrl_data["axis"] == 'horizontal' else (
                    COLOR_ORANGE if ctrl_data["axis"] == 'vertical' else COLOR_GREEN
                )
                cv2.line(img, pt1, pt2, line_color, 3)
                cv2.circle(img, pt1, 8, line_color, -1)
                cv2.circle(img, pt2, 8, line_color, -1)

                mid_pt = ((pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2 - 12)
                tag = "VOL" if ctrl_data["axis"] == 'horizontal' else ("BRIGHT" if ctrl_data["axis"] == 'vertical' else "GRIP")
                cv2.putText(img, tag, mid_pt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, line_color, 2)
            else:
                cv2.line(img, pt1, pt2, COLOR_GRAY, 1)

        # --- 1-HAND MODE (Mouse & Scroll) ---
        elif hand_count == 1:
            two_hand.reset()
            landmarks = result.hand_landmarks[0]
            handedness_label = "Right"
            if result.handedness and len(result.handedness) > 0:
                handedness_label = result.handedness[0][0].category_name

            gesture = recognizer.recognize(landmarks, handedness_label)
            if mouse_enabled:
                action = mouse.update(landmarks, gesture)

        # --- NO HANDS ---
        else:
            mouse.reset()
            two_hand.reset()

        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime

        # Top banner
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, 110), (20, 20, 20), -1)
        img = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)

        mode_text = f"Mode: {gesture}" if hand_count != 1 else f"Gesture: {gesture}"
        cv2.putText(img, mode_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_YELLOW, 2)

        if action:
            act_color = COLOR_ORANGE if "Brightness" in action else (COLOR_CYAN if "Volume" in action else COLOR_GREEN)
            cv2.putText(img, f'Action: {action}', (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, act_color, 2)
        elif hand_count >= 2:
            cv2.putText(img, "Pinch both hands to adjust", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_WHITE, 1)

        status_text = "SYSTEM: ON" if mouse_enabled else "SYSTEM: OFF"
        status_color = COLOR_GREEN if mouse_enabled else COLOR_RED
        cv2.putText(img, status_text, (w - 190, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        cv2.putText(img, f'FPS: {int(fps)}', (w - 190, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 2)

        # Bottom banner
        overlay2 = img.copy()
        cv2.rectangle(overlay2, (0, h - 30), (w, h), (20, 20, 20), -1)
        img = cv2.addWeighted(overlay2, 0.7, img, 0.3, 0)
        cv2.putText(img, "2-Hand Pinch: Left-Right=Volume | North-South=Brightness",
                    (10, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

        cv2.imshow("Hand Gesture Mouse Control", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            mouse_enabled = not mouse_enabled
            state = "ON" if mouse_enabled else "OFF"
            print(f"Control: {state}")

    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
