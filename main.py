"""
Hand Gesture Recognition + Mouse & Two-Hand System Control (Live Stream)
Supports single-hand mouse control and two-hand Volume/Brightness adjustments[cite: 2].
"""

import cv2
import mediapipe as mp
import time
import threading
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController, TwoHandController


class ThreadedCamera:
    """Continuously pulls frames from the IP stream to eliminate buffer delay."""
    def __init__(self, src):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
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
    """Draw hand landmarks and connections on the image[cite: 2]."""
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
    stream_url = "http://10.245.186.74:8080/video"
    print(f"Connecting to phone stream at {stream_url}...")

    cap = ThreadedCamera(stream_url)
    if not cap.isOpened():
        print(f"Error: Could not connect to phone stream at {stream_url}")
        return

    time.sleep(0.5)

    # Initialize MediaPipe HandLandmarker with num_hands=2[cite: 2]
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=2,  # Multi-hand support
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
    print("  Hand Gesture Mouse & System Control (Live)")
    print("=" * 55)
    print("  [1 Hand Mode]")
    print("    - Pointing        → Move cursor")
    print("    - Pinch Index     → Left click")
    print("    - Pinch Middle    → Right click")
    print("    - Thumb Up/Down   → Dynamic Scroll")
    print("  [2 Hand Mode]")
    print("    - Pinch Both & Move Horizontal (Left-Right) → Volume")
    print("    - Pinch Both & Move Vertical (North-South)  → Brightness")
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

        # Draw hand skeletons[cite: 2]
        if hand_count > 0:
            for landmarks in result.hand_landmarks:
                draw_landmarks(img, landmarks, HAND_CONNECTIONS)

        # --- 2-HAND MODE (Volume & Brightness) ---
        if hand_count >= 2:
            mouse.reset()  # Freeze mouse during two-hand gestures
            h1 = result.hand_landmarks[0]
            h2 = result.hand_landmarks[1]

            ctrl_data = two_hand.update(h1, h2)
            gesture = "Two-Hand Control"
            action = ctrl_data["action"]

            # Visual connector between hands
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

        # Frame rate calculation[cite: 2]
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime

        # Top banner[cite: 2]
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, 110), (20, 20, 20), -1)
        img = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)

        # Header status
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

        # Bottom guide banner[cite: 2]
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