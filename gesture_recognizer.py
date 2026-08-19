"""
Gesture Recognizer Module
Classifies hand gestures based on MediaPipe hand landmarks.
Uses the new MediaPipe Tasks API (v1.0+).
"""


class GestureRecognizer:
    """Recognizes hand gestures from MediaPipe HandLandmarker results."""

    # MediaPipe landmark indices
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
        """Initialize the GestureRecognizer."""
        pass

    def recognize(self, landmarks, handedness_label):
        """
        Recognize a gesture based on hand landmarks.

        Args:
            landmarks: List of NormalizedLandmark objects from MediaPipe HandLandmarker.
                       Each landmark has .x, .y, .z attributes.
            handedness_label: String — "Left" or "Right".

        Returns:
            str: The name of the recognized gesture.
        """
        if not landmarks or len(landmarks) < 21:
            return "None"

        # Shorthand access
        lm = landmarks

        is_right = handedness_label == "Right"

        # --- Determine if each finger is extended ---

        # Thumb: compare tip.x to ip.x (horizontal extension)
        # Note: In a selfie/flipped view, right-hand thumb extends left (lower x)
        if is_right:
            thumb_ext = lm[self.THUMB_TIP].x < lm[self.THUMB_IP].x
        else:
            thumb_ext = lm[self.THUMB_TIP].x > lm[self.THUMB_IP].x

        # Other fingers: tip.y < pip.y means extended (y increases downward)
        index_ext = lm[self.INDEX_TIP].y < lm[self.INDEX_PIP].y
        middle_ext = lm[self.MIDDLE_TIP].y < lm[self.MIDDLE_PIP].y
        ring_ext = lm[self.RING_TIP].y < lm[self.RING_PIP].y
        pinky_ext = lm[self.PINKY_TIP].y < lm[self.PINKY_PIP].y

        # Are all 4 non-thumb fingers curled?
        four_curled = not (index_ext or middle_ext or ring_ext or pinky_ext)

        # --- Gesture classification ---

        # Fist / Thumbs Up / Thumbs Down (all 4 fingers curled)
        if four_curled:
            thumb_tip_y = lm[self.THUMB_TIP].y
            thumb_mcp_y = lm[self.THUMB_MCP].y

            if thumb_tip_y < thumb_mcp_y - 0.05:
                return "Thumbs Up"
            elif thumb_tip_y > thumb_mcp_y + 0.05:
                return "Thumbs Down"
            else:
                return "Fist"

        # Open Palm (all 5 fingers extended)
        if index_ext and middle_ext and ring_ext and pinky_ext:
            return "Open Palm"

        # Peace Sign / Victory (index + middle extended, ring + pinky curled)
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            return "Peace Sign"

        # Pointing (only index extended)
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return "Pointing"

        return "Unknown"
