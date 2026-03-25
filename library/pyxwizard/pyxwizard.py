#!/usr/bin/env python3
"""
PyX Wizard – Terminal Library Edition
======================================
A Python library that packages Python scripts into standalone Windows
executables using PyInstaller, with automatic dependency detection,
virtual environment isolation, optional code signing, and data bundling.

Usage
-----
    import pyxwizard

    pyxwizard.begin()
    pyxwizard.location("my_script.py")       # or "self" to package the calling script
    pyxwizard.name("MyProject")
    pyxwizard.author("My Name")              # optional, default TRADELY.DEV
    pyxwizard.console(True)                  # optional, default True
    pyxwizard.icon("app.ico")               # optional, default Tradely icon
    pyxwizard.data("assets", "config")       # optional, bundle folders into EXE
    pyxwizard.cert("cert.pfx", "pass123")    # optional, code signing
    pyxwizard.outlocation("C:/builds")       # where to create PyX_Data
    pyxwizard.build()
"""

# =============================================================================
# IMPORTS – Standard Library
# =============================================================================
import sys
import os
import re
import ast
import json
import shutil
import subprocess
import threading
import platform
import multiprocessing
import venv
import datetime
import tempfile
import textwrap
import urllib.request
import urllib.error
import inspect
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Set, Tuple

# =============================================================================
# IMPORTS – Optional (cryptography for PFX validation)
# =============================================================================
try:
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# =============================================================================
# CONSTANTS
# =============================================================================
APP_VERSION = "1.0.0"
DEFAULT_AUTHOR = "TRADELY.DEV"
PYINSTALLER_FLAGS = ["--onefile", "--clean", "--noconfirm"]
DEFAULT_ICON_URL = "https://doc.tradely.dev/images/tradely.ico"
SIGNTOOL_RELATIVE_PATH = "signtool/signtool.exe"
LIBRARIES_CATEGORY_FILE = "https://doc.tradely.dev/PyX/lib_categories.json"

# =============================================================================
# GLOBALS – Fetched Library Data
# =============================================================================
_lib_categories: Dict[str, str] = {}
_lib_collect_all: Set[str] = set()
_lib_hidden_imports: Dict[str, List[str]] = {}
_lib_copy_metadata: Dict[str, str] = {}
_lib_categories_loaded: bool = False

# =============================================================================
# CONSTANTS – Standard Library Module Names
# =============================================================================
_STDLIB_SKIP: Set[str] = {
    "__future__", "_thread", "abc", "aifc", "argparse", "array", "ast",
    "asynchat", "asyncio", "asyncore", "atexit", "audioop", "base64",
    "bdb", "binascii", "binhex", "bisect", "builtins", "bz2", "calendar",
    "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs", "codeop",
    "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt",
    "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
    "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc",
    "getopt", "getpass", "gettext", "glob", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "lib2to3", "linecache", "locale", "logging", "lzma",
    "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap",
    "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
    "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd",
    "smtplib", "sndhdr", "socket", "socketserver", "spwd", "sqlite3",
    "sre_compile", "sre_constants", "sre_parse", "ssl", "stat",
    "statistics", "string", "stringprep", "struct", "subprocess",
    "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
    "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
    "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid",
    "venv", "warnings", "wave", "weakref", "webbrowser", "winreg",
    "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
    "zipfile", "zipimport", "zlib",
    "_abc", "_bootlocale", "_collections_abc", "_compat_pickle",
    "_compression", "_contextvars", "_csv", "_datetime", "_decimal",
    "_dummy_thread", "_heapq", "_imp", "_io", "_json", "_locale",
    "_lzma", "_markupbase", "_opcode", "_operator", "_osx_support",
    "_pydecimal", "_pyio", "_queue", "_random", "_signal", "_sitebuiltins",
    "_socket", "_sqlite3", "_sre", "_ssl", "_stat", "_string",
    "_strptime", "_struct", "_symtable", "_threading_local", "_tracemalloc",
    "_warnings", "_weakref", "_weakrefset",
    "antigravity", "this", "ntpath", "posixpath", "genericpath",
    "stat", "nturl2path", "opcode", "dis",
    "encodings", "collections", "concurrent", "email", "html", "http",
    "importlib", "logging", "multiprocessing", "unittest", "urllib",
    "xml", "xmlrpc", "ctypes", "curses", "dbm", "distutils", "json",
    "lib2to3", "test", "tkinter", "idlelib",
    "copy", "io", "os", "re", "sys", "time", "math", "random",
    "typing", "dataclasses", "enum", "abc", "functools", "itertools",
    "operator", "contextlib", "pathlib", "subprocess",
    "msilib", "msvcrt", "winreg", "winsound",
    "__main__", "__phello__",
    "ensurepip", "pip", "setuptools", "pkg_resources",
    "pydoc_data", "turtledemo",
    "zoneinfo", "graphlib", "tomllib",
}

# =============================================================================
# CONSTANTS – Injected Helper Code
# =============================================================================
INJECTED_PATH_HELPER = textwrap.dedent('''\
# --- PyX Wizard: injected path helper (start) ---
import sys as _pyx_sys
import os as _pyx_os
from pathlib import Path as _pyx_Path

def _resolve_packaged_path(relative_path: str) -> str:
    """
    Resolve a path to a bundled resource.
    When running as a frozen executable (built by PyInstaller), resources are
    extracted to a temporary folder accessible via sys._MEIPASS.
    When running as a normal Python script, resources are relative to the
    script file location.
    Returns the resolved path as a string.
    """
    if getattr(_pyx_sys, "frozen", False):
        base = _pyx_Path(_pyx_sys._MEIPASS)
    else:
        base = _pyx_Path(__file__).parent
    return str(base / relative_path)

# Set the working directory to the location of the executable (or script)
# so that relative paths to files alongside the exe still work correctly.
if getattr(_pyx_sys, "frozen", False):
    _pyx_os.chdir(_pyx_os.path.dirname(_pyx_sys.executable))
else:
    _pyx_os.chdir(_pyx_os.path.dirname(_pyx_os.path.abspath(__file__)))
# --- PyX Wizard: injected path helper (end) ---
''')


