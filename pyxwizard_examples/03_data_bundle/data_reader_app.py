"""
data_reader_app.py — reads bundled config and asset files at runtime.

PyX Wizard rewrites "packaged-within-exe:..." paths at build time so
the files are found correctly whether the app is run from source or
from the compiled EXE.
"""

import json
import os


def read_bundled_file(pyx_path: str) -> str:
    """
    Read a file using a PyX Wizard bundled path.
    At runtime inside the EXE the preprocessor has already rewritten
    these to the correct sys._MEIPASS-relative path.
    """
    with open(pyx_path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    print("=== Data Reader App ===\n")

    # --- Read a JSON config file bundled from the 'config' folder ---
    config_raw = read_bundled_file("packaged-within-exe:config/settings.json")
    config = json.loads(config_raw)
    print("Config loaded:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print()

    # --- Read a text asset from the 'assets' folder ---
    motd = read_bundled_file("packaged-within-exe:assets/motd.txt")
    print("Message of the day:")
    print(f"  {motd.strip()}")

    print("\nDone.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
