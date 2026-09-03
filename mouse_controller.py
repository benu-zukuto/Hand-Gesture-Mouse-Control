"""
Mouse & System Controller Module
Handles single-hand mouse navigation and two-hand Volume/Brightness adjustments.
"""

import pyautogui
import subprocess
import time
import math

# Disable fail-safe to prevent edge crashes
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class TwoHandController:
    """Handles two-handed gestures: Horizontal for Volume, Vertical (North-South) for Brightness."""

    def __init__(self):
        self.last_action_time = 0
        self.active_axis = None  # 'horizontal' (Volume) or 'vertical' (Brightness)
        
        self.prev_dist_x = None
        self.prev_dist_y = None
        
        self.vol_accumulator = 0.0
        self.bright_accumulator = 0.0
        
        # Sensitivity parameters
        self.PINCH_THRESH = 0.095  # Max distance between thumb and index to register pinch
        self.DEADZONE = 0.008      # Minimum movement required to avoid jitter

    @staticmethod
    def _dist(p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _adjust_volume(self, clicks):
        """Dispatches volume steps via PyAutoGUI and non-blocking pactl (Linux pulse/pipewire)."""
        if clicks == 0:
            return
        key = 'volumeup' if clicks > 0 else 'volumedown'
        for _ in range(abs(clicks)):
            try:
                pyautogui.press(key, _pause=False)
            except Exception:
                pass
        try:
            sign = "+" if clicks > 0 else "-"
            subprocess.Popen(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{sign}{abs(clicks) * 3}%"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def _adjust_brightness(self, clicks):
        """Dispatches brightness steps via PyAutoGUI and non-blocking brightnessctl."""
        if clicks == 0:
            return
        key = 'brightnessup' if clicks > 0 else 'brightnessdown'
        for _ in range(abs(clicks)):
            try:
                pyautogui.press(key, _pause=False)
            except Exception:
                pass
        try:
            arg = f"+{abs(clicks) * 4}%" if clicks > 0 else f"{abs(clicks) * 4}%-"
            subprocess.Popen(
                ["brightnessctl", "set", arg],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    def update(self, hand1, hand2):
        """
        Processes two hands.
        Returns:
            dict containing pinch states, line coordinates, active axis, and status text.
        """
        # Landmark 4: Thumb Tip, Landmark 8: Index Tip
        h1_thumb, h1_index = hand1[4], hand1[8]
        h2_thumb, h2_index = hand2[4], hand2[8]

        # Calculate pinch distances on each hand
        h1_pinch_dist = self._dist(h1_thumb, h1_index)
        h2_pinch_dist = self._dist(h2_thumb, h2_index)
        
        h1_pinched = h1_pinch_dist < self.PINCH_THRESH
        h2_pinched = h2_pinch_dist < self.PINCH_THRESH
        both_pinched = h1_pinched and h2_pinched

        # Midpoints of the pinch on each hand
        p1 = ((h1_thumb.x + h1_index.x) / 2.0, (h1_thumb.y + h1_index.y) / 2.0)
        p2 = ((h2_thumb.x + h2_index.x) / 2.0, (h2_thumb.y + h2_index.y) / 2.0)

        dist_x = abs(p1[0] - p2[0])
        dist_y = abs(p1[1] - p2[1])

        status = "2 Hands: Pinch both to adjust"
        action = ""

        if both_pinched:
            if self.prev_dist_x is None or self.prev_dist_y is None:
                self.prev_dist_x = dist_x
                self.prev_dist_y = dist_y
                return {
                    "p1": p1, "p2": p2, "both_pinched": True,
                    "axis": self.active_axis, "status": "Pinch Active: Move to adjust", "action": ""
                }

            dx = dist_x - self.prev_dist_x
            dy = dist_y - self.prev_dist_y

            # Lock dominant axis for this pinch stroke to prevent diagonal cross-talk
            if self.active_axis is None:
                if abs(dx) > self.DEADZONE and abs(dx) > abs(dy) * 1.2:
                    self.active_axis = 'horizontal'
                elif abs(dy) > self.DEADZONE and abs(dy) > abs(dx) * 1.2:
                    self.active_axis = 'vertical'

            # --- Horizontal (Left to Right) -> Volume ---
            if self.active_axis == 'horizontal':
                self.vol_accumulator += dx * 30.0
                if abs(self.vol_accumulator) >= 1.0:
                    clicks = int(self.vol_accumulator)
                    self._adjust_volume(clicks)
                    self.vol_accumulator -= clicks
                action = "Volume UP" if dx > 0.002 else ("Volume DOWN" if dx < -0.002 else "Holding Volume")
                status = f"Volume: {'+' if dx > 0 else '-'}"

            # --- Vertical (North to South) -> Screen Brightness ---
            elif self.active_axis == 'vertical':
                self.bright_accumulator += dy * 26.0
                if abs(self.bright_accumulator) >= 1.0:
                    clicks = int(self.bright_accumulator)
                    self._adjust_brightness(clicks)
                    self.bright_accumulator -= clicks
                action = "Brightness UP" if dy > 0.002 else ("Brightness DOWN" if dy < -0.002 else "Holding Brightness")
                status = f"Brightness: {'+' if dy > 0 else '-'}"

            self.prev_dist_x = dist_x
            self.prev_dist_y = dist_y

        else:
            # Pinch released: lock values, reset accumulators and baseline
            self.active_axis = None
            self.prev_dist_x = None
            self.prev_dist_y = None
            self.vol_accumulator = 0.0
            self.bright_accumulator = 0.0

        return {
            "p1": p1,
            "p2": p2,
            "both_pinched": both_pinched,
            "axis": self.active_axis,
            "status": status,
            "action": action
        }

    def reset(self):
        self.active_axis = None
        self.prev_dist_x = None
        self.prev_dist_y = None
        self.vol_accumulator = 0.0
        self.bright_accumulator = 0.0


class MouseController:
    """Controls the mouse cursor using single-hand landmark positions and gestures."""

    def __init__(self, screen_w=None, screen_h=None, smoothing=2):
        detected_w, detected_h = pyautogui.size()
        self.screen_w = screen_w or detected_w
        self.screen_h = screen_h or detected_h
        self.smoothing = max(1, smoothing)

        self.frame_margin = 0.15
        self.x_history = []
        self.y_history = []

        self.left_clicking = False
        self.left_click_time = 0
        self.right_clicking = False
        self.right_click_time = 0

        self.last_scroll_time = 0
        self.last_valid_gesture_time = 0
        self.scroll_accumulator = 0.0
        self.filtered_dy = None
        self.prev_dy = None

        self.MIN_SCROLL_SPEED = 2.5
        self.MAX_SCROLL_SPEED = 26.0

        self.PINCH_CLOSE = 0.07
        self.PINCH_RELEASE = 0.09
        self.CLICK_COOLDOWN = 0.35

        self.debug = {
            "thumb_index_dist": 0.0,
            "thumb_middle_dist": 0.0,
            "pinch_threshold": self.PINCH_CLOSE,
        }

    def _smooth(self, x, y):
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
        mapped_x = (norm_x - self.frame_margin) / (1.0 - 2 * self.frame_margin)
        mapped_y = (norm_y - self.frame_margin) / (1.0 - 2 * self.frame_margin)
        mapped_x = max(0.0, min(1.0, mapped_x))
        mapped_y = max(0.0, min(1.0, mapped_y))

        pixel_x = int(mapped_x * self.screen_w)
        pixel_y = int(mapped_y * self.screen_h)

        pixel_x = max(3, min(self.screen_w - 4, pixel_x))
        pixel_y = max(3, min(self.screen_h - 4, pixel_y))
        return pixel_x, pixel_y

    @staticmethod
    def _distance(lm1, lm2):
        return math.hypot(lm1.x - lm2.x, lm1.y - lm2.y)

    def move_cursor(self, index_tip):
        sx, sy = self._smooth(index_tip.x, index_tip.y)
        screen_x, screen_y = self._map_to_screen(sx, sy)
        try:
            pyautogui.moveTo(screen_x, screen_y, _pause=False)
        except Exception:
            pass

    def check_left_click(self, thumb_tip, index_tip):
        dist = self._distance(thumb_tip, index_tip)
        self.debug["thumb_index_dist"] = dist
        now = time.time()

        if not self.left_clicking:
            if dist < self.PINCH_CLOSE and (now - self.left_click_time) > self.CLICK_COOLDOWN:
                self.left_clicking = True
                self.left_click_time = now
                try:
                    pyautogui.click(_pause=False)
                except Exception:
                    pass
                return "Left Click"
        else:
            if dist > self.PINCH_RELEASE:
                self.left_clicking = False

        return "Holding" if self.left_clicking else None

    def check_right_click(self, thumb_tip, middle_tip):
        dist = self._distance(thumb_tip, middle_tip)
        self.debug["thumb_middle_dist"] = dist
        now = time.time()

        if not self.right_clicking:
            if dist < self.PINCH_CLOSE and (now - self.right_click_time) > self.CLICK_COOLDOWN:
                self.right_clicking = True
                self.right_click_time = now
                try:
                    pyautogui.rightClick(_pause=False)
                except Exception:
                    pass
                return "Right Click"
        else:
            if dist > self.PINCH_RELEASE:
                self.right_clicking = False

        return "Holding R" if self.right_clicking else None

    def handle_scroll(self, landmarks, gesture):
        now = time.time()

        if gesture == "Thumb Neutral":
            self.scroll_accumulator = 0.0
            self.filtered_dy = None
            self.prev_dy = None
            self.last_scroll_time = now
            self.last_valid_gesture_time = now
            return "Scroll: Paused"

        if gesture in ("Thumbs Up", "Thumbs Down"):
            self.last_valid_gesture_time = now
            dt = now - self.last_scroll_time if self.last_scroll_time > 0 else 0.033
            dt = min(0.08, max(0.005, dt))
            self.last_scroll_time = now

            hand_scale = max(0.05, self._distance(landmarks[0], landmarks[9]))
            raw_dy = (landmarks[2].y - landmarks[4].y) / hand_scale
            direction = 1 if gesture == "Thumbs Up" else -1

            if self.filtered_dy is None:
                self.filtered_dy = raw_dy
                self.prev_dy = raw_dy

            self.filtered_dy = self.filtered_dy * 0.65 + raw_dy * 0.35

            tilt_mag = abs(self.filtered_dy)
            deadzone = 0.20
            max_range = 0.85
            norm_tilt = max(0.0, min(1.0, (tilt_mag - deadzone) / (max_range - deadzone)))

            base_speed = self.MIN_SCROLL_SPEED + (norm_tilt ** 2.0) * (self.MAX_SCROLL_SPEED - self.MIN_SCROLL_SPEED)

            twist_vel = (self.filtered_dy - self.prev_dy) / dt
            self.prev_dy = self.filtered_dy

            twist_alignment = twist_vel if direction > 0 else -twist_vel
            twist_boost = max(0.0, twist_alignment) * 15.0

            effective_speed = base_speed + min(20.0, twist_boost)
            self.scroll_accumulator += direction * effective_speed * dt

            if abs(self.scroll_accumulator) >= 1.0:
                clicks = int(self.scroll_accumulator)
                try:
                    pyautogui.scroll(clicks, _pause=False)
                except Exception:
                    pass
                self.scroll_accumulator -= clicks

            speed_label = "Fast" if effective_speed > 13.0 else ("Med" if effective_speed > 5.0 else "Slow")
            return f"Scroll {('Up' if direction > 0 else 'Down')} ({speed_label})"

        if now - self.last_valid_gesture_time < 0.15:
            return "Scrolling..."

        self.scroll_accumulator = 0.0
        self.filtered_dy = None
        self.prev_dy = None
        self.last_scroll_time = 0
        return None

    def update(self, landmarks, gesture):
        if not landmarks or len(landmarks) < 21:
            return "No hand"

        if gesture in ("Thumbs Up", "Thumbs Down", "Thumb Neutral") or (time.time() - self.last_valid_gesture_time < 0.15):
            scroll_status = self.handle_scroll(landmarks, gesture)
            if scroll_status:
                return scroll_status

        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        left = self.check_left_click(thumb_tip, index_tip)
        right = self.check_right_click(thumb_tip, middle_tip)

        if left and left != "Holding":
            return left
        if right and right != "Holding":
            return right

        if self.left_clicking or self.right_clicking:
            return "L-Click Hold" if self.left_clicking else "R-Click Hold"

        self.move_cursor(index_tip)
        return "Moving"

    def reset(self):
        self.x_history.clear()
        self.y_history.clear()
        self.left_clicking = False
        self.right_clicking = False
        self.scroll_accumulator = 0.0
        self.filtered_dy = None
        self.prev_dy = None
        self.last_scroll_time = 0
        self.last_valid_gesture_time = 0