# =============================================================================
# TERMINAL OUTPUT HELPERS
# =============================================================================
class _TermStyle:
    """ANSI colour codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    GREY    = "\033[90m"
    BG_GREEN  = "\033[42m"
    BG_RED    = "\033[41m"
    BG_YELLOW = "\033[43m"


def _banner() -> None:
    """Print the PyX Wizard banner."""
    S = _TermStyle
    print()
    print(f"{S.GREEN}{S.BOLD}  ╔══════════════════════════════════════════════════╗{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║                                                  ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ██████╗ ██╗   ██╗██╗  ██╗                    ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ██╔══██╗╚██╗ ██╔╝╚██╗██╔╝                    ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ██████╔╝ ╚████╔╝  ╚███╔╝                     ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ██╔═══╝   ╚██╔╝   ██╔██╗                     ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ██║        ██║   ██╔╝ ██╗                     ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║     ╚═╝        ╚═╝   ╚═╝  ╚═╝     WIZARD        ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║                                                  ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ║  {S.WHITE}Python → EXE Builder  {S.GREY}v{APP_VERSION:<10}{S.GREEN}{S.BOLD}             ║{S.RESET}")
    print(f"{S.GREEN}{S.BOLD}  ╚══════════════════════════════════════════════════╝{S.RESET}")
    print()


def _header(text: str) -> None:
    """Print a section header."""
    S = _TermStyle
    width = 54
    print()
    print(f"{S.CYAN}{S.BOLD}  ┌{'─' * width}┐{S.RESET}")
    print(f"{S.CYAN}{S.BOLD}  │  {text:<{width - 2}}│{S.RESET}")
    print(f"{S.CYAN}{S.BOLD}  └{'─' * width}┘{S.RESET}")


def _info(msg: str) -> None:
    """Print an info message."""
    print(f"  {_TermStyle.GREEN}●{_TermStyle.RESET}  {msg}")


def _warn(msg: str) -> None:
    """Print a warning message."""
    print(f"  {_TermStyle.YELLOW}⚠{_TermStyle.RESET}  {_TermStyle.YELLOW}{msg}{_TermStyle.RESET}")


def _error(msg: str) -> None:
    """Print an error message."""
    print(f"  {_TermStyle.RED}✕{_TermStyle.RESET}  {_TermStyle.RED}{msg}{_TermStyle.RESET}")


def _success(msg: str) -> None:
    """Print a success message."""
    print(f"  {_TermStyle.GREEN}✓{_TermStyle.RESET}  {_TermStyle.GREEN}{msg}{_TermStyle.RESET}")


def _detail(msg: str) -> None:
    """Print a detail/subprocess line."""
    print(f"  {_TermStyle.GREY}   {msg}{_TermStyle.RESET}")


def _progress_bar(label: str, current: float, total: float = 1.0, width: int = 40) -> None:
    """Print a progress bar."""
    S = _TermStyle
    ratio = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    print(f"\r  {S.GREEN}{bar}{S.RESET}  {pct:>3}%  {S.GREY}{label}{S.RESET}", end="", flush=True)
    if ratio >= 1.0:
        print()


# =============================================================================
# CORE HELPER FUNCTIONS
# =============================================================================
def _resolve_packaged_path_local(relative_path: str) -> Path:
    """Resolve a path to a resource bundled alongside this script or frozen exe."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / relative_path


def _fetch_lib_categories() -> bool:
    """Download LIBRARIES_CATEGORY_FILE and populate all library globals."""
    global _lib_categories, _lib_collect_all, _lib_hidden_imports, _lib_copy_metadata, _lib_categories_loaded
    try:
        with urllib.request.urlopen(LIBRARIES_CATEGORY_FILE, timeout=6) as resp:
            data: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))

        mapping: Dict[str, str] = {}
        for cat_name, libs in data.get("categories", {}).items():
            if isinstance(libs, list):
                for lib in libs:
                    mapping[str(lib).lower()] = cat_name
        _lib_categories = mapping

        collect_all = data.get("collect_all", [])
        if isinstance(collect_all, list):
            _lib_collect_all = set(collect_all)

        hidden = data.get("hidden_imports", {})
        if isinstance(hidden, dict):
            _lib_hidden_imports = {
                pkg: entries
                for pkg, entries in hidden.items()
                if isinstance(entries, list)
            }

        copy_meta = data.get("copy_metadata", {})
        if isinstance(copy_meta, dict):
            _lib_copy_metadata = {
                imp: dist
                for imp, dist in copy_meta.items()
                if isinstance(dist, str)
            }

        _lib_categories_loaded = True
        return True
    except Exception:
        _lib_categories_loaded = False
        return False


def _get_category(lib_name: str) -> Optional[str]:
    """Return the category for *lib_name* if known, else None."""
    return _lib_categories.get(lib_name.lower())


