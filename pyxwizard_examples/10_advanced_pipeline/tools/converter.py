"""
tools/converter.py — a file-format converter tool.
Packaged as a single-file EXE in Example 10 using --onefile.
"""

import sys
import os
from pathlib import Path


SUPPORTED = {".txt", ".csv", ".json", ".md"}


def convert(src: Path, to_ext: str) -> None:
    if src.suffix not in SUPPORTED:
        print(f"Unsupported input format: {src.suffix}")
        sys.exit(1)
    dest = src.with_suffix(to_ext)
    content = src.read_text(encoding="utf-8")
    # Minimal transform: wrap in target format envelope
    if to_ext == ".md":
        output = f"# {src.stem}\n\n```\n{content}\n```\n"
    elif to_ext == ".json":
        import json
        output = json.dumps({"source": src.name, "content": content}, indent=2)
    else:
        output = content
    dest.write_text(output, encoding="utf-8")
    print(f"Converted: {src}  →  {dest}")


def main() -> None:
    print("FileConverter — built as --onefile EXE")
    if len(sys.argv) < 3:
        print(f"Usage: FileConverter <input_file> <output_extension>")
        print(f"Supported: {', '.join(sorted(SUPPORTED))}")
        input("\nPress Enter to exit...")
        return
    src  = Path(sys.argv[1])
    ext  = sys.argv[2] if sys.argv[2].startswith(".") else f".{sys.argv[2]}"
    convert(src, ext)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
