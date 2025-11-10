import cv2
import time
import math
import os
from datetime import datetime
from hand_tracking import HandTracker
from gestures import control_cursor, get_scroll_direction, PalmTimer, volume_control_gesture
from actions import scroll_up, scroll_down

try:
    import pyautogui as pag
except Exception:
    pag = None

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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, hand_data = tracker.find_hands(frame)

        if not hand_data:
            log_message = "No hands detected"
            palm_timer.reset()
        else:
            hand = hand_data[0]
            landmarks = hand['landmarks']
            label = hand['label']
            current_time = time.time()

            if palm_timer.update(landmarks):
                break

            elapsed = palm_timer.get_elapsed_time()
            if elapsed > 0:
                log_message = f"Hold palm to exit: {5 - elapsed:.1f}s"
            else:
                if current_time - last_scroll_time > SCROLL_DELAY:
                    direction = get_scroll_direction(landmarks)
                    if direction == "up":
                        scroll_up()
                        log_message = "Scroll Up"
                        last_scroll_time = current_time
                    elif direction == "down":
                        scroll_down()
                        log_message = "Scroll Down"
                        last_scroll_time = current_time

                gesture_result = volume_control_gesture(landmarks, label)
                if gesture_result:
                    log_message = gesture_result

            prev_x, prev_y = control_cursor(landmarks, prev_x, prev_y)

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
