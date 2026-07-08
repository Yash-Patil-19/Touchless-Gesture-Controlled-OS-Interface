import cv2
import time
import math
from hand_tracking import HandTracker
from gestures import is_fist, PalmTimer, is_pinch, control_cursor, volume_control_gesture
from actions import scroll_up, scroll_down, take_screenshot
import numpy as np
import os
from datetime import datetime

try:
    import pyautogui as pag
except Exception:
    pag = None

# Cooldown and threshold settings
SCROLL_DELAY = 0.2  
PINCH_THRESHOLD = 0.05
PINCH_VIS_RADIUS = 18
PINCH_COOLDOWN = 0.5 
SCREENSHOT_COOLDOWN = 2.0

def main():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    palm_timer = PalmTimer(timeout_seconds=5)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    window_name = 'Webcam'
    cv2.namedWindow(window_name)
    last_scroll_time = 0
    prev_x, prev_y = 0, 0
    log_message = ""

    last_pinch_state = {}  
    last_click_time = {}    
    last_screenshot_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, hand_data = tracker.find_hands(frame)
        h, w, _ = frame.shape

        if not hand_data:
            palm_timer.reset()
        else:
            current_time = time.time()
            
            # --- Two-Hand Screenshot Gesture ---
            if len(hand_data) == 2:
                hand1, hand2 = hand_data[0], hand_data[1]
                pinched1, _ = is_pinch(hand1['landmarks'], threshold=PINCH_THRESHOLD)
                pinched2, _ = is_pinch(hand2['landmarks'], threshold=PINCH_THRESHOLD)

                if pinched1 and pinched2:
                    if current_time - last_screenshot_time > SCREENSHOT_COOLDOWN:
                        log_message = take_screenshot()
                        last_screenshot_time = current_time
                    
                    if "Screenshot" in log_message:
                        cv2.putText(frame, log_message, (10, frame.shape[0]-40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                        cv2.imshow(window_name, frame)
                        if cv2.waitKey(1) & 0xFF == 27:
                            break
                        continue

            # --- Single-Hand Gestures ---
            prev_x, prev_y = control_cursor(hand_data[0]['landmarks'], prev_x, prev_y)

            # --- Click  ---
            for hand in hand_data:
                landmarks = hand['landmarks']
                label = hand.get('label', 'Unknown')

                if label not in last_pinch_state:
                    last_pinch_state[label] = False
                if label not in last_click_time:
                    last_click_time[label] = 0.0

                pinched, index_lm = is_pinch(landmarks, threshold=PINCH_THRESHOLD)

                if pinched and not last_pinch_state[label]:
                    if (current_time - last_click_time[label]) >= PINCH_COOLDOWN:
                        last_click_time[label] = current_time
                        button = 'left' if label.lower().startswith('left') else 'right'
                        log_message = f"{label} hand: Pinch -> {button} click"

                        if pag:
                            try:
                                sx, sy = pag.position()
                                pag.click(x=sx, y=sy, button=button)
                                if index_lm:
                                    cx, cy = int(index_lm.x * w), int(index_lm.y * h)
                                    cv2.circle(frame, (cx, cy), PINCH_VIS_RADIUS, (0, 0, 255), -1)
                            except Exception as e:
                                print(f"Warning: OS click failed: {e}")
                
                last_pinch_state[label] = bool(pinched)

            hand = hand_data[0]
            landmarks = hand['landmarks']
            label = hand['label']

            # --- Palm Exit ---
            if palm_timer.update(landmarks):
                break

            elapsed = palm_timer.get_elapsed_time()
            if elapsed > 0:
                log_message = f"Hold palm to exit: {5 - elapsed:.1f}s"
            else:
                # --- Scroll Gesture ---
                if current_time - last_scroll_time > SCROLL_DELAY:
                    if is_fist(landmarks):
                        if label == "Left":
                            scroll_up()
                            log_message = "Scroll Up"
                            last_scroll_time = current_time
                        elif label == "Right":
                            scroll_down()
                            log_message = "Scroll Down"
                            last_scroll_time = current_time

                # --- Volume Control ---
                gesture_result = volume_control_gesture(landmarks, label)
                if gesture_result:
                    log_message = gesture_result

        # log message
        if log_message:
            cv2.putText(frame, log_message, (10, frame.shape[0]-40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.imshow(window_name, frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
