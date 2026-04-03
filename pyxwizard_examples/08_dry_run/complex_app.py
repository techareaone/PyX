"""
complex_app.py — a script with several third-party imports used in Example 08
to demonstrate the dependency detection during a dry run.

None of these are actually executed during a dry run — PyX Wizard only
inspects and installs them into the build venv.
"""

# These imports cause PyX Wizard to detect and bundle these packages
import json
import os
import pathlib
import re
import datetime

# Third-party packages that will be detected
try:
    import requests          # HTTP
    import PIL               # Pillow
    import yaml              # PyYAML
except ImportError:
    pass   # OK in source — will be installed in build venv


def main() -> None:
    print("ComplexApp running.")
    data_path = "packaged-within-exe:config/settings.json"
    template_path = "packaged-within-exe:templates/report.html"
    print(f"Config   : {data_path}")
    print(f"Template : {template_path}")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
