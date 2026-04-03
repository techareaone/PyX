"""
calculator_app.py — simple tkinter calculator being packaged in Example 02.
"""

import tkinter as tk


class Calculator:
    def __init__(self, root: tk.Tk) -> None:
        root.title("Calculator")
        root.resizable(False, False)

        self._expression = ""

        # Display
        self._display_var = tk.StringVar(value="0")
        display = tk.Entry(
            root,
            textvariable=self._display_var,
            font=("Segoe UI", 22),
            justify="right",
            state="readonly",
            bd=0,
            bg="#1e1e1e",
            fg="white",
            readonlybackground="#1e1e1e",
        )
        display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        # Button layout
        buttons = [
            ("C", 1, 0), ("±", 1, 1), ("%", 1, 2), ("÷", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("×", 2, 3),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("−", 3, 3),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("+", 4, 3),
            ("0", 5, 0), (".", 5, 2),              ("=", 5, 3),
        ]

        op_map = {"÷": "/", "×": "*", "−": "-"}

        for label, row, col in buttons:
            colspan = 2 if label == "0" else 1
            bg = "#ff9f0a" if label in ("=",) else (
                "#505050" if label in ("C", "±", "%", "÷", "×", "−", "+") else "#333333"
            )
            btn = tk.Button(
                root, text=label, font=("Segoe UI", 16), bg=bg, fg="white",
                activebackground="#666666", bd=0, padx=20, pady=20,
                command=lambda l=label, m=op_map: self._press(l, m),
            )
            btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)

        for i in range(6):
            root.rowconfigure(i, weight=1)
        for i in range(4):
            root.columnconfigure(i, weight=1)

    def _press(self, label: str, op_map: dict) -> None:
        if label == "C":
            self._expression = ""
            self._display_var.set("0")
        elif label == "=":
            try:
                result = eval(self._expression)  # noqa: S307 (demo only)
                self._display_var.set(str(result))
                self._expression = str(result)
            except Exception:
                self._display_var.set("Error")
                self._expression = ""
        elif label == "±":
            try:
                val = float(self._expression or "0") * -1
                self._expression = str(val)
                self._display_var.set(self._expression)
            except Exception:
                pass
        elif label == "%":
            try:
                val = float(self._expression or "0") / 100
                self._expression = str(val)
                self._display_var.set(self._expression)
            except Exception:
                pass
        else:
            ch = op_map.get(label, label)
            self._expression += ch
            self._display_var.set(self._expression)


if __name__ == "__main__":
    root = tk.Tk()
    Calculator(root)
    root.mainloop()
