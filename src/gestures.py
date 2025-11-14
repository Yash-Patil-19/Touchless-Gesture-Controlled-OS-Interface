import mediapipe as mp
import time
import pyautogui as pag
import numpy as np
import math

mp_hands = mp.solutions.hands

# -------------------------------------------------------
# FIST / OPEN PALM / PEACE SIGN
# -------------------------------------------------------

def is_fist(landmarks):
    if not landmarks:
        return False
    tips = [8, 12, 16, 20]
    mcps = [5, 9, 13, 17]
    for tip, mcp in zip(tips, mcps):
        if landmarks[tip].y < landmarks[mcp].y:
            return False
    return True


def is_open_palm(landmarks):
    if not landmarks:
        return False
    tips = [8, 12, 16, 20]
    mcps = [5, 9, 13, 17]

    # Fingers extended
    for tip, mcp in zip(tips, mcps):
        if landmarks[tip].y > landmarks[mcp].y:
            return False

    # Thumb slightly open
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    return abs(thumb_tip.x - thumb_mcp.x) >= 0.03


def is_peace_sign(landmarks):
    if not landmarks:
        return False

    def distance(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    idx_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    idx_pip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP]

    mid_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    mid_pip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]

    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    ring_mcp = landmarks[mp_hands.HandLandmark.RING_FINGER_MCP]

    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    pinky_mcp = landmarks[mp_hands.HandLandmark.PINKY_MCP]

    # --- FIXED threshold (was 0.04 -> too strict)
    index_extended = distance(idx_tip, idx_pip) > 0.03
    middle_extended = distance(mid_tip, mid_pip) > 0.03

    ring_folded = distance(ring_tip, ring_mcp) < 0.06
    pinky_folded = distance(pinky_tip, pinky_mcp) < 0.06

    return index_extended and middle_extended and ring_folded and pinky_folded


# -------------------------------------------------------
# SCROLL DIRECTION
# -------------------------------------------------------

def get_scroll_direction(landmarks):
    if not is_peace_sign(landmarks):
        return None

    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    idx_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    mid_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

    avg_y = (idx_tip.y + mid_tip.y) / 2

    # --- FIXED thresholds ---
    # Peace finger up → avg_y smaller than wrist.y
    # Peace finger down → avg_y larger than wrist.y
    if avg_y < wrist.y - 0.02:
        return "up"
    elif avg_y > wrist.y + 0.02:
        return "down"

    return None


# -------------------------------------------------------
# PALM TIMER
# -------------------------------------------------------

class PalmTimer:
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
        return time.time() - self.start_time if self.is_timing else 0


# -------------------------------------------------------
# PINCH
# -------------------------------------------------------

def is_pinch(landmarks, threshold=0.05):
    if not landmarks:
        return False, None

    thumb = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]

    dist = math.hypot(thumb.x - index.x, thumb.y - index.y)

    return (dist < threshold), index


# -------------------------------------------------------
# CURSOR CONTROL
# -------------------------------------------------------

def control_cursor(landmarks, prev_x, prev_y, smoothing=5, margin=0.01):
    INDEX_TIP = 8
    INDEX_PIP = 6
    SCREEN_WIDTH, SCREEN_HEIGHT = pag.size()
    CAM_WIDTH, CAM_HEIGHT = 640, 480

    def active(lm):
        return lm[INDEX_TIP].y < lm[INDEX_PIP].y - margin

    if active(landmarks):
        tip = landmarks[INDEX_TIP]
        cx = int(tip.x * CAM_WIDTH)
        cy = int(tip.y * CAM_HEIGHT)

        sx = np.interp(cx, [0, CAM_WIDTH], [0, SCREEN_WIDTH])
        sy = np.interp(cy, [0, CAM_HEIGHT], [0, SCREEN_HEIGHT])

        new_x = prev_x + (sx - prev_x) / smoothing
        new_y = prev_y + (sy - prev_y) / smoothing

        pag.moveTo(new_x, new_y)
        return new_x, new_y

    return prev_x, prev_y


# -------------------------------------------------------
# VOLUME CONTROL
# -------------------------------------------------------

last_volume_time = 0
VOLUME_COOLDOWN = 0.3

def volume_control_gesture(landmarks, hand_label):
    global last_volume_time
    current_time = time.time()

    if current_time - last_volume_time < VOLUME_COOLDOWN:
        return None

    if not landmarks:
        return None

    PINKY_TIP = mp_hands.HandLandmark.PINKY_TIP
    PINKY_PIP = mp_hands.HandLandmark.PINKY_PIP

    tip = landmarks[PINKY_TIP]
    pip = landmarks[PINKY_PIP]

    pinky_up = tip.y < pip.y - 0.03

    if pinky_up:
        last_volume_time = current_time

        if hand_label == "Right":
            pag.press("volumeup")
            return "Volume Up"
        elif hand_label == "Left":
            pag.press("volumedown")
            return "Volume Down"

    return None
