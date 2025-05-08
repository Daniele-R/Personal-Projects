import winreg                          # Used to interact with the Windows Registry
import ctypes                          # Allows GUI interaction and system calls
import subprocess                      # Used to execute system-level commands like killing processes
import os                              # Provides OS utilities

import restart                         # Custom module, used here to get the EXE path

# Function to clean up traces of the script
# Removes from startup, kills processes, deletes the EXE and script itself, then exits

def clean_up(name="RSCAD"):
    # Step 1: Remove startup entry from Windows Registry
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, name)                       # Try to delete the registry value
        winreg.CloseKey(key)                                # Close the key after modifying
        print(f"[INFO] Startup entry '{name}' removed.")
    except FileNotFoundError:
        print(f"[INFO] Startup entry '{name}' not found.")  # Entry didn't exist
    except Exception as e:
        print(f"[ERROR] Could not remove startup entry: {e}")

    # Step 2: Kill related processes
    procs_to_kill = [
        os.path.basename(restart.EXE_PATH),                 # The main executable file name
        "RSCAD.exe",                                        # Backup name in case EXE_PATH was renamed
        "python.exe"                                        # Catch-all in case the script is running via Python
    ]
    for proc_name in procs_to_kill:
        try:
            subprocess.call(
                ["taskkill", "/F", "/IM", proc_name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print(f"[INFO] taskkill issued for {proc_name}")
        except Exception as e:
            print(f"[WARNING] Could not taskkill {proc_name}: {e}")

    # Step 3: Delete the bundled executable if it exists
    exe_path = restart.EXE_PATH
    try:
        if os.path.exists(exe_path):
            os.remove(exe_path)                             # Remove EXE from disk
            print(f"[INFO] Deleted executable: {exe_path}")
    except Exception as e:
        print(f"[WARNING] Could not delete executable: {e}")

    # Step 4: Delete this Python script file itself
    py_path = os.path.abspath(__file__)
    try:
        os.remove(py_path)                                  # Self-delete the .py file
        print(f"[INFO] Deleted script file: {py_path}")
    except Exception as e:
        print(f"[WARNING] Could not delete script file: {e}")

    # Step 5: Show a message and terminate immediately
    ctypes.windll.user32.MessageBoxW(
        0,
        "Cleanup complete. All traces removed.",
        "Cleanup",
        0x40 | 0x1
    )
    os._exit(0)                                             # Exit the program immediately