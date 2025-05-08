import winreg                # Access Windows Registry
import os                    # Provides OS-related utilities
import sys                   # Access system-specific parameters and functions

# Function to get the path of the current executable or script
# If the script is bundled (e.g., using PyInstaller), return the path to the .exe
# Otherwise, return the path to the .py file

def get_self_exe_path():
    if getattr(sys, 'frozen', False):                           # Checks if the script is running as a bundled executable
        return os.path.abspath(sys.executable)                  # Returns the absolute path to the .exe
    else:
        print(f"Fallback as this is running as .py")
        return os.path.abspath(__file__)                        # Returns the absolute path to the script file


# Adds the script or executable to the Windows startup registry so it runs on boot
# 'name' is the name of the registry entry

def add_to_startup(exe_path=None, name="RSCAD"):                # Default name for the registry entry
    if exe_path is None:
        exe_path = get_self_exe_path()                          # Determine the executable path if not provided

    # Open the Windows registry key for current user startup programs
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)

    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, exe_path)    # Set the startup path
    winreg.CloseKey(key)                                        # Close the registry key
    print(f"[INFO] Startup entry added: {name} → {exe_path}")