"""
tools/monitor.py — a lightweight system monitor GUI.
Packaged with a bundled config folder in Example 10.
"""

import tkinter as tk
import time
import threading
import json
import os
import platform


def load_config() -> dict:
    config_path = "packaged-within-exe:monitor_config/config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"refresh_ms": 2000, "title": "System Monitor"}


class MonitorApp:
    def __init__(self, root: tk.Tk, config: dict) -> None:
        root.title(config.get("title", "System Monitor"))
        root.geometry("420x280")
        root.configure(bg="#0d0d0d")
        root.resizable(False, False)

        self._refresh = config.get("refresh_ms", 2000)
        self._running = True

        tk.Label(root, text="SYSTEM MONITOR", font=("Courier", 13, "bold"),
                 bg="#0d0d0d", fg="#00ff41").pack(pady=(16, 4))

        self._stats_var = tk.StringVar(value="Loading…")
        tk.Label(root, textvariable=self._stats_var, font=("Courier", 10),
                 bg="#0d0d0d", fg="#00cc33", justify="left").pack(padx=20, pady=8)

        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._update()

    def _update(self) -> None:
        if not self._running:
            return
        lines = [
            f"Platform  : {platform.system()} {platform.release()}",
            f"Machine   : {platform.machine()}",
            f"Processor : {platform.processor() or 'N/A'}",
            f"Python    : {platform.python_version()}",
            f"Time      : {time.strftime('%H:%M:%S')}",
        ]
        self._stats_var.set("\n".join(lines))
        tk._default_root.after(self._refresh, self._update)  # type: ignore

    def _on_close(self) -> None:
        self._running = False
        tk._default_root.destroy()  # type: ignore


def main() -> None:
    config = load_config()
    root = tk.Tk()
    MonitorApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
