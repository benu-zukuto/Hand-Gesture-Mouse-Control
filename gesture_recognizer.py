"""
Gesture Recognizer Module
Classifies hand gestures using scale- and rotation-invariant geometry.
Uses MediaPipe Tasks API (v1.0+).
"""

import math


class GestureRecognizer:
    """Recognizes hand gestures from MediaPipe HandLandmarker results."""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(self):
        pass

    @staticmethod
    def _dist(p1, p2):
        """Calculate 2D Euclidean distance between two landmark points."""
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def recognize(self, landmarks, handedness_label):
        """
        Recognize hand gesture based on 21 hand landmarks.

        Args:
            landmarks: List of NormalizedLandmark objects.
            handedness_label: String — "Left" or "Right".

        Returns:
            str: The recognized gesture name.
        """
        if not landmarks or len(landmarks) < 21:
            return "None"

        lm = landmarks

        # Measure palm scale (wrist to middle knuckle) for camera-distance invariance
        hand_scale = self._dist(lm[self.WRIST], lm[self.MIDDLE_MCP])
        if hand_scale < 0.01:
            return "None"

        # Rotation-invariant finger extension:
        # A curled finger's tip moves closer to the wrist than its PIP knuckle,
        # regardless of whether the hand is pointing up, down, or sideways.
        index_ext = self._dist(lm[self.INDEX_TIP], lm[self.WRIST]) > self._dist(lm[self.INDEX_PIP], lm[self.WRIST])
        middle_ext = self._dist(lm[self.MIDDLE_TIP], lm[self.WRIST]) > self._dist(lm[self.MIDDLE_PIP], lm[self.WRIST])
        ring_ext = self._dist(lm[self.RING_TIP], lm[self.WRIST]) > self._dist(lm[self.RING_PIP], lm[self.WRIST])
        pinky_ext = self._dist(lm[self.PINKY_TIP], lm[self.WRIST]) > self._dist(lm[self.PINKY_PIP], lm[self.WRIST])

        four_curled = not (index_ext or middle_ext or ring_ext or pinky_ext)

        # --- Thumb Scroll Postures (All 4 fingers curled) ---
        if four_curled:
            # Measure vertical difference scaled to hand size
            vert_diff = lm[self.THUMB_MCP].y - lm[self.THUMB_TIP].y
            tilt_threshold = 0.22 * hand_scale

            if vert_diff > tilt_threshold:
                return "Thumbs Up"
            elif vert_diff < -tilt_threshold:
                return "Thumbs Down"
            else:
                return "Thumb Neutral"

        # Open Palm
        if index_ext and middle_ext and ring_ext and pinky_ext:
            return "Open Palm"

        # Pointing (Index extended, remaining fingers curled)
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return "Pointing"

        return "Unknown"