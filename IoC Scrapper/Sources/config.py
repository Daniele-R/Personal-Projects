from __future__ import annotations                                  # Maybe for future references and/or compatibility
import os
from typing import Optional                                         # Same as union, pretty much if it doesnt retun something recognizable, returns none

CONFIG_FILE = "config.toml"
                                                                    
def _load_from_toml(path: str = CONFIG_FILE) -> Optional[str]:      # Attempt to read `otx.api_key` from a local TOML file.
    if not os.path.exists(path):
        return None                                                 # Returns None if the file is missing or unreadable.
    
    try:                                                            
        import tomllib                                              # Safety-wise here, in case it is run on 3.10 or below (SUCKS) - otherwise it might break on built

        with open(path, "rb") as fh:                                # rb = read binary , fh = file handle / note that needs to read binary as toml is raw bytes...
            data = tomllib.load(fh)
        return (data.get("otx") or {}).get("api_key")
    
    except Exception:                                               # If anything goes wrong, returns none quietly (to dont break it)
        return None

def get_otx_api_key(cli_key: Optional[str] = None) -> str:          # Checks if API is given (optional); if not, goes to string (for retro-compatibility)
    
    key = cli_key or os.getenv("OTX_API_KEY") or _load_from_toml()  # Self-explanatory, get it from CLI (legacy), ENV, TOML
    if not key or not key.strip():                                  # key.strip = reads w/o spaces -> for validation purposes
        raise RuntimeError(                                         # Interrupt w/ RtE
            "OTX API key not found. Provide one via config.toml > OTX_API_KEY > env:\n"
            "[otx]\n"
            "api_key = \"YOUR_KEY\""
        )
    return key.strip()                                              # key altogether (no spaces)