# ---------- Coding-wise ----------
from __future__ import annotations
import json, csv, os, threading
from typing import List, Dict
from datetime import datetime, timezone, date

# ---------- Front-end ----------
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---------- In-home ----------
from config import get_otx_api_key
from auto_OTX import automation_OTX
from storage import init_db, filter_new, save_new

"""
At some point, I will have the UI separated in its own module (like right now but more clean), and the main happening somewhere else.
"""

def write_json(recs: List[Dict], path: str) -> None:

    os.makedirs(os.path.dirname(path), exist_ok=True)                                           # Makes a direction if lack of one

    with open(path, "w", encoding="utf-8") as f:
        json.dump(recs, f, indent=2, ensure_ascii=False)                                        # Dumpts into a JSON / ensure ascii prevents leakage

def write_csv(recs: List[Dict], path: str) -> None: 
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = ["indicator", "type", "source", "source_url", "first_seen", "pulse_name", "pulse_id"]

    with open(path, "w", newline="", encoding="utf-8") as f:                                    

        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()

        for r in recs:
            ctx = r.get("context", {}) or {}                                                    # Itinerates each entry. {} uses to fallback if emtpy
            w.writerow({
                "indicator": r.get("indicator", ""),
                "type": r.get("type", ""),
                "source": r.get("source", ""),
                "source_url": r.get("source_url", ""),
                "first_seen": r.get("first_seen", ""),
                "pulse_name": ctx.get("pulse_name", ""),
                "pulse_id": ctx.get("pulse_id", "")
            })

def parse_since(s: str):

    s = s.strip()

    if not s:                                                                                   # If empty w/o spaces, then there's nothing
        return None
    try:
        if "T" in s:                                                                            # If contains T -> Full ISO8601
            return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)
        return datetime.fromisoformat(s + "T00:00:00+00:00").astimezone(timezone.utc)
    except Exception:                                   
        raise ValueError("Use YYYY-MM-DD or full ISO like 2025-09-01T00:00:00Z")                # Friendly error. Friendly as it doenst break the app

def filter_since(recs: List[Dict], cutoff_dt) -> List[Dict]:                                    # Cutoff print

    out = []

    for r in recs:
        ts = r.get("first_seen", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z","+00:00"))                               # Refer to docs for this, gets kinda confusing the more you look at it
        except Exception:
            out.append(r)                                                                       # Keep if unknown/unclear/not-well-formatted
            continue
        if dt >= cutoff_dt:                                                                     # Return filteted list if TS is at/after cutoff
            out.append(r)
    return out

def summarize_by_type(recs: List[Dict]) -> Dict[str,int]:                                       

    from collections import Counter                                                             # Only add the module from the lib when needed
    
    return dict(Counter(r.get("type","unknown") for r in recs))                                 # If it misses a type, it becomes unknown, and turns the counter to plain IPv4, domain, etc.

# ---------- Date Picker (no external deps) ----------

class DatePicker(tk.Toplevel):
    def __init__(self, master, initial: str = ""):
        super().__init__(master)
        self.title("Pick a date")
        self.resizable(False, False)
        self.result: str | None = None

        today = date.today()                                                                    # try to parse initial
        yy, mm, dd = today.year, today.month, today.day
        if initial:
            try:
                d = datetime.fromisoformat(initial.strip() + "T00:00:00").date()
                yy, mm, dd = d.year, d.month, d.day
            except Exception:
                pass

        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0)

        ttk.Label(frm, text="Year").grid(row=0, column=0, padx=6, pady=4)
        ttk.Label(frm, text="Month").grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(frm, text="Day").grid(row=0, column=2, padx=6, pady=4)

        self.year = tk.Spinbox(frm, from_=1970, to=2100, width=6)
        self.year.delete(0, "end"); self.year.insert(0, str(yy))
        self.month = tk.Spinbox(frm, from_=1, to=12, width=4)
        self.month.delete(0, "end"); self.month.insert(0, str(mm))
        self.day = tk.Spinbox(frm, from_=1, to=31, width=4)
        self.day.delete(0, "end"); self.day.insert(0, str(dd))

        self.year.grid(row=1, column=0, padx=6, pady=4)
        self.month.grid(row=1, column=1, padx=6, pady=4)
        self.day.grid(row=1, column=2, padx=6, pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=3, pady=8)
        ttk.Button(btns, text="Today", command=self._today).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Clear", command=self._clear).grid(row=0, column=1, padx=4)
        ttk.Button(btns, text="OK", command=self._ok).grid(row=0, column=2, padx=4)
        ttk.Button(btns, text="Cancel", command=self._cancel).grid(row=0, column=3, padx=4)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _today(self):
        t = date.today()
        self.year.delete(0,"end"); self.year.insert(0, str(t.year))
        self.month.delete(0,"end"); self.month.insert(0, str(t.month))
        self.day.delete(0,"end"); self.day.insert(0, str(t.day))

    def _clear(self):
        self.result = ""
        self.destroy()

    def _ok(self):
        try:
            y = int(self.year.get()); m = int(self.month.get()); d = int(self.day.get())
            picked = date(y, m, d)
            self.result = picked.isoformat()                                                    # YYYY-MM-DD
            self.destroy()
        except Exception:
            messagebox.showerror("Invalid date", "Please provide a valid Year/Month/Day.")

    def _cancel(self):
        self.result = None
        self.destroy()

