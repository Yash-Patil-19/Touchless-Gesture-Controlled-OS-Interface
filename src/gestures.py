import mediapipe as mp
import time
import pyautogui as pag
import numpy as np
import math

mp_hands = mp.solutions.hands

# ------------------- Fist / Open Palm / Peace Sign -------------------

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
    for tip, mcp in zip(tips, mcps):
        if landmarks[tip].y > landmarks[mcp].y:
            return False

    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    return abs(thumb_tip.x - thumb_mcp.x) >= 0.04

def is_peace_sign(landmarks):
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

# ------------------- Palm Timer -------------------

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
        return time.time() - self.start_time if self.is_timing and self.start_time else 0

# ------------------- Cursor Control -------------------

def control_cursor(landmarks, prev_x, prev_y, smoothing=5, margin=0.01):
    INDEX_TIP = 8
    INDEX_PIP = 6
    SCREEN_WIDTH, SCREEN_HEIGHT = pag.size()
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

        pag.moveTo(curr_x, curr_y)
        return curr_x, curr_y

    return prev_x, prev_y

# ------------------- VOLUME CONTROL USING PINKY -------------------

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

    pinky_tip = landmarks[PINKY_TIP]
    pinky_pip = landmarks[PINKY_PIP]
    pinky_up = pinky_tip.y < pinky_pip.y - 0.03

    if pinky_up:
        last_volume_time = current_time

        if hand_label == "Right":
            pag.press("volumeup")
            return "Right Hand Pinky Up - Volume Up"

        elif hand_label == "Left":
            pag.press("volumedown")
            return "Left Hand Pinky Up - Volume Down"

    return None
