"""
PyX Wizard — Example 07: GUI Builder with Live Callbacks
=========================================================
Embeds PyX Wizard into a tkinter GUI. Terminal output is suppressed
completely; instead, progress bars, log boxes, and step indicators
are driven by PyX Wizard's callback API.

This is the reference pattern for integrating PyX Wizard into any
desktop GUI (tkinter, PyQt, wxPython, etc.).

Key points:
  - feedback("none")     → silences all terminal output
  - on_progress(fn)      → fn(value: float 0-1, label: str)
  - on_log(fn)           → fn(message: str)
  - on_step(fn)          → fn(step_id: str, label: str, progress: float)
  - Callbacks + feedback mode persist across begin() calls — set once.

Requirements:
    pip install pyxwizard

Usage:
    python gui_builder.py
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path

import pyxwizard

# ── Wire up callbacks BEFORE begin() ────────────────────────────────────────
# These registrations persist; we attach real widgets later.
pyxwizard.feedback("none")   # suppress all terminal output


class BuilderApp:
    def __init__(self, root: tk.Tk) -> None:
        root.title("PyX Wizard — GUI Builder")
        root.geometry("700x580")
        root.configure(bg="#1a1a2e")
        root.resizable(False, False)

        self._build_thread: threading.Thread | None = None

        self._build_ui(root)
        self._wire_callbacks()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self, root: tk.Tk) -> None:
        DARK   = "#1a1a2e"
        PANEL  = "#16213e"
        ACCENT = "#e94560"
        FG     = "#eaeaea"
        MUTED  = "#8892a4"

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Build.Horizontal.TProgressbar",
            troughcolor=PANEL, background=ACCENT, thickness=8,
        )

        # ── Title bar ──
        title_frame = tk.Frame(root, bg=DARK, pady=14)
        title_frame.pack(fill="x")
        tk.Label(
            title_frame, text="⚡  PyX Wizard  GUI Builder",
            font=("Consolas", 15, "bold"), bg=DARK, fg=ACCENT,
        ).pack()

        # ── Config panel ──
        cfg = tk.Frame(root, bg=PANEL, padx=20, pady=12)
        cfg.pack(fill="x", padx=12, pady=(0, 8))

        def row(label: str, r: int) -> tk.Entry:
            tk.Label(cfg, text=label, font=("Segoe UI", 9), bg=PANEL, fg=MUTED, anchor="w")\
                .grid(row=r, column=0, sticky="w", padx=(0, 10), pady=3)
            e = tk.Entry(cfg, font=("Consolas", 10), bg="#0f3460", fg=FG,
                         insertbackground=FG, bd=0, width=48)
            e.grid(row=r, column=1, sticky="ew", pady=3)
            return e

        cfg.columnconfigure(1, weight=1)

        self._script_entry = row("Script path", 0)
        self._name_entry   = row("App name",    1)
        self._icon_entry   = row("Icon (.ico)",  2)

        # Browse button
        tk.Button(
            cfg, text="Browse…", font=("Segoe UI", 9),
            bg=ACCENT, fg="white", bd=0, padx=10, pady=4,
            command=self._browse_script,
        ).grid(row=0, column=2, padx=(8, 0), pady=3)

        # Console toggle
        self._console_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            cfg, text="Show console window", variable=self._console_var,
            bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
            font=("Segoe UI", 9),
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # ── Step indicator ──
        self._step_label = tk.Label(
            root, text="Ready", font=("Consolas", 9),
            bg=DARK, fg=MUTED, anchor="w",
        )
        self._step_label.pack(fill="x", padx=14)

        # ── Progress bar ──
        self._progress_var = tk.DoubleVar(value=0.0)
        self._progress_bar = ttk.Progressbar(
            root, variable=self._progress_var,
            style="Build.Horizontal.TProgressbar",
            maximum=1.0, length=676,
        )
        self._progress_bar.pack(padx=12, pady=(2, 6))

        self._progress_label = tk.Label(
            root, text="", font=("Segoe UI", 8),
            bg=DARK, fg=MUTED,
        )
        self._progress_label.pack()

        # ── Log box ──
        self._log = scrolledtext.ScrolledText(
            root, font=("Consolas", 8), bg="#0d0d1a", fg="#b0c4de",
            insertbackground="white", bd=0, height=14,
        )
        self._log.pack(fill="both", expand=True, padx=12, pady=(4, 8))
        self._log.config(state="disabled")

        # ── Build / Cancel buttons ──
        btn_frame = tk.Frame(root, bg=DARK, pady=8)
        btn_frame.pack()
        self._build_btn = tk.Button(
            btn_frame, text="▶  BUILD",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT, fg="white", bd=0, padx=28, pady=8,
            command=self._start_build,
        )
        self._build_btn.pack(side="left", padx=6)

    def _wire_callbacks(self) -> None:
        """Register PyX Wizard callbacks that update our widgets."""
        pyxwizard.on_progress(self._cb_progress)
        pyxwizard.on_log(self._cb_log)
        pyxwizard.on_step(self._cb_step)

    # ── Callbacks (called from PyX Wizard's build thread) ───────────────────

    def _cb_progress(self, value: float, label: str) -> None:
        self._progress_var.set(value)
        self._progress_label.config(text=label)

    def _cb_log(self, message: str) -> None:
        self._log.config(state="normal")
        self._log.insert("end", message + "\n")
        self._log.see("end")
        self._log.config(state="disabled")

    def _cb_step(self, step_id: str, label: str, progress: float) -> None:
        self._step_label.config(text=f"▸  {label}")

    # ── Build logic ─────────────────────────────────────────────────────────

    def _browse_script(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Python scripts", "*.py"), ("All files", "*.*")]
        )
        if path:
            self._script_entry.delete(0, "end")
            self._script_entry.insert(0, path)
            if not self._name_entry.get():
                self._name_entry.insert(0, Path(path).stem)

    def _start_build(self) -> None:
        script = self._script_entry.get().strip()
        name   = self._name_entry.get().strip()
        icon   = self._icon_entry.get().strip()

        if not script or not name:
            self._cb_log("⚠  Please fill in Script path and App name.")
            return

        self._build_btn.config(state="disabled", text="Building…")
        self._progress_var.set(0.0)
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

        def run() -> None:
            pyxwizard.begin()
            pyxwizard.location(script)
            pyxwizard.name(name)
            pyxwizard.console(self._console_var.get())
            if icon:
                pyxwizard.icon(icon)

            result = pyxwizard.build()

            # Update UI on the main thread
            root = self._build_btn.winfo_toplevel()
            root.after(0, lambda: self._on_build_done(result))

        self._build_thread = threading.Thread(target=run, daemon=True)
        self._build_thread.start()

    def _on_build_done(self, result) -> None:
        self._build_btn.config(state="normal", text="▶  BUILD")
        if result:
            self._cb_log(f"\n✅  SUCCESS  →  {result.exe_path}")
            self._cb_log(f"   Size: {result.exe_size_mb:.1f} MB  |  Time: {result.build_duration_seconds:.1f}s")
            self._step_label.config(text="✅  Build complete")
        else:
            self._cb_log(f"\n❌  FAILED: {result.error_message}")
            self._step_label.config(text="❌  Build failed")


if __name__ == "__main__":
    root = tk.Tk()
    app = BuilderApp(root)
    root.mainloop()