# ---------- GUI app ----------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IOCS - By Daniele R Ricciardelli")
        self.geometry("700x540")
        self.resizable(False, False)

        # --- Source registry ---
        # Will change this to checkboxes with a tree)
        self.sources = {
            "OTX (AlienVault)": automation_OTX,
            # "CISA": some_other_callable,   # easy to add later
        }

        # Vars
        self.selected_source = tk.StringVar(value="OTX (AlienVault)")
        self.save_dir   = tk.StringVar(value=os.path.abspath("."))
        self.base_name  = tk.StringVar(value="Report Name")
        self.pages      = tk.IntVar(value=1)
        self.want_json  = tk.BooleanVar(value=True)
        self.want_csv   = tk.BooleanVar(value=True)
        self.export_all = tk.BooleanVar(value=False)
        self.want_report= tk.BooleanVar(value=True)
        self.since_str  = tk.StringVar(value="")                                                # YYYY-MM-DD or ISO

        # Layout
        pad = {"padx":10, "pady":6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, **pad)

        # Source selector
        srclab = ttk.LabelFrame(frm, text="Source")
        srclab.grid(row=0, column=0, sticky="ew", **pad)
        ttk.Label(srclab, text="Choose source:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.source_cb = ttk.Combobox(srclab, textvariable=self.selected_source, state="readonly",
                                      values=list(self.sources.keys()), width=40)
        self.source_cb.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        # Output type
        typelab = ttk.LabelFrame(frm, text="Output format")
        typelab.grid(row=1, column=0, sticky="ew", **pad)
        ttk.Checkbutton(typelab, text="JSON", variable=self.want_json).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(typelab, text="CSV",  variable=self.want_csv ).grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Save path
        pathlab = ttk.LabelFrame(frm, text="Save directory")
        pathlab.grid(row=2, column=0, sticky="ew", **pad)
        self.path_entry = ttk.Entry(pathlab, textvariable=self.save_dir, width=60)
        self.path_entry.grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Button(pathlab, text="Browse…", command=self.pick_dir).grid(row=0, column=1, padx=8, pady=4)

        # File base name
        outlab = ttk.LabelFrame(frm, text="Output file base name")
        outlab.grid(row=3, column=0, sticky="ew", **pad)
        ttk.Entry(outlab, textvariable=self.base_name, width=30).grid(row=0, column=0, padx=8, pady=4, sticky="w")
        ttk.Label(outlab, text="(Do not repeat names, program will not re-write/edit files)").grid(row=0, column=1, padx=8, pady=4, sticky="w")

        # Flags
        flaglab = ttk.LabelFrame(frm, text="Flags")
        flaglab.grid(row=4, column=0, sticky="ew", **pad)
        ttk.Label(flaglab, text="Pages:").grid(row=0, column=0, padx=8, pady=4, sticky="e")
        ttk.Spinbox(flaglab, from_=1, to=50, textvariable=self.pages, width=6).grid(row=0, column=1, padx=8, pady=4, sticky="w")
        ttk.Checkbutton(flaglab, text="Export ALL (ignore dedup filter for export)", variable=self.export_all).grid(row=0, column=2, padx=8, pady=4, sticky="w")
        ttk.Checkbutton(flaglab, text="Write report", variable=self.want_report).grid(row=0, column=3, padx=8, pady=4, sticky="w")

        # Since + Date Picker
        sincelab = ttk.LabelFrame(frm, text="Since (optional)")
        sincelab.grid(row=5, column=0, sticky="ew", **pad)
        ttk.Entry(sincelab, textvariable=self.since_str, width=30).grid(row=0, column=0, padx=8, pady=4, sticky="w")
        ttk.Label(sincelab, text="Format: YYYY-MM-DD or 2025-09-01T00:00:00Z").grid(row=0, column=1, padx=8, pady=4, sticky="w")
        ttk.Button(sincelab, text="Pick date…", command=self.open_date_picker).grid(row=0, column=2, padx=8, pady=4)

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, sticky="ew", **pad)
        self.run_btn = ttk.Button(btns, text="Run", command=self.on_run)
        self.run_btn.grid(row=0, column=0, padx=8)
        ttk.Button(btns, text="Quit", command=self.destroy).grid(row=0, column=1, padx=8)

        # Log box
        loglab = ttk.LabelFrame(frm, text="Logs")
        loglab.grid(row=7, column=0, sticky="nsew", **pad)
        frm.grid_rowconfigure(7, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.log = tk.Text(loglab, height=10)
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

    def open_date_picker(self):
        dp = DatePicker(self, self.since_str.get())
        self.wait_window(dp)
        if dp.result is not None:
            # None = cancel, "" = clear, "YYYY-MM-DD" = chosen
            self.since_str.set(dp.result)

    def pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir.get() or os.getcwd())
        if d:
            self.save_dir.set(d)

    def logln(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.update_idletasks()

    def on_run(self):
        if not (self.want_json.get() or self.want_csv.get()):
            messagebox.showwarning("Select output", "Please select JSON and/or CSV.")
            return
        if not self.base_name.get().strip():
            messagebox.showwarning("Base name", "Please provide an output base name.")
            return
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def _run_pipeline(self):
        try:
            source_name = self.selected_source.get()
            fetch_fn = self.sources.get(source_name)
            if not fetch_fn:
                raise RuntimeError(f"Unknown source selected: {source_name}")

            self.logln(f"[*] Source: {source_name}")
            self.logln("[*] Loading API key…")
            api_key = get_otx_api_key()

            self.logln("[*] Initializing database…")
            init_db()

            pages = int(self.pages.get())
            self.logln(f"[*] Fetching (pages={pages})…")
            recs = fetch_fn(api_key, max_pulse_pages=pages)

            self.logln(f"[*] Pulled: {len(recs)} IoCs")
            self.logln("[*] Applying persistent dedup (NEW vs seen)…")
            new_recs = filter_new(recs)

            to_export = recs if self.export_all.get() else new_recs                             # Choose export set

            since_txt = self.since_str.get().strip()                                            # Since filter
            if since_txt:
                self.logln(f"[*] Applying --since filter: {since_txt}")
                cutoff = parse_since(since_txt)
                to_export = filter_since(to_export, cutoff)

            # Output paths
            base = self.base_name.get().strip()
            out_dir = self.save_dir.get().strip() or os.getcwd()
            json_out = os.path.join(out_dir, f"{base}.json")
            csv_out  = os.path.join(out_dir, f"{base}.csv")
            rpt_out  = os.path.join(out_dir, f"{base}_report.txt")

            # Write outputs
            if self.want_json.get():
                self.logln(f"[*] Writing JSON → {json_out}")
                write_json(to_export, json_out)
            if self.want_csv.get():
                self.logln(f"[*] Writing CSV  → {csv_out}")
                write_csv(to_export, csv_out)

            # Persist NEW
            self.logln("[*] Saving NEW IoCs to DB…")
            save_new(new_recs)

            # Report
            if self.want_report.get():
                self.logln(f"[*] Writing report → {rpt_out}")
                pulled_by = summarize_by_type(recs)
                exported_by = summarize_by_type(to_export)
                with open(rpt_out, "w", encoding="utf-8") as f:
                    f.write("# IoC Scrape Report\n")
                    f.write(f"Source:         {source_name}\n")
                    f.write(f"Pages:          {pages}\n")
                    f.write(f"Since filter:   {since_txt or 'none'}\n")
                    f.write(f"Pulled total:   {len(recs)}\n")
                    f.write(f"New (DB):       {len(new_recs)}\n")
                    f.write(f"Exported:       {len(to_export)}\n\n")
                    f.write("Pulled by type:\n")
                    for k,v in pulled_by.items(): f.write(f"  - {k}: {v}\n")
                    f.write("\nExported by type:\n")
                    for k,v in exported_by.items(): f.write(f"  - {k}: {v}\n")

            self.logln("[✓] Done.")
            messagebox.showinfo("Done", f"Exported {len(to_export)} IoCs")

        except Exception as e:
            self.logln(f"[!] Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.run_btn.config(state="normal")

if __name__ == "__main__":
    App().mainloop()
