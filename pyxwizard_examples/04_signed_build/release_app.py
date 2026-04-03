"""
release_app.py — a minimal app packaged with code signing in Example 04.
"""

import tkinter as tk
from tkinter import messagebox


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "ACME Release App",
        "This EXE has been code-signed.\n\n"
        "Windows SmartScreen will trust it because it carries\n"
        "a valid digital signature from ACME Corp.",
    )
    root.destroy()


if __name__ == "__main__":
    main()
