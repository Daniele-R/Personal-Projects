import keyboard                # External module for capturing keyboard events
import ctypes                  # Allows calling functions in DLLs or shared libraries
import os                      # OS module for terminating the script

# Function to register a hotkey that will trigger script termination

def listen_for_exit():
    print("[INFO] Exit hotkey listener active (Ctrl+Alt+x)")
    # Bind Ctrl+Alt+X to the kill_script function
    keyboard.add_hotkey('ctrl+alt+x', kill_script)


# Function that gets called when the hotkey is pressed
# Shows a message box and terminates the script immediately

def kill_script():
    ctypes.windll.user32.MessageBoxW(                   # Display a Windows message box
        0,
        "USB Detector Stopped by User",                 # Message
        "Exit Notification",                            # Title
        0x40 | 0x1                                      # Icon type and buttons
    )
    print("[INFO] Script manually terminated by hotkey.")
    os._exit(0)                                         # Forcefully and immediately exits the Python interpreter