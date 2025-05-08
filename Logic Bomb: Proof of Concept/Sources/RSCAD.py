import time                            # Provides time-related functions (e.g., sleep, timestamps)
import threading                       # Enables concurrent execution via threads

import proxy                           # Custom module to disable system proxy
import usb_alert                       # Custom module to monitor USB plug-in events
import killing                         # Custom module to allow manual termination via hotkey
import hidden                          # Custom module to add the script to Windows startup

# Main logic of the script starts here
if __name__ == "__main__":
    proxy.disable_proxy()                                   # Disable proxy settings to prevent interference
    hidden.add_to_startup(hidden.get_self_exe_path())       # Add this script to system startup registry

    # Start a background thread to listen for Ctrl+Alt+X for manual termination
    listen_thread = threading.Thread(target=killing.listen_for_exit, daemon=True)
    listen_thread.start()

    # Create a USB event watcher using WMI
    watcher = usb_alert.create_usb_watcher()
    last_event_time = 0                                     # Initialize the timestamp of the last event

    # Begin monitoring loop
    while True:
        try:
            # Wait for and handle the next USB event
            last_event_time = usb_alert.usb_detection(watcher, last_event_time)
        except KeyboardInterrupt:
            print("Script manually stopped.")               # Graceful shutdown on Ctrl+C
            break
        except Exception as e:
            print(f"[ERROR] {e}")                           # Handle unexpected errors gracefully
            time.sleep(1)                                   # Wait before retrying
