import pyautogui
import os
from datetime import datetime

def scroll_up():
    """Scroll up in the active window."""
    pyautogui.scroll(100)

def scroll_down():
    """Scroll down in the active window."""
    pyautogui.scroll(-100)

def left_click():
    """Perform a left mouse click."""
    pyautogui.click()

def move_cursor(x, y):
    """Move cursor to specified coordinates."""
    pyautogui.moveTo(x, y)

def take_screenshot():
    """Take a screenshot and save it to the project's screenshots directory."""
    # Go up one level from src to the project root, then into screenshots
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    screenshots_dir = os.path.join(project_root, "screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
    
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        # Return just the filename for a cleaner log message
        return f"Screenshot saved: {os.path.basename(filename)}"
    except Exception as e:
        return f"Error taking screenshot: {e}"