def detect_script_imports(script_path: Path) -> List[str]:
    """Parse a Python script and extract all top-level third-party import names."""
    imports: Set[str] = set()
    try:
        source_code = script_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source_code, filename=str(script_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as parse_error:
        _warn(f"Could not parse {script_path}: {parse_error}")
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level_name = alias.name.split(".")[0]
                imports.add(top_level_name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                top_level_name = node.module.split(".")[0]
                imports.add(top_level_name)

    sanitised: List[str] = []
    for name in sorted(imports):
        if not name.isidentifier():
            continue
        if name.lower() in {item.lower() for item in _STDLIB_SKIP}:
            continue
        if name.lower() == "pyinstaller":
            continue
        # Exclude pyxwizard itself to avoid self-referencing
        if name.lower() == "pyxwizard":
            continue
        sanitised.append(name)

    return sanitised


def folder_size(path: Path) -> int:
    """Calculate total size of all files within a directory recursively."""
    total_bytes = 0
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_bytes += item.stat().st_size
                except OSError:
                    pass
    return total_bytes


def write_manifest(project_dir: Path, meta: dict) -> None:
    """Write a JSON manifest file into the project directory."""
    manifest_path = project_dir / "pyx_manifest.json"
    manifest_path.write_text(
        json.dumps(meta, indent=4, default=str),
        encoding="utf-8"
    )


def write_build_log(project_dir: Path, log_lines: List[str]) -> None:
    """Write the build log to a timestamped file in logs/."""
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"build_{timestamp_str}.txt"
    log_file.write_text("\n".join(log_lines), encoding="utf-8")


def validate_pfx(pfx_path: Path, password: str) -> bool:
    """Validate a PFX/P12 certificate file using the cryptography library."""
    if not CRYPTOGRAPHY_AVAILABLE:
        return False
    try:
        pfx_data = pfx_path.read_bytes()
        pkcs12.load_key_and_certificates(
            pfx_data,
            password.encode("utf-8"),
            default_backend()
        )
        return True
    except Exception:
        return False


def run_cmd(
    cmd: List[str],
    log: Callable[[str], None],
    cwd: Optional[str] = None,
    verbose: bool = True
) -> None:
    """Execute a subprocess command and stream output to the log callback."""
    log(f"Running: {' '.join(str(c) for c in cmd)}")
    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NO_WINDOW
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        cwd=cwd,
        creationflags=creation_flags
    )
    output_lines: List[str] = []
    for line in process.stdout:
        stripped_line = line.rstrip("\n\r")
        output_lines.append(stripped_line)
        if verbose:
            log(stripped_line)
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode,
            cmd,
            output="\n".join(output_lines)
        )


def create_project_venv(project_dir: Path, log: Callable[[str], None]) -> Path:
    """Create or reuse a virtual environment in the project directory."""
    venv_dir = project_dir / "venv"
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if python_exe.exists():
        log(f"Reusing existing virtual environment: {venv_dir}")
    else:
        log(f"Creating virtual environment: {venv_dir}")
        if getattr(sys, "frozen", False):
            system_python = shutil.which("python") or shutil.which("python3")
            if not system_python:
                raise FileNotFoundError(
                    "Could not find a Python interpreter on PATH to create the "
                    "virtual environment. Please ensure Python is installed and "
                    "available on your PATH."
                )
            run_cmd([system_python, "-m", "venv", str(venv_dir)], log)
        else:
            venv.create(str(venv_dir), with_pip=True, clear=False)
        log("Virtual environment created successfully.")

    return python_exe


def venv_pip_install(
    python_exe: Path,
    *packages: str,
    log: Callable[[str], None]
) -> None:
    """Install packages using pip inside the virtual environment."""
    if not packages:
        return
    cmd = [str(python_exe), "-m", "pip", "install"] + list(packages)
    run_cmd(cmd, log)


