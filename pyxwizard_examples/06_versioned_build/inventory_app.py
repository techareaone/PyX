"""
inventory_app.py — minimal inventory manager UI packaged in Example 06.
Demonstrates a real-world GUI app that benefits from version embedding.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


SAMPLE_STOCK = [
    {"sku": "WDG-001", "name": "Widget A",    "qty": 142, "reorder": 50},
    {"sku": "WDG-002", "name": "Widget B",    "qty": 23,  "reorder": 30},
    {"sku": "GAD-010", "name": "Gadget Pro",  "qty": 8,   "reorder": 20},
    {"sku": "GAD-011", "name": "Gadget Lite", "qty": 305, "reorder": 100},
    {"sku": "CMP-500", "name": "Component X", "qty": 0,   "reorder": 15},
]

APP_VERSION = "3.1.4"


class InventoryApp:
    def __init__(self, root: tk.Tk) -> None:
        root.title(f"Inventory Manager v{APP_VERSION}")
        root.geometry("620x380")
        root.configure(bg="#f0f0f0")

        # Header
        header = tk.Frame(root, bg="#2c3e50", pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"📦  Inventory Manager  •  v{APP_VERSION}",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white",
        ).pack()

        # Treeview
        frame = tk.Frame(root, bg="#f0f0f0", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        cols = ("SKU", "Name", "Qty", "Reorder At", "Status")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col not in ("Name", "Status") else 150)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._populate()

        # Footer
        footer = tk.Frame(root, bg="#ecf0f1", pady=5)
        footer.pack(fill="x")
        tk.Button(
            footer, text="Refresh", command=self._populate,
            bg="#3498db", fg="white", bd=0, padx=12, pady=4,
        ).pack(side="left", padx=10)
        tk.Button(
            footer, text="About", command=self._about,
            bg="#95a5a6", fg="white", bd=0, padx=12, pady=4,
        ).pack(side="left")

    def _populate(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in SAMPLE_STOCK:
            status = "⚠ Low" if item["qty"] <= item["reorder"] else "✓ OK"
            if item["qty"] == 0:
                status = "✗ Out of stock"
            tag = "low" if item["qty"] <= item["reorder"] else "ok"
            self.tree.insert("", "end", values=(
                item["sku"], item["name"], item["qty"], item["reorder"], status
            ), tags=(tag,))
        self.tree.tag_configure("low", foreground="#c0392b")
        self.tree.tag_configure("ok",  foreground="#27ae60")

    def _about(self) -> None:
        messagebox.showinfo(
            "About",
            f"Inventory Manager v{APP_VERSION}\n"
            "© Warehouse Solutions Inc.\n\n"
            "Version info is embedded in this EXE's\n"
            "file properties (right-click → Properties → Details).",
        )


if __name__ == "__main__":
    root = tk.Tk()
    InventoryApp(root)
    root.mainloop()
