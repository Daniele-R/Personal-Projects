from __future__ import annotations
import time                                                                                             # To be gentle, otherwise you a sicko
from typing import Dict, Any, List, Optional                                                            # Too lazy to explain... Google: Provides type hints for static analysis, code readability, and tooling (like IDEs, linters, and mypy).
from datetime import datetime, timezone                                                                 # For filtering. We nonly need "datetime func"
import requests                                                                                         # To obtain GET for HTTP

OTX_BASE = "https://otx.alienvault.com/api/v1"                                                          # Base URL for their API

def _headers(api_key: str) -> Dict[str, str]:                                                           # HTTP header helper - 
    return {
        "X-OTX-API-KEY": api_key,                                                                       # duh
        "User-Agent": "ioc-scraper-quickwin/0.3"                                                        # For good API hygiene (recommended based on docs)
    }

def _get_subscribed_pulses(api_key: str, page: int = 1) -> Dict[str, Any]:                              # Subscribed pulses page where initializes at 1. STR(KEY), Any (integer for the page, or ALL)
    url = f"{OTX_BASE}/pulses/subscribed?page={page}"                                                   # If this requires explanation, there's absolute no reason for you to be seeing my code
    r = requests.get(url, headers=_headers(api_key), timeout=30)                                        # r = request, buddy
    if r.status_code == 401:                                                                            # 401 - No bueno
        raise RuntimeError("OTX 401 Unauthorized. Check your API key.")                                 # Raise = interrupt
    r.raise_for_status()                                                                                # Other status such as 503, 443, etc.
    return r.json()                                                                                     # Easy pzy, straight JSON spitted

def _get_pulse_indicators(api_key: str, pulse_id: str, page: int = 1) -> Dict[str, Any]:                
    url = f"{OTX_BASE}/pulses/{pulse_id}/indicators?page={page}"                                        # Pulse id - identifier of the pulse - important to manual checks
    r = requests.get(url, headers=_headers(api_key), timeout=30)
    r.raise_for_status()
    return r.json()


def automation_OTX(                                                                                     # Main attraction
    api_key: str,
    *,                                                                                                  # Keeps order
    max_pulse_pages: int = 1,                                                                           # Initializes it at 1
    include_reports: bool = False,                                                                      # Not needed here, but for safety/further implementations
    since_iso: Optional[str] = None,                                                                    # Not needed here, but for safety/further implementations
    polite_delay: float = 0.8,                                                                          # In one of the examples online says to put it, so I did it here. I assume it can be set as a variable within the functions intead of an argument...
) -> List[Dict[str, Any]]:

    collected: List[Dict[str, Any]] = []                                                                # Initializes results

    # Parse the optional since timestamp once up-front
    since_dt: Optional[datetime] = None                                                                 # Starts empty

    if since_iso:
        try:
            since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))                         # Ever after writing it this format is cheeks
        except Exception:                                                                               # Ignore bad format AKA treats it as no filter
            since_dt = None                                                                             # Can parse as it is... OPTIONAL

    pulse_page = 1
    for _ in range(max_pulse_pages):                                                                    # FOR LOOP, FIRST ONE YAY
        data = _get_subscribed_pulses(api_key, page=pulse_page)                                         # From docs
        pulses = data.get("results", []) or []                                                          # ^
        for p in pulses:
            pulse_id = str(p.get("id"))
            pulse_name = p.get("name") or ""
            pulse_ref = p.get("reference") or ""

            # Walk indicators within this pulse
            ind_page = 1

            while True:
                inds = _get_pulse_indicators(api_key, pulse_id, page=ind_page)                          # Next page browsing
                results = inds.get("results", []) or []
                for it in results:                                                                      # Indicators come from it
                    indicator = (it.get("indicator") or "").strip()                                     # domain/IP/URL/hash
                    itype = (it.get("type") or "").strip().lower()                                      # domain, IPv4, URL, SHA256, MD5, ...

                    if since_dt is not None:                                                            # Optional since filter. Try common timestamp fields
                        ts = None                                                                       # ts = TimeStamp OR if you're genZ, means This/That Shit
                        for k in ("created", "modified", "expiration"):
                            v = it.get(k)                                                               # Gets the fields from line above and turns them into "Any" type
                            if v:                                                                       # AKA a good ol' temp var
                                try:
                                    ts = datetime.fromisoformat(str(v).replace("Z", "+00:00"))          # Transforms/Translates string to format required. MAGIC!
                                    break
                                except Exception:
                                    pass
                        if ts is not None and ts.tzinfo is not None:                                    # If lack of clarification, it is UTC
                            ts = ts.astimezone(timezone.utc)                                            
                        if ts is not None and ts < since_dt:                                            # It is still retrieved from the API, but it will ignore it
                            continue  # too old—skip

                    rec: Dict[str, Any] = {                                                             # Normalization report
                        "indicator": indicator,
                        "type": itype or "unknown",
                        "source": "OTX",
                        "source_url": pulse_ref,
                        "first_seen": it.get("created") or "",
                        "context": {
                            "pulse_name": pulse_name,
                            "pulse_id": pulse_id,
                        },
                    }
                    if include_reports and pulse_ref:                                                   # When successful...
                        rec["context"]["report_url"] = pulse_ref                                        
                    collected.append(rec)                                                               # Adds it to our results, collected

                if not inds.get("next_page"):                                                           # Once indicators are none, we reached the end of the indicator
                    break
                ind_page += 1                                                                           # Onto the next indicator

            if polite_delay:                                                                            # At this point I thought "pd" doenst read as "demiure" as "polite_delay"
                time.sleep(polite_delay)

        if not data.get("next_page"):                                                                   # If nothing else to retrieve, breaks
            break
        pulse_page += 1                                                                                 # Next pulse

    return collected                                                                                    # C O L L E C T E D