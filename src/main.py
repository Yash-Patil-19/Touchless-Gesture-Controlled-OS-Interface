import cv2
import time
import math
from hand_tracking import HandTracker
from gestures import get_scroll_direction, PalmTimer, is_pinch, control_cursor, volume_control_gesture
from actions import scroll_up, scroll_down
import numpy as np

# optional OS click library
try:
    import pyautogui as pag
except Exception:
    pag = None

# Cooldown and threshold settings
SCROLL_DELAY = 0.2  # 200 milliseconds
PINCH_THRESHOLD = 0.05
PINCH_VIS_RADIUS = 18
PINCH_COOLDOWN = 0.5  # seconds between clicks per hand

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
    log_message = ""
    prev_x, prev_y = 0, 0

    # Per-hand state for pinch clicks
    last_pinch_state = {}   # e.g. {'Left': False, 'Right': False}
    last_click_time = {}    # e.g. {'Left': 0.0, 'Right': 0.0}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        frame, hand_data = tracker.find_hands(frame)
        h, w, _ = frame.shape

        if not hand_data:
            log_message = "No hands detected. Place your hands in front of the camera."
            palm_timer.reset()
        else:
            current_time = time.time()
            
            # --- Cursor Control (uses first hand) ---
            # Run this first to allow cursor movement while other gestures are checked
            prev_x, prev_y = control_cursor(hand_data[0]['landmarks'], prev_x, prev_y)

            # --- Pinch-to-Click (handles all detected hands) ---
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

            # --- Other Gestures (use first detected hand) ---
            hand = hand_data[0]
            landmarks = hand['landmarks']
            label = hand['label']

            # --- Palm Exit ---
            if palm_timer.update(landmarks):
                log_message = "Open palm held for 5 seconds. Exiting..."
                cv2.putText(frame, log_message, (10, frame.shape[0] - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.imshow(window_name, frame)
                cv2.waitKey(2000)
                break

            elapsed = palm_timer.get_elapsed_time()
            if elapsed > 0:
                remaining = 5 - elapsed
                log_message = f"Hold palm to exit: {remaining:.1f}s remaining"
            else:
                # --- Scroll Gesture ---
                if current_time - last_scroll_time > SCROLL_DELAY:
                    scroll_direction = get_scroll_direction(landmarks)
                    if scroll_direction == 'up':
                        scroll_up()
                        log_message = f"{label} hand: Peace Sign - Scroll Up"
                        last_scroll_time = current_time
                    elif scroll_direction == 'down':
                        scroll_down()
                        log_message = f"{label} hand: Peace Sign - Scroll Down"
                        last_scroll_time = current_time

                # --- Volume Control ---
                gesture_result = volume_control_gesture(landmarks, label)
                if gesture_result:
                    log_message = gesture_result

        # Overlay log message
        if log_message:
            cv2.putText(frame, log_message, (10, frame.shape[0] - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("To close the webcam, press the 'Esc' key.")
            break

        if key == 27:  # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