def venv_has_package(python_exe: Path, package: str) -> bool:
    """Check if a package is importable in the virtual environment."""
    try:
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [str(python_exe), "-c", f"import {package}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            creationflags=creation_flags
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_script_deps(
    python_exe: Path,
    script_path: Path,
    log: Callable[[str], None]
) -> None:
    """Detect and install third-party imports into the virtual environment."""
    detected_imports = detect_script_imports(script_path)
    if not detected_imports:
        log("No third-party dependencies detected.")
        return

    log(f"Detected third-party imports: {', '.join(detected_imports)}")

    for package_name in detected_imports:
        if venv_has_package(python_exe, package_name):
            log(f"  Package '{package_name}' is already installed.")
        else:
            pip_name = _lib_copy_metadata.get(package_name, package_name)
            log(f"  Installing '{pip_name}'...")
            try:
                venv_pip_install(python_exe, pip_name, log=log)
            except subprocess.CalledProcessError as install_error:
                log(
                    f"  WARNING: Failed to install '{pip_name}'. "
                    f"It may be a local module or have a different pip name. "
                    f"Error: {install_error}"
                )


def sign_exe(
    exe: Path,
    pfx: Path,
    pwd: str,
    log: Callable[[str], None],
    signtool_path_override: Optional[str] = None
) -> None:
    """Sign the built executable using signtool.exe."""
    if signtool_path_override:
        signtool_path = Path(signtool_path_override)
    else:
        signtool_path = _resolve_packaged_path_local(SIGNTOOL_RELATIVE_PATH)

    if not signtool_path.exists():
        log(f"WARNING: signtool.exe not found at {signtool_path}. Skipping code signing.")
        return

    cmd = [
        str(signtool_path),
        "sign",
        "/f", str(pfx),
        "/p", pwd,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        str(exe)
    ]
    log("Signing executable...")
    try:
        run_cmd(cmd, log)
        log("Code signing completed successfully.")
    except subprocess.CalledProcessError as sign_error:
        log(f"WARNING: Code signing failed: {sign_error}")


def _download_icon(base_dir: Path) -> Optional[str]:
    """Download the default icon from DEFAULT_ICON_URL."""
    icon_path = base_dir / "default_icon.ico"
    if icon_path.exists():
        return str(icon_path)
    try:
        urllib.request.urlretrieve(DEFAULT_ICON_URL, str(icon_path))
        return str(icon_path)
    except (urllib.error.URLError, OSError, Exception) as download_error:
        _warn(f"Could not download default icon: {download_error}")
        return None


def preprocess_script(script_path: Path, temp_dir: Path) -> Path:
    """Create a preprocessed copy of the target script with injected helpers."""
    source_code = script_path.read_text(encoding="utf-8", errors="replace")
    lines = source_code.split("\n")

    has_toplevel_resolver = False
    try:
        tree = ast.parse(source_code)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_resolve_packaged_path":
                has_toplevel_resolver = True
                break
    except SyntaxError:
        pass

    if has_toplevel_resolver:
        modified_source = source_code
    else:
        last_import_line_index = -1
        for line_index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if not line[0:1].isspace():
                    last_import_line_index = line_index

        if "# --- PyX Wizard: injected path helper (start) ---" not in source_code:
            injection_position = last_import_line_index + 1 if last_import_line_index >= 0 else 0
            helper_lines = INJECTED_PATH_HELPER.split("\n")
            for offset, helper_line in enumerate(helper_lines):
                lines.insert(injection_position + offset, helper_line)

        modified_source = "\n".join(lines)

        packaged_pattern = re.compile(
            r"""(?P<quote>["'])packaged-within-exe:(?P<relpath>[^"']+)(?P=quote)"""
        )
        modified_source = packaged_pattern.sub(
            r'_resolve_packaged_path("\g<relpath>")',
            modified_source
        )

    temp_script_path = temp_dir / script_path.name
    temp_script_path.write_text(modified_source, encoding="utf-8")
    return temp_script_path


def _strip_pyxwizard_from_script(script_path: Path, temp_dir: Path) -> Path:
    """
    For 'self' mode: copy the calling script but remove all pyxwizard
    import lines and pyxwizard.xxx() calls so the packaged EXE doesn't
    depend on this library.
    """
    source = script_path.read_text(encoding="utf-8", errors="replace")
    lines = source.split("\n")
    cleaned: List[str] = []

    for line in lines:
        stripped = line.strip()
        # Remove import pyxwizard / from pyxwizard import ...
        if re.match(r'^(import\s+pyxwizard|from\s+pyxwizard\s+import)', stripped, re.IGNORECASE):
            continue
        # Remove pyxwizard.xxx(...) calls (any casing)
        if re.match(r'^pyxwizard\.\w+\s*\(', stripped, re.IGNORECASE):
            continue
        cleaned.append(line)

    output_path = temp_dir / script_path.name
    output_path.write_text("\n".join(cleaned), encoding="utf-8")
    return output_path


def count_existing_projects(base_dir: Path) -> int:
    """Count existing project directories inside PyX_Data/."""
    pyx_data_dir = base_dir / "PyX_Data"
    if not pyx_data_dir.exists():
        return 0
    return sum(1 for item in pyx_data_dir.iterdir() if item.is_dir())


# =============================================================================
# PyX WIZARD CLASS – The Library Interface
# =============================================================================
class _PyXWizard:
    """
    Internal state manager for the pyxwizard library.
    All public module-level functions delegate to a singleton instance.
    """

    def __init__(self) -> None:
        self._initialised = False
        self._script_path: Optional[Path] = None
        self._self_mode = False
        self._project_name: Optional[str] = None
        self._author: str = DEFAULT_AUTHOR
        self._console_mode: bool = True
        self._icon_path: Optional[str] = None
        self._data_folders: List[Path] = []
        self._pfx_path: Optional[Path] = None
        self._pfx_password: Optional[str] = None
        self._signtool_path: Optional[str] = None
        self._out_location: Optional[Path] = None
        self._log_lines: List[str] = []
        self._detected_imports: List[str] = []
        self._lib_fetch_done = False

    def _reset(self) -> None:
        """Reset all state for a fresh configuration."""
        self._script_path = None
        self._self_mode = False
        self._project_name = None
        self._author = DEFAULT_AUTHOR
        self._console_mode = True
        self._icon_path = None
        self._data_folders = []
        self._pfx_path = None
        self._pfx_password = None
        self._signtool_path = None
        self._out_location = None
        self._log_lines = []
        self._detected_imports = []

    def _log(self, message: str) -> None:
        """Log a message to both terminal and internal buffer."""
        self._log_lines.append(message)
        _detail(message)

    def _get_base_dir(self) -> Path:
        """Return the base directory for PyX_Data output."""
        if self._out_location is not None:
            return self._out_location
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        # Default: directory of the calling script, or CWD
        if self._script_path:
            return self._script_path.parent
        return Path.cwd()

    # -------------------------------------------------------------------------
    # PUBLIC API METHODS
    # -------------------------------------------------------------------------

    def begin(self) -> None:
        """Initialise PyX Wizard. Must be called first."""
        self._reset()
        self._initialised = True
        _banner()
        _info("PyX Wizard initialised.")
        _info(f"Platform: {platform.system()} {platform.machine()}")
        _info(f"Python: {sys.version.split()[0]}")
        _info(f"Default author: {self._author}")

        # Fetch library categories in background
        if not self._lib_fetch_done:
            _info("Fetching library categories from remote...")
            success = _fetch_lib_categories()
            self._lib_fetch_done = True
            if success:
                cat_count = len(_lib_categories)
                _success(f"Library categories loaded ({cat_count} libraries catalogued).")
            else:
                _warn("Could not fetch library categories (no internet?). Build will continue without categorisation.")

    def location(self, script_path: str) -> None:
        """Set the Python script to package."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.location().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("SCRIPT LOCATION")

        if script_path.lower() == "self":
            # Package the calling script — walk the stack to find the first
            # frame that is outside this module (skips the module-level wrapper).
            _this_file = os.path.abspath(__file__)
            caller_file = None
            for _frame in inspect.stack():
                if os.path.abspath(_frame.filename) != _this_file:
                    caller_file = _frame.filename
                    break
            if caller_file and os.path.isfile(caller_file):
                self._script_path = Path(caller_file).resolve()
                self._self_mode = True
                _info(f'Mode: "self" — packaging the calling script.')
                _info(f"Script: {self._script_path}")
                _info("pyxwizard commands will be stripped from the packaged copy.")
            else:
                _error(f"Could not resolve calling script path: {caller_file}")
                raise FileNotFoundError(f"Cannot resolve 'self' to a script file: {caller_file}")
        else:
            resolved = Path(script_path).resolve()
            if not resolved.exists():
                _error(f"Script not found: {resolved}")
                raise FileNotFoundError(f"Script not found: {resolved}")
            if not resolved.suffix == ".py":
                _warn(f"File does not have .py extension: {resolved}")
            self._script_path = resolved
            self._self_mode = False
            _info(f"Script: {self._script_path}")

        # Detect imports
        self._detected_imports = detect_script_imports(self._script_path)
        if self._detected_imports:
            _info(f"Detected {len(self._detected_imports)} third-party import(s):")
            for imp in self._detected_imports:
                cat = _get_category(imp)
                cat_str = f"  [{cat}]" if cat else ""
                _detail(f"  • {imp}{cat_str}")
        else:
            _info("No third-party imports detected (standard library only).")

        file_size = self._script_path.stat().st_size
        _info(f"Script size: {file_size:,} bytes")

    def name(self, project_name: str) -> None:
        """Set the project/executable name."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.name().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("PROJECT NAME")

        sanitised = re.sub(r'[^\w\-.]', '_', project_name.strip())
        if not sanitised:
            _error(f"Invalid project name: '{project_name}'")
            raise ValueError(f"Invalid project name: '{project_name}'")

        self._project_name = sanitised
        _info(f"Project name: {self._project_name}")

        if sanitised != project_name.strip():
            _warn(f"Name sanitised from '{project_name}' to '{sanitised}'")

        base_dir = self._get_base_dir()
        project_dir = base_dir / "PyX_Data" / sanitised
        _info(f"Output directory: {project_dir}")

        if project_dir.exists():
            _warn("Project directory already exists. Cleaned script will be overwritten; virtual environment will be reused.")

        existing = count_existing_projects(base_dir)
        _info(f"Existing projects in PyX_Data: {existing}")

    def author(self, author_name: str) -> None:
        """Set the author name (optional, default TRADELY.DEV)."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.author().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        self._author = author_name.strip() if author_name.strip() else DEFAULT_AUTHOR
        _header("AUTHOR")
        _info(f"Author set to: {self._author}")

    def console(self, enabled: bool = True) -> None:
        """Set console mode (True = show console, False = GUI-only/windowed)."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.console().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        self._console_mode = bool(enabled)
        _header("CONSOLE MODE")
        if self._console_mode:
            _info("Console mode: ON (console window will be shown)")
        else:
            _info("Console mode: OFF (no console window — GUI/windowed mode)")

    def icon(self, icon_path: str) -> None:
        """Set a custom .ico icon for the executable."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.icon().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("CUSTOM ICON")

        resolved = Path(icon_path).resolve()
        if not resolved.exists():
            _error(f"Icon file not found: {resolved}")
            raise FileNotFoundError(f"Icon file not found: {resolved}")
        if resolved.suffix.lower() != ".ico":
            _warn(f"Icon file is not .ico format: {resolved.suffix}")

        self._icon_path = str(resolved)
        _info(f"Custom icon: {self._icon_path}")
        _info(f"Icon size: {resolved.stat().st_size:,} bytes")

    def data(self, *folder_paths: str) -> None:
        """Add data folders to bundle into the executable."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.data().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("DATA FOLDERS")

        if not folder_paths:
            _info("No data folders specified.")
            return

        total_bytes = 0
        for fp in folder_paths:
            resolved = Path(fp).resolve()
            if not resolved.exists():
                _error(f"Data folder not found: {resolved}")
                raise FileNotFoundError(f"Data folder not found: {resolved}")
            if not resolved.is_dir():
                _error(f"Path is not a directory: {resolved}")
                raise NotADirectoryError(f"Not a directory: {resolved}")

            size = folder_size(resolved)
            total_bytes += size
            size_mb = size / (1024 * 1024)
            self._data_folders.append(resolved)
            marker = "  ⚠ (>50 MB — large!)" if size_mb > 50 else ""
            _info(f"Added: {resolved}")
            _detail(f"  → bundled as '{resolved.name}/' ({size_mb:.1f} MB){marker}")

        total_mb = total_bytes / (1024 * 1024)
        _info(f"Total data size: {total_mb:.1f} MB across {len(folder_paths)} folder(s)")

        if total_mb > 100:
            _warn("Total data exceeds 100 MB. The EXE may be very large.")

    def cert(self, certificate_path: str, password: str, signtool_path: Optional[str] = None) -> None:
        """Set a PFX/P12 certificate for code signing."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.cert().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("CODE SIGNING CERTIFICATE")

        resolved = Path(certificate_path).resolve()
        if not resolved.exists():
            _error(f"Certificate file not found: {resolved}")
            raise FileNotFoundError(f"Certificate not found: {resolved}")

        self._pfx_path = resolved
        self._pfx_password = password
        _info(f"Certificate: {self._pfx_path}")

        if signtool_path:
            st = Path(signtool_path).resolve()
            if not st.exists():
                _warn(f"signtool.exe not found at: {st}")
            else:
                _info(f"signtool.exe: {st}")
            self._signtool_path = str(st)

        # Validate if cryptography is available
        if CRYPTOGRAPHY_AVAILABLE:
            _info("Validating certificate...")
            if validate_pfx(self._pfx_path, self._pfx_password):
                _success("Certificate validated successfully.")
            else:
                _error("Certificate validation failed (bad password or corrupted file).")
                _warn("Signing will still be attempted during build.")
        else:
            _warn("'cryptography' package not installed — cannot pre-validate certificate.")
            _info("Signing will be attempted during build regardless.")

    def outlocation(self, path: str) -> None:
        """Set the output location where PyX_Data will be created."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.outlocation().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        _header("OUTPUT LOCATION")

        resolved = Path(path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        self._out_location = resolved
        _info(f"Output base: {self._out_location}")
        _info(f"PyX_Data will be created at: {self._out_location / 'PyX_Data'}")

    def build(self) -> Optional[Path]:
        """
        Execute the full build process. Returns the path to the built
        executable on success, or None on failure.
        """
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.build().")
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._script_path is None:
            _error("No script specified. Call pyxwizard.location() first.")
            raise RuntimeError("No script specified.")
        if self._project_name is None:
            _error("No project name specified. Call pyxwizard.name() first.")
            raise RuntimeError("No project name specified.")

        # =====================================================================
        _header("BUILD STARTED")
        # =====================================================================
        S = _TermStyle
        print()
        print(f"  {S.BOLD}{S.WHITE}Project:  {S.GREEN}{self._project_name}{S.RESET}")
        print(f"  {S.BOLD}{S.WHITE}Script:   {S.RESET}{self._script_path}")
        print(f"  {S.BOLD}{S.WHITE}Author:   {S.RESET}{self._author}")
        print(f"  {S.BOLD}{S.WHITE}Console:  {S.RESET}{'Yes' if self._console_mode else 'No'}")
        print(f"  {S.BOLD}{S.WHITE}Icon:     {S.RESET}{self._icon_path or '(default Tradely)'}")
        print(f"  {S.BOLD}{S.WHITE}Data:     {S.RESET}{len(self._data_folders)} folder(s)")
        print(f"  {S.BOLD}{S.WHITE}Signing:  {S.RESET}{'Yes' if self._pfx_path else 'No'}")
        print()

        base_dir = self._get_base_dir()
        pyx_data_dir = base_dir / "PyX_Data"
        project_dir = pyx_data_dir / self._project_name
        temp_dir: Optional[Path] = None
        signed = False
        build_start = time.time()

        self._log_lines = []

        try:
            # =================================================================
            # STEP 1: Project structure
            # =================================================================
            _progress_bar("Creating project structure...", 0.05)
            self._log(f"=== PyX Wizard v{APP_VERSION} Build Started ===")
            self._log(f"Project: {self._project_name}")
            self._log(f"Script: {self._script_path}")
            self._log(f"Author: {self._author}")
            self._log(f"Timestamp: {datetime.datetime.now().isoformat()}")
            self._log("")

            for subfolder_name in ["venv", "build", "dist", "logs"]:
                subfolder = project_dir / subfolder_name
                subfolder.mkdir(parents=True, exist_ok=True)
                self._log(f"Ensured directory: {subfolder}")

            _progress_bar("Project structure created", 0.10)

            # =================================================================
            # STEP 2: Virtual environment
            # =================================================================
            _header("VIRTUAL ENVIRONMENT")
            _progress_bar("Setting up virtual environment...", 0.12)
            self._log("")
            self._log("--- Virtual Environment ---")
            python_exe = create_project_venv(project_dir, self._log)
            _success(f"Virtual environment ready: {python_exe}")
            _progress_bar("Virtual environment ready", 0.20)

            # =================================================================
            # STEP 3: Upgrade pip
            # =================================================================
            _header("UPGRADING PIP")
            _progress_bar("Upgrading pip...", 0.22)
            self._log("")
            self._log("--- Upgrading pip ---")
            try:
                run_cmd(
                    [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
                    self._log
                )
                _success("pip upgraded.")
            except subprocess.CalledProcessError as pip_error:
                self._log(f"WARNING: pip upgrade failed: {pip_error}")
                _warn(f"pip upgrade failed: {pip_error}")
            _progress_bar("pip ready", 0.25)

            # =================================================================
            # STEP 4: PyInstaller
            # =================================================================
            _header("PYINSTALLER CHECK")
            _progress_bar("Checking PyInstaller...", 0.28)
            self._log("")
            self._log("--- PyInstaller ---")
            if not venv_has_package(python_exe, "PyInstaller"):
                _info("PyInstaller not found. Installing...")
                self._log("PyInstaller not found in venv. Installing...")
                venv_pip_install(python_exe, "pyinstaller", log=self._log)
                _success("PyInstaller installed.")
            else:
                self._log("PyInstaller is already installed.")
                _success("PyInstaller already installed.")
            _progress_bar("PyInstaller ready", 0.35)

            # =================================================================
            # STEP 5: Dependencies
            # =================================================================
            _header("DEPENDENCIES")
            _progress_bar("Installing dependencies...", 0.38)
            self._log("")
            self._log("--- Dependencies ---")
            install_script_deps(python_exe, self._script_path, self._log)
            _success("Dependencies resolved.")
            _progress_bar("Dependencies installed", 0.45)

            # =================================================================
            # STEP 6: Preprocess script
            # =================================================================
            _header("SCRIPT PREPROCESSING")
            _progress_bar("Preprocessing script...", 0.48)
            self._log("")
            self._log("--- Script Preprocessing ---")
            temp_dir = Path(tempfile.mkdtemp(prefix="pyx_build_"))

            if self._self_mode:
                # Strip pyxwizard commands first, then preprocess
                _info("Stripping pyxwizard commands from self-referencing script...")
                self._log("Stripping pyxwizard library calls from script (self mode)...")
                stripped_script = _strip_pyxwizard_from_script(self._script_path, temp_dir)
                # Save the cleaned script into the PyX_Data project folder,
                # overwriting any previous copy so stale files are never reused.
                cleaned_in_project = project_dir / self._script_path.name
                cleaned_in_project.write_text(
                    stripped_script.read_text(encoding="utf-8"), encoding="utf-8"
                )
                self._log(f"Cleaned script written to: {cleaned_in_project}")
                _info(f"Cleaned script saved → {cleaned_in_project}")
                preprocessed_script = preprocess_script(stripped_script, temp_dir)
            else:
                preprocessed_script = preprocess_script(self._script_path, temp_dir)

            self._log(f"Preprocessed script: {preprocessed_script}")
            _success(f"Script preprocessed → {preprocessed_script.name}")
            _progress_bar("Script preprocessed", 0.50)

            # =================================================================
            # STEP 7: Icon
            # =================================================================
            effective_icon: Optional[str] = self._icon_path
            if effective_icon is None or not Path(effective_icon).exists():
                _header("ICON")
                _info("No custom icon. Downloading default...")
                self._log("")
                self._log("--- Icon ---")
                self._log("No custom icon provided. Downloading default icon...")
                effective_icon = _download_icon(base_dir)
                if effective_icon:
                    self._log(f"Default icon: {effective_icon}")
                    _success(f"Default icon ready: {effective_icon}")
                else:
                    self._log("WARNING: Could not download default icon.")
                    _warn("Building without icon.")

            # =================================================================
            # STEP 8: PyInstaller build
            # =================================================================
            _header("PYINSTALLER BUILD")
            _progress_bar("Running PyInstaller...", 0.55)
            self._log("")
            self._log("--- PyInstaller Build ---")

            pyinstaller_cmd: List[str] = [
                str(python_exe), "-m", "PyInstaller"
            ]
            pyinstaller_cmd.extend(PYINSTALLER_FLAGS)
            pyinstaller_cmd.extend(["--name", self._project_name])
            pyinstaller_cmd.extend(["--distpath", str(project_dir / "dist")])
            pyinstaller_cmd.extend(["--workpath", str(project_dir / "build")])

            if not self._console_mode:
                pyinstaller_cmd.append("--noconsole")

            if effective_icon and Path(effective_icon).exists():
                pyinstaller_cmd.extend(["--icon", effective_icon])

            # Hidden imports (sanitised)
            detected_imports = self._detected_imports
            for import_name in detected_imports:
                top_level = import_name.split(".")[0]
                if top_level.isidentifier() and top_level.lower() != "pyinstaller":
                    pyinstaller_cmd.extend(["--hidden-import", top_level])

            # Collect-all for packages with dynamic imports
            _COLLECT_ALL_PACKAGES: Set[str] = {
                "OpenGL", "glfw", "moderngl", "vispy", "pyglet",
                "pygame", "wx", "PyQt5", "PyQt6", "PySide2", "PySide6", "kivy",
                "PIL", "cv2", "imageio", "skimage",
                "sklearn", "scipy", "matplotlib", "numba", "shapely",
                "cryptography", "cffi", "nacl",
                "pkg_resources", "importlib_resources", "importlib_metadata",
            }
            if _lib_collect_all:
                _COLLECT_ALL_PACKAGES |= _lib_collect_all

            collected_tops = {imp.split(".")[0] for imp in detected_imports}

            for pkg in _COLLECT_ALL_PACKAGES:
                if pkg in collected_tops:
                    pyinstaller_cmd.extend(["--collect-all", pkg])
                    self._log(f"collect-all: {pkg}")

            for pkg, hidden_list in _lib_hidden_imports.items():
                if pkg in collected_tops:
                    for hi in hidden_list:
                        pyinstaller_cmd.extend(["--hidden-import", hi])
                    self._log(f"hidden-imports ({pkg}): {', '.join(hidden_list)}")

            for imp_name, dist_name in _lib_copy_metadata.items():
                if imp_name in collected_tops:
                    pyinstaller_cmd.extend(["--copy-metadata", dist_name])
                    self._log(f"copy-metadata: {dist_name}")

            # Data folders
            separator = ";" if platform.system() == "Windows" else ":"
            for data_folder in self._data_folders:
                dest_name = data_folder.name
                add_data_arg = f"{data_folder}{separator}{dest_name}"
                pyinstaller_cmd.extend(["--add-data", add_data_arg])
                self._log(f"add-data: {add_data_arg}")

            pyinstaller_cmd.append(str(preprocessed_script))

            self._log(f"Command: {' '.join(str(c) for c in pyinstaller_cmd)}")
            self._log("")

            _info("PyInstaller command assembled. Building...")

            try:
                run_cmd(pyinstaller_cmd, self._log, cwd=str(project_dir))
            except subprocess.CalledProcessError:
                self._log("WARNING: PyInstaller failed with uppercase. Trying lowercase...")
                _warn("Retrying with lowercase module name...")
                pyinstaller_cmd_retry = [
                    str(python_exe), "-m", "pyinstaller"
                ] + pyinstaller_cmd[3:]
                run_cmd(pyinstaller_cmd_retry, self._log, cwd=str(project_dir))

            _progress_bar("PyInstaller finished", 0.80)
            _success("PyInstaller build completed.")

            # =================================================================
            # STEP 9: Locate executable
            # =================================================================
            _header("LOCATING EXECUTABLE")
            self._log("")
            self._log("--- Locating Executable ---")

            dist_dir = project_dir / "dist"
            exe_name = self._project_name + (".exe" if platform.system() == "Windows" else "")
            exe_path = dist_dir / exe_name

            if not exe_path.exists():
                possible_exes = list(dist_dir.glob("*"))
                if possible_exes:
                    exe_path = possible_exes[0]
                    self._log(f"Found executable: {exe_path}")
                    _info(f"Executable found: {exe_path}")
                else:
                    raise FileNotFoundError(
                        f"No executable found in {dist_dir}. Build may have failed."
                    )
            else:
                self._log(f"Executable located: {exe_path}")
                _success(f"Executable: {exe_path}")

            exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
            _info(f"Executable size: {exe_size_mb:.1f} MB")
            _progress_bar("Executable located", 0.85)

            # =================================================================
            # STEP 10: Code signing
            # =================================================================
            _header("CODE SIGNING")
            if self._pfx_path is not None and self._pfx_password is not None:
                self._log("")
                self._log("--- Code Signing ---")
                _info("Signing executable...")
                try:
                    sign_exe(
                        exe_path, self._pfx_path, self._pfx_password,
                        self._log, self._signtool_path
                    )
                    signed = True
                    _success("Executable signed successfully.")
                except Exception as sign_error:
                    self._log(f"WARNING: Code signing failed: {sign_error}")
                    _warn(f"Code signing failed: {sign_error}")
                    signed = False
            else:
                self._log("")
                self._log("--- Code Signing ---")
                self._log("No certificate provided. Skipping.")
                _info("No certificate provided. Skipping code signing.")

            _progress_bar("Signing step complete", 0.90)

            # =================================================================
            # STEP 11: Manifest
            # =================================================================
            _header("MANIFEST")
            self._log("")
            self._log("--- Manifest ---")
            manifest_data = {
                "created": datetime.datetime.now().isoformat(),
                "author": self._author,
                "project": self._project_name,
                "script": str(self._script_path),
                "exe": str(exe_path),
                "signed": signed,
                "pyx_version": APP_VERSION,
                "console_mode": self._console_mode,
                "data_folders": [str(f) for f in self._data_folders],
            }
            write_manifest(project_dir, manifest_data)
            self._log(f"Manifest: {project_dir / 'pyx_manifest.json'}")
            _success(f"Manifest written: {project_dir / 'pyx_manifest.json'}")

            # =================================================================
            # STEP 12: Build log
            # =================================================================
            self._log("")
            self._log("--- Build Log ---")
            write_build_log(project_dir, self._log_lines)
            self._log(f"Log saved to: {project_dir / 'logs'}")

            _progress_bar("Build complete", 1.0)

            # =================================================================
            # BUILD COMPLETE
            # =================================================================
            elapsed = time.time() - build_start
            self._log("")
            self._log(f"=== BUILD SUCCESSFUL ===")
            self._log(f"Executable: {exe_path}")
            self._log(f"Build time: {elapsed:.1f}s")

            print()
            print(f"  {S.GREEN}{S.BOLD}╔══════════════════════════════════════════════════╗{S.RESET}")
            print(f"  {S.GREEN}{S.BOLD}║              BUILD SUCCESSFUL                    ║{S.RESET}")
            print(f"  {S.GREEN}{S.BOLD}╚══════════════════════════════════════════════════╝{S.RESET}")
            print()
            _success(f"Executable:  {exe_path}")
            _success(f"Size:        {exe_size_mb:.1f} MB")
            _success(f"Signed:      {'Yes' if signed else 'No'}")
            _success(f"Build time:  {elapsed:.1f}s")
            _success(f"Log folder:  {project_dir / 'logs'}")
            print()

            # Print full log summary
            _header("FULL BUILD LOG")
            print()
            for line in self._log_lines:
                print(f"  {S.GREY}{line}{S.RESET}")
            print()

            return exe_path

        except Exception as build_error:
            self._log("")
            self._log(f"=== BUILD FAILED ===")
            self._log(f"Error: {build_error}")

            # Write log even on failure
            try:
                if project_dir.exists():
                    write_build_log(project_dir, self._log_lines)
            except Exception:
                pass

            elapsed = time.time() - build_start

            print()
            print(f"  {S.RED}{S.BOLD}╔══════════════════════════════════════════════════╗{S.RESET}")
            print(f"  {S.RED}{S.BOLD}║              BUILD FAILED                        ║{S.RESET}")
            print(f"  {S.RED}{S.BOLD}╚══════════════════════════════════════════════════╝{S.RESET}")
            print()
            _error(f"Error: {build_error}")
            _error(f"Build time: {elapsed:.1f}s")
            _info(f"Check logs at: {project_dir / 'logs'}")
            print()

            # Print full log
            _header("FULL BUILD LOG")
            print()
            for line in self._log_lines:
                print(f"  {S.GREY}{line}{S.RESET}")
            print()

            return None

        finally:
            if temp_dir is not None and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    self._log(f"WARNING: Could not clean up temp dir: {cleanup_error}")


# =============================================================================
# MODULE-LEVEL SINGLETON & PUBLIC API
# =============================================================================
_wizard = _PyXWizard()


def begin() -> None:
    """Initialise PyX Wizard. Must be called before any other pyxwizard command."""
    _wizard.begin()


def location(script_path: str) -> None:
    """
    Set the Python script to package.

    Parameters
    ----------
    script_path : str
        Path to the .py file, or "self" to package the calling script
        (pyxwizard commands will be stripped automatically).
    """
    _wizard.location(script_path)


def name(project_name: str) -> None:
    """Set the project name (used as the executable filename)."""
    _wizard.name(project_name)


def author(author_name: str = DEFAULT_AUTHOR) -> None:
    """Set the author name (optional, default TRADELY.DEV)."""
    _wizard.author(author_name)


def console(enabled: bool = True) -> None:
    """Set console mode (True = show console, False = GUI-only)."""
    _wizard.console(enabled)


def icon(icon_path: str) -> None:
    """Set a custom .ico icon for the executable."""
    _wizard.icon(icon_path)


def data(*folder_paths: str) -> None:
    """
    Add data folders to bundle into the executable.

    Files in bundled folders can be accessed at runtime using:
        "packaged-within-exe:folder_name/file.ext"
    """
    _wizard.data(*folder_paths)


def cert(
    certificate_path: str,
    password: str,
    signtool_path: Optional[str] = None
) -> None:
    """
    Set a PFX/P12 certificate for code signing.

    Parameters
    ----------
    certificate_path : str
        Path to the .pfx or .p12 certificate file.
    password : str
        The certificate password.
    signtool_path : str, optional
        Path to signtool.exe (auto-detected if not provided).
    """
    _wizard.cert(certificate_path, password, signtool_path)


def outlocation(path: str) -> None:
    """Set the base directory where PyX_Data/ will be created."""
    _wizard.outlocation(path)


def build() -> Optional[Path]:
    """
    Execute the full build process.

    Returns
    -------
    Path or None
        The path to the built executable on success, or None on failure.
    """
    return _wizard.build()
