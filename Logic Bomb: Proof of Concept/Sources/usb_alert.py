import win32com.client                # Provides access to Windows Management Instrumentation (WMI)
import time                           # Used for timing and cooldown between USB events
import ctypes                         # Used to call Windows native functions, e.g., message boxes
import action                         # Custom module that modifies .dtp files and performs cleanup

# Initializes a WMI watcher to detect USB insertions

def create_usb_watcher():
    print("USB watcher initialized.")
    wmi = win32com.client.GetObject("winmgmts:")            # Connect to the WMI service
    watcher = wmi.ExecNotificationQuery(
        "SELECT * FROM __InstanceCreationEvent WITHIN 2 WHERE TargetInstance ISA 'Win32_USBControllerDevice'"
    )                                                       # Listen for new USB devices every 2 seconds
    return watcher

# Detects a new USB insertion and triggers a response if the cooldown time has passed

def usb_detection(watcher, last_event_time, cooldown=3):
    event = watcher.NextEvent()                             # This call blocks until a USB device is inserted
    now = time.time()                                       # Current timestamp

    if now - last_event_time > cooldown:                    # Check if cooldown has passed
        ctypes.windll.user32.MessageBoxW(                   # Display a popup notification
            0,
            "RTDS Detected!",
            "USB Notification",
            0x40 | 0x1
        )
        print("USB event handled. Notification shown.")
        action.my_custom_function()                         # Call the core logic to modify and clean
        return now                                          # Update last event time
    else:
        print("Duplicate USB event ignored.")
        return last_event_time                              # Return previous timestamp if cooldown not met