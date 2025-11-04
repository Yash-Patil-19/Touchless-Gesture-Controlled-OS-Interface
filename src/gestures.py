import mediapipe as mp
import time
import pyautogui
import numpy as np
import math

mp_hands = mp.solutions.hands

# ------------------- Existing Hand Gesture Functions -------------------

def is_fist(landmarks):
    """Return True if the hand is a closed fist."""
    if not landmarks:
        return False
    tips = [8, 12, 16, 20]
    mcps = [5, 9, 13, 17]
    for tip, mcp in zip(tips, mcps):
        if landmarks[tip].y < landmarks[mcp].y:
            return False
    return True

def is_open_palm(landmarks):
    """Return True if all fingers (including thumb) are extended."""
    if not landmarks:
        return False
    tips = [8, 12, 16, 20]
    mcps = [5, 9, 13, 17]
    for tip, mcp in zip(tips, mcps):
        if landmarks[tip].y > landmarks[mcp].y:
            return False
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    return abs(thumb_tip.x - thumb_mcp.x) >= 0.04

def is_peace_sign(landmarks):
    """Return True if index & middle fingers are extended and others folded."""
    if not landmarks:
        return False

    def distance(p1, p2):
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    idx_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    idx_pip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP]
    mid_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    mid_pip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    ring_mcp = landmarks[mp_hands.HandLandmark.RING_FINGER_MCP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    pinky_mcp = landmarks[mp_hands.HandLandmark.PINKY_MCP]

    index_extended = distance(idx_tip, idx_pip) > 0.04
    middle_extended = distance(mid_tip, mid_pip) > 0.04
    ring_folded = distance(ring_tip, ring_mcp) < 0.06
    pinky_folded = distance(pinky_tip, pinky_mcp) < 0.06

    return index_extended and middle_extended and ring_folded and pinky_folded

def get_scroll_direction(landmarks):
    """Return 'up', 'down', or None based on peace sign orientation."""
    if not is_peace_sign(landmarks):
        return None
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    idx_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    mid_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    avg_y = (idx_tip.y + mid_tip.y) / 2
    if avg_y < wrist.y - 0.05:
        return 'up'
    elif avg_y > wrist.y + 0.05:
        return 'down'
    return None

# ------------------- Palm Timer Class -------------------

class PalmTimer:
    """Track how long an open palm gesture is sustained."""
    def __init__(self, timeout_seconds=5):
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        self.is_timing = False

    def update(self, landmarks):
        if is_open_palm(landmarks):
            if not self.is_timing:
                self.start_time = time.time()
                self.is_timing = True
            else:
                if time.time() - self.start_time >= self.timeout_seconds:
                    return True
        else:
            self.reset()
        return False

    def reset(self):
        self.start_time = None
        self.is_timing = False

    def get_elapsed_time(self):
        return time.time() - self.start_time if self.is_timing and self.start_time else 0

# ------------------- Cursor Control -------------------

def control_cursor(landmarks, prev_x, prev_y, smoothing=5, margin=0.01):
    """Move the system cursor following index fingertip when raised."""
    INDEX_TIP = 8
    INDEX_PIP = 6
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
    CAM_WIDTH, CAM_HEIGHT = 640, 480

    def is_index_active(lm):
        return lm[INDEX_TIP].y < lm[INDEX_PIP].y - margin

    if is_index_active(landmarks):
        tip = landmarks[INDEX_TIP]
        cam_x = int(tip.x * CAM_WIDTH)
        cam_y = int(tip.y * CAM_HEIGHT)

        screen_x = np.interp(cam_x, [0, CAM_WIDTH], [0, SCREEN_WIDTH])
        screen_y = np.interp(cam_y, [0, CAM_HEIGHT], [0, SCREEN_HEIGHT])

        curr_x = prev_x + (screen_x - prev_x) / smoothing
        curr_y = prev_y + (screen_y - prev_y) / smoothing

        pyautogui.moveTo(curr_x, curr_y)
        return curr_x, curr_y

    return prev_x, prev_y

# ------------------- Volume Control Gestures -------------------

import pyautogui
import time

last_volume_time = 0
VOLUME_COOLDOWN = 0.2  # seconds

def volume_control_gesture(landmarks, hand_label):
    """
    Strict Volume Control with hand labels:
    - Volume Up: Right hand, Thumb + Index fingers up
    - Volume Down: Left hand, Thumb + Index fingers up
    """

    global last_volume_time
    current_time = time.time()
    if current_time - last_volume_time < VOLUME_COOLDOWN:
        return None  # prevent rapid repeats

    if not landmarks or hand_label not in ["Left", "Right"]:
        return None

    tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    pips = [2, 6, 10, 14, 18]

    margin = 0.04  # increase margin for better accuracy
    fingers_up = [landmarks[tip].y < landmarks[pip].y - margin for tip, pip in zip(tips, pips)]

    # ------------------- Volume Up (Right Hand) -------------------
    if hand_label == "Right" and fingers_up[0] and fingers_up[1] and not any(fingers_up[2:]):
        pyautogui.press("volumeup")
        last_volume_time = current_time
        return "Volume Up"

    # ------------------- Volume Down (Left Hand) -------------------
    if hand_label == "Left" and fingers_up[0] and fingers_up[1] and not any(fingers_up[2:]):
        pyautogui.press("volumedown")
        last_volume_time = current_time
        return "Volume Down"

    return None




