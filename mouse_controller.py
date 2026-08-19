"""
Mouse Controller Module
Maps hand gestures and landmarks to mouse actions using PyAutoGUI.

Improved with:
  - Larger pinch thresholds for easier triggering
  - Cursor freezes during click actions (no jitter)
  - Visual debug info support
  - Better scroll sensitivity
"""

import pyautogui
import time
import math

# PyAutoGUI config
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


class MouseController:
    """Controls the mouse cursor using hand landmark positions and gestures."""

    def __init__(self, screen_w=None, screen_h=None, smoothing=6):
        """
        Initialize the MouseController.

        Args:
            screen_w: Screen width in pixels (auto-detected if None).
            screen_h: Screen height in pixels (auto-detected if None).
            smoothing: Number of frames to average for smooth cursor movement.
        """
        self.screen_w = screen_w or pyautogui.size()[0]
        self.screen_h = screen_h or pyautogui.size()[1]
        self.smoothing = smoothing

        # Frame margin — maps central 70% of camera to full screen
        self.frame_margin = 0.15

        # History buffers for smoothing
        self.x_history = []
        self.y_history = []

        # --- Click state ---
        self.left_clicking = False
        self.left_click_time = 0

        self.right_clicking = False
        self.right_click_time = 0

        # --- Double click ---
        self.double_click_time = 0

        # --- Scroll state ---
        self.scroll_prev_y = None
        self.last_scroll_time = 0

        # --- Pinch thresholds (normalized coords, bigger = easier to trigger) ---
        self.PINCH_CLOSE = 0.08    # Distance to START a pinch
        self.PINCH_RELEASE = 0.10  # Distance to RELEASE a pinch (hysteresis)
        self.CLICK_COOLDOWN = 0.4  # Seconds between repeated clicks

        # --- Debug info (populated each frame) ---
        self.debug = {
            "thumb_index_dist": 0.0,
            "thumb_middle_dist": 0.0,
            "pinch_threshold": self.PINCH_CLOSE,
        }

    def _smooth(self, x, y):
        """Apply moving average smoothing to cursor position."""
        self.x_history.append(x)
        self.y_history.append(y)

        if len(self.x_history) > self.smoothing:
            self.x_history.pop(0)
            self.y_history.pop(0)

        return (
            sum(self.x_history) / len(self.x_history),
            sum(self.y_history) / len(self.y_history),
        )

    def _map_to_screen(self, norm_x, norm_y):
        """Map normalized camera coords to screen pixels with margin remapping."""
        mapped_x = (norm_x - self.frame_margin) / (1.0 - 2 * self.frame_margin)
        mapped_y = (norm_y - self.frame_margin) / (1.0 - 2 * self.frame_margin)
        mapped_x = max(0.0, min(1.0, mapped_x))
        mapped_y = max(0.0, min(1.0, mapped_y))
        return int(mapped_x * self.screen_w), int(mapped_y * self.screen_h)

    @staticmethod
    def _distance(lm1, lm2):
        """Euclidean distance between two landmarks (normalized coords)."""
        return math.sqrt((lm1.x - lm2.x) ** 2 + (lm1.y - lm2.y) ** 2)

    def move_cursor(self, index_tip):
        """Move mouse cursor to follow the index finger tip."""
        sx, sy = self._smooth(index_tip.x, index_tip.y)
        screen_x, screen_y = self._map_to_screen(sx, sy)
        pyautogui.moveTo(screen_x, screen_y, _pause=False)

    def check_left_click(self, thumb_tip, index_tip):
        """
        Detect left click via thumb-index pinch.
        Uses hysteresis (different thresholds for press/release) to avoid flicker.

        Returns:
            str or None: "Left Click" if triggered, None otherwise.
        """
        dist = self._distance(thumb_tip, index_tip)
        self.debug["thumb_index_dist"] = dist
        now = time.time()

        if not self.left_clicking:
            # Start click when fingers close enough
            if dist < self.PINCH_CLOSE and (now - self.left_click_time) > self.CLICK_COOLDOWN:
                self.left_clicking = True
                self.left_click_time = now
                pyautogui.click(_pause=False)
                return "Left Click"
        else:
            # Release when fingers separate beyond release threshold
            if dist > self.PINCH_RELEASE:
                self.left_clicking = False

        return "Holding" if self.left_clicking else None

    def check_right_click(self, thumb_tip, middle_tip):
        """
        Detect right click via thumb-middle pinch.

        Returns:
            str or None: "Right Click" if triggered, None otherwise.
        """
        dist = self._distance(thumb_tip, middle_tip)
        self.debug["thumb_middle_dist"] = dist
        now = time.time()

        if not self.right_clicking:
            if dist < self.PINCH_CLOSE and (now - self.right_click_time) > self.CLICK_COOLDOWN:
                self.right_clicking = True
                self.right_click_time = now
                pyautogui.rightClick(_pause=False)
                return "Right Click"
        else:
            if dist > self.PINCH_RELEASE:
                self.right_clicking = False

        return "Holding R" if self.right_clicking else None

    def check_scroll(self, landmarks, gesture):
        """
        Scroll when peace sign detected — direction follows hand movement.

        Returns:
            str or None: "Scroll Up"/"Scroll Down" if scrolling, None otherwise.
        """
        if gesture != "Peace Sign":
            self.scroll_prev_y = None
            return None

        current_y = landmarks[8].y  # Index finger tip
        now = time.time()

        if self.scroll_prev_y is None:
            self.scroll_prev_y = current_y
            return "Scroll Ready"

        # Throttle scroll events
        if now - self.last_scroll_time < 0.08:
            return "Scrolling..."

        delta = self.scroll_prev_y - current_y  # Positive = moved up
        if abs(delta) > 0.012:
            scroll_amount = int(delta * 30)
            pyautogui.scroll(scroll_amount, _pause=False)
            self.scroll_prev_y = current_y
            self.last_scroll_time = now
            return "Scroll Up" if delta > 0 else "Scroll Down"

        return "Scroll Ready"

    def check_double_click(self, gesture):
        """
        Double click on fist gesture.

        Returns:
            str or None: "Double Click" if triggered, None otherwise.
        """
        now = time.time()
        if gesture == "Fist" and (now - self.double_click_time) > 1.0:
            pyautogui.doubleClick(_pause=False)
            self.double_click_time = now
            return "Double Click"
        return None

    def update(self, landmarks, gesture):
        """
        Main update — call once per frame.

        Args:
            landmarks: List of 21 hand landmarks.
            gesture: The recognized gesture string.

        Returns:
            str: Description of the current mouse action.
        """
        if not landmarks or len(landmarks) < 21:
            return "No hand"

        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        # --- Priority 1: Scroll (Peace Sign) ---
        scroll_result = self.check_scroll(landmarks, gesture)
        if scroll_result:
            return scroll_result

        # --- Priority 2: Double Click (Fist) ---
        dbl = self.check_double_click(gesture)
        if dbl:
            return dbl

        # --- Priority 3: Check for pinch clicks BEFORE moving ---
        left = self.check_left_click(thumb_tip, index_tip)
        right = self.check_right_click(thumb_tip, middle_tip)

        # If actively clicking, DON'T move the cursor (prevents jitter)
        if left and left != "Holding":
            return left
        if right and right != "Holding":
            return right

        # If holding a click, still don't move
        if self.left_clicking or self.right_clicking:
            action = "Holding"
            if self.left_clicking:
                action = "L-Click Hold"
            if self.right_clicking:
                action = "R-Click Hold"
            return action

        # --- Priority 4: Move cursor ---
        self.move_cursor(index_tip)
        return "Moving"

    def reset(self):
        """Reset all state (call when hand is lost)."""
        self.x_history.clear()
        self.y_history.clear()
        self.left_clicking = False
        self.right_clicking = False
        self.scroll_prev_y = None
