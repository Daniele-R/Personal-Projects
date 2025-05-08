import winreg                           # Provides access to the Windows Registry API

# Function to disable proxy settings for the current user

def disable_proxy():
    try:
        # Open the Internet Settings registry key with write access
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            0,
            winreg.KEY_SET_VALUE
        )

        # Set 'ProxyEnable' to 0 to disable the proxy
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)

        # Optionally delete the proxy server address if it exists
        winreg.DeleteValue(key, "ProxyServer")

        winreg.CloseKey(key)            # Always close registry key when done
        print("[INFO] Proxy disabled.")

    except Exception as e:
        # Handle and display any errors that occur while editing the registry
        print(f"[WARNING] Could not disable proxy: {e}")
