"""
Hand Gesture Recognition + Mouse Control
Uses MediaPipe Tasks API (v1.0+) with HandLandmarker in VIDEO mode.
Opens the webcam, detects hand landmarks, recognizes gestures,
and controls the mouse cursor accordingly.

Controls:
  - Index finger    → Move cursor
  - Thumb + Index   → Left click (pinch)
  - Thumb + Middle  → Right click (pinch)
  - Peace sign      → Scroll (move hand up/down)
  - Fist            → Double click
  - Press 'q'       → Quit
  - Press 'm'       → Toggle mouse control on/off
"""

import cv2
import mediapipe as mp
import time
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController


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
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
        cv2.circle(img, (cx, cy), 7, (0, 0, 200), 1)


# Standard hand connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

# Colors for display
COLOR_CYAN = (255, 255, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_ORANGE = (0, 165, 255)


def main():
    # Initialize the webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Initialize MediaPipe HandLandmarker
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    landmarker = HandLandmarker.create_from_options(options)

    # Initialize modules
    recognizer = GestureRecognizer()
    mouse = MouseController(smoothing=5)

    # State
    pTime = 0
    frame_timestamp_ms = 0
    mouse_enabled = True

    print("=" * 50)
    print("  Hand Gesture Mouse Control")
    print("=" * 50)
    print("  Index finger  → Move cursor")
    print("  Thumb + Index  → Left click")
    print("  Thumb + Middle → Right click")
    print("  Peace sign     → Scroll up/down")
    print("  Fist           → Double click")
    print("-" * 50)
    print("  Press 'q' to quit")
    print("  Press 'm' to toggle mouse control")
    print("=" * 50)

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image from camera.")
            break

        # Flip for selfie view
        img = cv2.flip(img, 1)

        # Convert to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        # Detect landmarks
        frame_timestamp_ms += 33
        result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

        gesture = "None"
        action = ""

        if result.hand_landmarks:
            for hand_idx, landmarks in enumerate(result.hand_landmarks):
                # Draw landmarks
                draw_landmarks(img, landmarks, HAND_CONNECTIONS)

                # Get handedness
                handedness_label = "Right"
                if result.handedness and hand_idx < len(result.handedness):
                    handedness_label = result.handedness[hand_idx][0].category_name

                # Recognize gesture
                gesture = recognizer.recognize(landmarks, handedness_label)

                # Control mouse if enabled
                if mouse_enabled:
                    action = mouse.update(landmarks, gesture)
        else:
            # No hand detected — reset mouse state
            mouse.reset()

        # Calculate FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime

        # --- Draw UI overlay ---
        h, w, _ = img.shape

        # Top banner (semi-transparent dark)
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, 130), (20, 20, 20), -1)
        img = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)

        # Gesture name
        cv2.putText(img, f'Gesture: {gesture}', (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_YELLOW, 2)

        # Mouse action
        if mouse_enabled and action:
            action_color = COLOR_GREEN
            if "Click" in action:
                action_color = COLOR_ORANGE
            elif "Scroll" in action:
                action_color = COLOR_CYAN
            cv2.putText(img, f'Action: {action}', (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, action_color, 2)

        # Debug: pinch distances (visual bars)
        if mouse_enabled:
            d = mouse.debug
            ti_dist = d["thumb_index_dist"]
            tm_dist = d["thumb_middle_dist"]
            threshold = d["pinch_threshold"]

            # Thumb-Index distance bar
            bar_x = 20
            bar_y = 85
            bar_max_w = 250
            ti_bar_w = int(min(ti_dist / 0.20, 1.0) * bar_max_w)
            thresh_x = int((threshold / 0.20) * bar_max_w)
            ti_color = COLOR_GREEN if ti_dist < threshold else (100, 100, 255)
            cv2.putText(img, "L-Click:", (bar_x, bar_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_WHITE, 1)
            cv2.rectangle(img, (bar_x + 65, bar_y - 12), (bar_x + 65 + ti_bar_w, bar_y), ti_color, -1)
            cv2.line(img, (bar_x + 65 + thresh_x, bar_y - 14), (bar_x + 65 + thresh_x, bar_y + 2), COLOR_YELLOW, 2)

            # Thumb-Middle distance bar
            bar_y2 = 110
            tm_bar_w = int(min(tm_dist / 0.20, 1.0) * bar_max_w)
            tm_color = COLOR_GREEN if tm_dist < threshold else (100, 100, 255)
            cv2.putText(img, "R-Click:", (bar_x, bar_y2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_WHITE, 1)
            cv2.rectangle(img, (bar_x + 65, bar_y2 - 12), (bar_x + 65 + tm_bar_w, bar_y2), tm_color, -1)
            cv2.line(img, (bar_x + 65 + thresh_x, bar_y2 - 14), (bar_x + 65 + thresh_x, bar_y2 + 2), COLOR_YELLOW, 2)

        # Mouse control status
        status_text = "MOUSE: ON" if mouse_enabled else "MOUSE: OFF"
        status_color = COLOR_GREEN if mouse_enabled else COLOR_RED
        cv2.putText(img, status_text, (w - 200, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # FPS
        cv2.putText(img, f'FPS: {int(fps)}', (w - 200, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_WHITE, 2)

        # Bottom help bar
        overlay2 = img.copy()
        cv2.rectangle(overlay2, (0, h - 35), (w, h), (20, 20, 20), -1)
        img = cv2.addWeighted(overlay2, 0.7, img, 0.3, 0)
        cv2.putText(img, "Pinch=Click | Peace=Scroll | Fist=DblClick | 'q'=Quit | 'm'=Toggle",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

        # Show the video feed
        cv2.imshow("Hand Gesture Mouse Control", img)

        # Key handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            mouse_enabled = not mouse_enabled
            state = "ON" if mouse_enabled else "OFF"
            print(f"Mouse control: {state}")

    # Cleanup
    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
