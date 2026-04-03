"""
heavy_app.py — simulates a slow-loading application to demonstrate
the splash screen staying visible during startup in Example 05.
"""

import time
import tkinter as tk


def main() -> None:
    # Simulate a slow import / initialisation phase
    time.sleep(3)

    root = tk.Tk()
    root.title("Heavy App")
    root.geometry("400x200")

    label = tk.Label(
        root,
        text="App loaded!\nThe splash screen was shown during startup.",
        font=("Segoe UI", 13),
        justify="center",
    )
    label.pack(expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
