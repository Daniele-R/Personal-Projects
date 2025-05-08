import os                          # Provides access to OS-level operations like killing processes
import subprocess                  # Used to run and control system processes
import time                        # Time-related functions like sleep
import threading                   # Enables running code in parallel using threads
import keyboard                    # External module for handling keyboard input
import ctypes                      # For Windows-specific GUI calls

EXE_PATH = r"C:\Users\danie\OneDrive\Desktop\SDP\RSCAD.exe"                  # Path to main executable
CHECK_INTERVAL = 2  # Interval in seconds for checking if the main process is running

# Hotkey-triggered function to kill the EXE, clean startup, and exit

def manual_kill():
    import startup_delete

    proc_name = os.path.basename(EXE_PATH)                                          # Extract just the file name from the path
    try:
        subprocess.call(
            ["taskkill", "/F", "/IM", proc_name],                                   # Force kill the main executable
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"[WATCHDOG] Killed process: {proc_name}")
    except Exception as e:
        print(f"[WATCHDOG][WARNING] Could not taskkill {proc_name}: {e}")

    try:
        startup_delete.remove_from_startup(name="RSCAD")                            # Remove from registry startup
        print("[WATCHDOG] Removed startup entry")
    except Exception as e:
        print(f"[WATCHDOG][WARNING] Could not remove startup entry: {e}")

    ctypes.windll.user32.MessageBoxW(                                               # Show a shutdown message box
        0,
        "Manual shutdown: all traces removed.",
        "Watchdog",
        0x40 | 0x1
    )
    os._exit(0)                                                                     # Exit immediately

# Function to check if a process with a given name is running using 'tasklist'
def is_process_running(exe_name: str) -> bool:
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        lines = output.splitlines()
        return any(exe_name.lower() in line.lower() for line in lines[3:])          # Skip header lines
    except Exception:
        return False

# Function to start the main executable in the background, no visible window

def launch_main():
    try:
        subprocess.Popen(
            [EXE_PATH],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        )
        print(f"[WATCHDOG] Launched {EXE_PATH}")
    except Exception as e:
        print(f"[WATCHDOG][ERROR] Could not launch main exe: {e}")

# Core watchdog loop that ensures the main executable stays running

def watchdog_loop():
    exe_name = os.path.basename(EXE_PATH)                                           # Get the executable name from the full path
    last_seen = False                                                               # Track if it was seen running last check

    while True:
        running = is_process_running(exe_name)
        if not running and not last_seen:
            launch_main()                                                           # Restart if not running
        last_seen = running
        time.sleep(CHECK_INTERVAL)                                                  # Wait before checking again

# Start a listener thread for hotkey Ctrl+Alt+K to trigger manual kill

def start_manual_kill_listener():
    keyboard.add_hotkey("ctrl+alt+k", manual_kill)
    print("[WATCHDOG] Manual kill hotkey registered: Ctrl+Alt+K")

# Main entry point for the script
if __name__ == "__main__":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)   # Hide the console window
    launch_main()                                                                   # Launch main app once
    threading.Thread(target=start_manual_kill_listener, daemon=True).start()        # Start hotkey listener thread
    watchdog_loop()                                                                 # Begin monitoring loop