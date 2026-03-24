#!/usr/bin/env python3

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
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Set, Tuple

# =============================================================================
# IMPORTS – Third-party (customtkinter and tkinter)
# =============================================================================
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk

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
# CONSTANTS – Version and Author
# =============================================================================
APP_VERSION = "BETA 0.28"
DEFAULT_AUTHOR = "TRADELY.DEV"

# =============================================================================
# CONSTANTS – Step Labels
# =============================================================================
STEP_LABELS = ["Welcome", "Script", "Config", "Data", "Certificate", "Build"]

# =============================================================================
# CONSTANTS – PyInstaller Flags
# =============================================================================
PYINSTALLER_FLAGS = ["--onefile", "--clean", "--noconfirm"]

# =============================================================================
# CONSTANTS – Default Icon URL
# =============================================================================
DEFAULT_ICON_URL = (
    "https://doc.tradely.dev/images/tradely.ico"
)

SIGNTOOL_RELATIVE_PATH = "signtool/signtool.exe"

# =============================================================================
# CONSTANTS – Library Categories Remote File
# Update this URL to point to your hosted lib_categories.json to push new
# category/library data without shipping a new executable.
# =============================================================================
LIBRARIES_CATEGORY_FILE = (
    "https://doc.tradely.dev/PyX/lib_categories.json"
)

# =============================================================================
# GLOBALS – Fetched Library Data (populated from LIBRARIES_CATEGORY_FILE)
# _lib_categories      : lowercase library name → category label
# _lib_collect_all     : packages that need --collect-all passed to PyInstaller
# _lib_hidden_imports  : package name → list of --hidden-import values
# _lib_copy_metadata   : import name → pip distribution name for --copy-metadata
#                        (e.g. {"sklearn": "scikit-learn"} — for packages that
#                        read their own metadata at runtime, or whose import
#                        name differs from their pip name)
# _lib_categories_loaded: True when the remote file was fetched successfully
# =============================================================================
_lib_categories: Dict[str, str] = {}
_lib_collect_all: Set[str] = set()
_lib_hidden_imports: Dict[str, List[str]] = {}
_lib_copy_metadata: Dict[str, str] = {}
_lib_categories_loaded: bool = False

# =============================================================================
# CONSTANTS – Colour Scheme (Dark Green Theme)
# =============================================================================
COL_BG = "#0a0f0a"             # Main background
COL_PANEL = "#0d1a0d"          # Sidebar panel background
COL_CARD = "#111f11"           # Card background
COL_ACCENT = "#2d9e2d"        # Accent colour for buttons and progress
COL_ACCENT_HOVER = "#27882a"  # Accent hover colour
COL_ACCENT_LIGHT = "#3dbe3d"  # Lighter accent
COL_SUCCESS = "#4ade80"        # Success indicator
COL_WARNING = "#fbbf24"        # Warning indicator
COL_ERROR = "#f87171"          # Error indicator
COL_TEXT = "#e8f5e8"           # Primary text colour
COL_MUTED = "#5a7a5a"         # Muted text colour
COL_BORDER = "#1e3a1e"        # Border colour
COL_LOG_BG = "#080e08"        # Log area background

# =============================================================================
# CONSTANTS – Font Definitions
# =============================================================================
FONT_TITLE = ("Consolas", 22, "bold")
FONT_HEADER = ("Consolas", 14, "bold")
FONT_BODY = ("Consolas", 11)
FONT_MONO = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)
FONT_STEP_LABEL = ("Consolas", 11)

# =============================================================================
# CONSTANTS – Standard Library Module Names (comprehensive list for Python 3)
# This set is used to exclude standard library modules from dependency detection.
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
    # Additional commonly encountered standard library modules and subpackages
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
    # Subpackages that should not trigger pip install
    "encodings", "collections", "concurrent", "email", "html", "http",
    "importlib", "logging", "multiprocessing", "unittest", "urllib",
    "xml", "xmlrpc", "ctypes", "curses", "dbm", "distutils", "json",
    "lib2to3", "test", "tkinter", "idlelib",
    # Commonly confused modules
    "copy", "io", "os", "re", "sys", "time", "math", "random",
    "typing", "dataclasses", "enum", "abc", "functools", "itertools",
    "operator", "contextlib", "pathlib", "subprocess",
    # Windows-specific standard library modules
    "msilib", "msvcrt", "winreg", "winsound",
    # Internal and private standard library modules
    "__main__", "__phello__",
    # Additional modules for broader coverage
    "ensurepip", "pip", "setuptools", "pkg_resources",
    "pydoc_data", "turtledemo",
    "zoneinfo", "graphlib", "tomllib",
}

# =============================================================================
# CONSTANTS – Injected helper code for packaged-within-exe path resolution
# This exact code block is injected into target scripts during preprocessing.
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
# HELPER FUNCTION – Path Resolution (for the PyX Wizard itself)
# =============================================================================
def _resolve_packaged_path(relative_path: str) -> Path:
    """
    Resolve a path to a resource bundled alongside this script or frozen exe.

    If the program is frozen (compiled via PyInstaller), resources are found
    inside sys._MEIPASS. Otherwise they are relative to this script file.

    Parameters
    ----------
    relative_path : str
        The relative path to the resource (for example "signtool/signtool.exe").

    Returns
    -------
    Path
        The fully resolved absolute Path to the resource.
    """
    if getattr(sys, "frozen", False):
        # Running as a frozen executable – resources are in the temporary
        # extraction directory provided by PyInstaller.
        base = Path(sys._MEIPASS)
    else:
        # Running as a normal Python script – resources are relative to
        # this script file.
        base = Path(__file__).parent
    return base / relative_path


def _get_base_dir() -> Path:
    """
    Return the base directory of this application.
    When frozen, this is the directory containing the executable.
    When running as a script, this is the directory containing this .py file.

    Returns
    -------
    Path
        The base directory for PyX_Data and other relative outputs.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent


# =============================================================================
# HELPER FUNCTION – Fetch Library Categories from Remote JSON
# =============================================================================
def _fetch_lib_categories() -> bool:
    """
    Download LIBRARIES_CATEGORY_FILE and populate all library globals.

    Expected JSON shape::

        {
            "collect_all": ["OpenGL", "sklearn", ...],
            "hidden_imports": {
                "sklearn": ["sklearn.utils._cython_blas", ...],
                "cv2":     ["cv2"],
                ...
            },
            "categories": {
                "Data Science": ["numpy", "pandas", ...],
                "Web":          ["requests", "flask", ...],
                ...
            }
        }

    Returns True on success, False if the fetch fails for any reason.
    """
    global _lib_categories, _lib_collect_all, _lib_hidden_imports, _lib_copy_metadata, _lib_categories_loaded
    try:
        with urllib.request.urlopen(LIBRARIES_CATEGORY_FILE, timeout=6) as resp:
            data: Dict[str, Any] = json.loads(resp.read().decode("utf-8"))

        # --- categories ---
        mapping: Dict[str, str] = {}
        for cat_name, libs in data.get("categories", {}).items():
            if isinstance(libs, list):
                for lib in libs:
                    mapping[str(lib).lower()] = cat_name
        _lib_categories = mapping

        # --- collect_all ---
        collect_all = data.get("collect_all", [])
        if isinstance(collect_all, list):
            _lib_collect_all = set(collect_all)

        # --- hidden_imports ---
        hidden = data.get("hidden_imports", {})
        if isinstance(hidden, dict):
            _lib_hidden_imports = {
                pkg: entries
                for pkg, entries in hidden.items()
                if isinstance(entries, list)
            }

        # --- copy_metadata ---
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


# =============================================================================
# HELPER FUNCTION – Detect Script Imports
# =============================================================================
def detect_script_imports(script_path: Path) -> List[str]:
    """
    Parse the given Python script and extract all top-level import names.
    Apply sanitisation rules:
      - 'import numpy as np' yields 'numpy'
      - 'from tkinter import *' yields 'tkinter'
      - Only the top-level package name is kept (os.path yields os)
      - Only valid Python identifiers are kept
      - Standard library modules (in _STDLIB_SKIP) are excluded
      - 'pyinstaller' is excluded

    Parameters
    ----------
    script_path : Path
        The path to the Python script to analyse.

    Returns
    -------
    List[str]
        A sorted list of unique third-party top-level package names.
    """
    imports: Set[str] = set()
    try:
        source_code = script_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source_code, filename=str(script_path))
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as parse_error:
        # If the script cannot be parsed, return an empty list and log
        # the issue rather than crashing.
        print(f"Warning: could not parse {script_path}: {parse_error}")
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # Handle: import numpy, import numpy as np, import os.path
            for alias in node.names:
                top_level_name = alias.name.split(".")[0]
                imports.add(top_level_name)
        elif isinstance(node, ast.ImportFrom):
            # Handle: from tkinter import *, from os.path import join
            if node.module is not None:
                top_level_name = node.module.split(".")[0]
                imports.add(top_level_name)

    # Filter: keep only valid identifiers, exclude stdlib and pyinstaller
    sanitised: List[str] = []
    for name in sorted(imports):
        if not name.isidentifier():
            continue
        if name.lower() in {item.lower() for item in _STDLIB_SKIP}:
            continue
        if name.lower() == "pyinstaller":
            continue
        sanitised.append(name)

    return sanitised


# =============================================================================
# HELPER FUNCTION – Folder Size
# =============================================================================
def folder_size(path: Path) -> int:
    """
    Calculate the total size of all files within a directory (recursively).

    Parameters
    ----------
    path : Path
        The directory path to measure.

    Returns
    -------
    int
        Total size in bytes.
    """
    total_bytes = 0
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_bytes += item.stat().st_size
                except OSError:
                    pass
    return total_bytes


# =============================================================================
# HELPER FUNCTION – Write Manifest
# =============================================================================
def write_manifest(project_dir: Path, meta: dict) -> None:
    """
    Write a JSON manifest file (pyx_manifest.json) into the project directory.

    Parameters
    ----------
    project_dir : Path
        The root directory of the project (for example PyX_Data/MyApp/).
    meta : dict
        A dictionary containing manifest fields such as 'created', 'author',
        'project', 'script', 'exe', and 'signed'.
    """
    manifest_path = project_dir / "pyx_manifest.json"
    manifest_path.write_text(
        json.dumps(meta, indent=4, default=str),
        encoding="utf-8"
    )


# =============================================================================
# HELPER FUNCTION – Write Build Log
# =============================================================================
def write_build_log(project_dir: Path, log_lines: List[str]) -> None:
    """
    Write the build log to a timestamped text file inside the project's
    logs/ subdirectory.

    Parameters
    ----------
    project_dir : Path
        The root directory of the project.
    log_lines : List[str]
        A list of log line strings to write to the file.
    """
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"build_{timestamp_str}.txt"
    log_file.write_text("\n".join(log_lines), encoding="utf-8")


# =============================================================================
# HELPER FUNCTION – Validate PFX Certificate
# =============================================================================
def validate_pfx(pfx_path: Path, password: str) -> bool:
    """
    Attempt to load and validate a PFX/P12 certificate file using the
    cryptography library. Returns True if the certificate and password
    are valid, False otherwise.

    If the cryptography library is not available, this function returns False.

    Parameters
    ----------
    pfx_path : Path
        Path to the .pfx or .p12 certificate file.
    password : str
        The password for the certificate.

    Returns
    -------
    bool
        True if the certificate was loaded successfully, False otherwise.
    """
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


# =============================================================================
# HELPER FUNCTION – Run Command (subprocess with streaming output)
# =============================================================================
def run_cmd(cmd: List[str], log: Callable[[str], None], cwd: Optional[str] = None) -> None:
    """
    Execute a subprocess command and stream its stdout and stderr to the
    provided log callback function line by line.

    Parameters
    ----------
    cmd : List[str]
        The command and arguments to execute.
    log : Callable[[str], None]
        A callback function that accepts a single string argument for logging.
    cwd : Optional[str]
        Working directory for the subprocess. Defaults to None (inherit CWD).

    Raises
    ------
    subprocess.CalledProcessError
        If the command exits with a non-zero return code.
    """
    log(f"Running: {' '.join(str(c) for c in cmd)}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        cwd=cwd,
        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
    )
    output_lines: List[str] = []
    for line in process.stdout:
        stripped_line = line.rstrip("\n\r")
        output_lines.append(stripped_line)
        log(stripped_line)
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode,
            cmd,
            output="\n".join(output_lines)
        )


# =============================================================================
# HELPER FUNCTION – Create or Reuse Project Virtual Environment
# =============================================================================
def create_project_venv(project_dir: Path, log: Callable[[str], None]) -> Path:
    """
    Create a new virtual environment inside the project directory, or reuse
    an existing one if it already exists.

    Parameters
    ----------
    project_dir : Path
        The root directory of the project (for example PyX_Data/MyApp/).
    log : Callable[[str], None]
        A callback function for logging messages.

    Returns
    -------
    Path
        The path to the Python executable inside the virtual environment.
    """
    venv_dir = project_dir / "venv"

    # Determine the Python executable path based on the operating system
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if python_exe.exists():
        log(f"Reusing existing virtual environment: {venv_dir}")
    else:
        log(f"Creating virtual environment: {venv_dir}")
        if getattr(sys, "frozen", False):
            # When running as a frozen EXE, sys.executable is the packaged
            # binary, not the Python interpreter.  venv.create() would fail
            # because it tries to bootstrap the venv from sys.executable.
            # Instead, locate the real interpreter on PATH and spawn it.
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


# =============================================================================
# HELPER FUNCTION – Pip Install Inside Virtual Environment
# =============================================================================
def venv_pip_install(
    python_exe: Path,
    *packages: str,
    log: Callable[[str], None]
) -> None:
    """
    Install one or more packages using pip inside the virtual environment.

    Parameters
    ----------
    python_exe : Path
        The path to the Python executable inside the virtual environment.
    *packages : str
        One or more package names to install.
    log : Callable[[str], None]
        A callback function for logging messages.
    """
    if not packages:
        return
    cmd = [str(python_exe), "-m", "pip", "install"] + list(packages)
    run_cmd(cmd, log)


# =============================================================================
# HELPER FUNCTION – Check if Package is Available in Virtual Environment
# =============================================================================
def venv_has_package(python_exe: Path, package: str) -> bool:
    """
    Check whether a given package can be imported inside the virtual
    environment by running a small test script.

    Parameters
    ----------
    python_exe : Path
        The path to the Python executable inside the virtual environment.
    package : str
        The name of the package to check.

    Returns
    -------
    bool
        True if the package is importable, False otherwise.
    """
    try:
        result = subprocess.run(
            [str(python_exe), "-c", f"import {package}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


# =============================================================================
# HELPER FUNCTION – Install Script Dependencies
# =============================================================================
def install_script_deps(
    python_exe: Path,
    script_path: Path,
    log: Callable[[str], None]
) -> None:
    """
    Detect all third-party imports in the target script and install any that
    are not already available in the virtual environment.

    Parameters
    ----------
    python_exe : Path
        The path to the Python executable inside the virtual environment.
    script_path : Path
        The path to the Python script to analyse.
    log : Callable[[str], None]
        A callback function for logging messages.
    """
    detected_imports = detect_script_imports(script_path)
    if not detected_imports:
        log("No third-party dependencies detected.")
        return

    log(f"Detected third-party imports: {', '.join(detected_imports)}")

    for package_name in detected_imports:
        if venv_has_package(python_exe, package_name):
            log(f"  Package '{package_name}' is already installed.")
        else:
            # Use the pip distribution name if known (e.g. sklearn → scikit-learn)
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


# =============================================================================
# HELPER FUNCTION – Sign Executable
# =============================================================================
def sign_exe(
    exe: Path,
    pfx: Path,
    pwd: str,
    log: Callable[[str], None]
) -> None:
    """
    Sign the built executable using signtool.exe with the provided PFX
    certificate and password.

    The path to signtool.exe is resolved using _resolve_packaged_path so
    that it works both when running as a script and when running as a
    frozen executable.

    Parameters
    ----------
    exe : Path
        The path to the executable file to sign.
    pfx : Path
        The path to the PFX/P12 certificate file.
    pwd : str
        The certificate password.
    log : Callable[[str], None]
        A callback function for logging messages.
    """
    signtool_path = _resolve_packaged_path(SIGNTOOL_RELATIVE_PATH)
    if not signtool_path.exists():
        log(
            f"WARNING: signtool.exe not found at {signtool_path}. "
            f"Skipping code signing."
        )
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


# =============================================================================
# HELPER FUNCTION – Download Default Icon
# =============================================================================
def _download_icon() -> Optional[str]:
    """
    Download the default icon from DEFAULT_ICON_URL and save it as
    default_icon.ico in the base directory of this script (or exe).

    Returns
    -------
    Optional[str]
        The path to the downloaded icon file as a string, or None if the
        download failed.
    """
    base_dir = _get_base_dir()
    icon_path = base_dir / "default_icon.ico"
    if icon_path.exists():
        return str(icon_path)
    try:
        urllib.request.urlretrieve(DEFAULT_ICON_URL, str(icon_path))
        return str(icon_path)
    except (urllib.error.URLError, OSError, Exception) as download_error:
        print(f"Warning: could not download default icon: {download_error}")
        return None


# =============================================================================
# HELPER FUNCTION – Open Folder in File Explorer
# =============================================================================
def _open_folder(path: Path) -> None:
    """
    Open the specified folder in the system's default file explorer.

    Parameters
    ----------
    path : Path
        The path to the folder to open.
    """
    folder_str = str(path)
    if platform.system() == "Windows":
        os.startfile(folder_str)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", folder_str])
    else:
        subprocess.Popen(["xdg-open", folder_str])


# =============================================================================
# HELPER FUNCTION – Preprocess Target Script
# =============================================================================
def preprocess_script(script_path: Path, temp_dir: Path) -> Path:
    """
    Create a preprocessed copy of the target script in the temporary directory.

    The preprocessing does two things:
    1. Injects the _resolve_packaged_path helper function after the last
       top-level import statement.
    2. Replaces all string literals of the form
       "packaged-within-exe:folder/file.ext" (both single and double quotes)
       with calls to _resolve_packaged_path("folder/file.ext").

    Parameters
    ----------
    script_path : Path
        The original script to preprocess.
    temp_dir : Path
        The temporary directory in which to place the preprocessed copy.

    Returns
    -------
    Path
        The path to the preprocessed script file.
    """
    source_code = script_path.read_text(encoding="utf-8", errors="replace")
    lines = source_code.split("\n")

    # -------------------------------------------------------------------------
    # Step 1: Determine whether the script already defines _resolve_packaged_path
    # as a real top-level function (not just as a string inside a constant).
    # Use ast so we are not fooled by the function name appearing inside string
    # literals (e.g. inside INJECTED_PATH_HELPER in the PyX wizard itself).
    # -------------------------------------------------------------------------
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
        # The script already owns its path-resolution logic.  Leave both the
        # helper injection and the literal replacement alone so we do not
        # generate a call to a function that may be defined later in the file.
        modified_source = source_code
    else:
        # ---------------------------------------------------------------------
        # Step 2: Find the position to inject the helper function.
        # We look for the last top-level import line (not indented).
        # ---------------------------------------------------------------------
        last_import_line_index = -1
        for line_index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                if not line[0:1].isspace():
                    last_import_line_index = line_index

        # ---------------------------------------------------------------------
        # Step 3: Inject the helper function if it is not already present.
        # Guard with the unique marker comment rather than the function name,
        # so we are not fooled by the name appearing in string constants.
        # ---------------------------------------------------------------------
        if "# --- PyX Wizard: injected path helper (start) ---" not in source_code:
            injection_position = last_import_line_index + 1 if last_import_line_index >= 0 else 0
            helper_lines = INJECTED_PATH_HELPER.split("\n")
            for offset, helper_line in enumerate(helper_lines):
                lines.insert(injection_position + offset, helper_line)

        modified_source = "\n".join(lines)

        # ---------------------------------------------------------------------
        # Step 4: Replace "packaged-within-exe:..." literals with function calls.
        # Pattern explanation:
        #   (?P<quote>["'])           - Match opening quote (single or double)
        #   packaged-within-exe:     - The literal prefix
        #   (?P<relpath>[^"']+)      - Capture the relative path (no quotes)
        #   (?P=quote)               - Match the same closing quote
        # ---------------------------------------------------------------------
        packaged_pattern = re.compile(
            r"""(?P<quote>["'])packaged-within-exe:(?P<relpath>[^"']+)(?P=quote)"""
        )
        modified_source = packaged_pattern.sub(
            r'_resolve_packaged_path("\g<relpath>")',
            modified_source
        )

    # -------------------------------------------------------------------------
    # Step 5: Write the preprocessed script to the temporary directory.
    # -------------------------------------------------------------------------
    temp_script_path = temp_dir / script_path.name
    temp_script_path.write_text(modified_source, encoding="utf-8")

    return temp_script_path


# =============================================================================
# HELPER FUNCTION – Count Existing Projects
# =============================================================================
def count_existing_projects() -> int:
    """
    Count the number of existing project directories inside PyX_Data/.

    Returns
    -------
    int
        The number of subdirectories inside PyX_Data/.
    """
    pyx_data_dir = _get_base_dir() / "PyX_Data"
    if not pyx_data_dir.exists():
        return 0
    return sum(1 for item in pyx_data_dir.iterdir() if item.is_dir())


# =============================================================================
# CLASS – Sidebar
# =============================================================================
class Sidebar(ctk.CTkFrame):
    """
    The sidebar frame displayed on the left side of the wizard window.
    It shows the PyX logo, step indicators, output folder path, project count,
    and version number.
    """

    def __init__(self, master: Any, **kwargs: Any) -> None:
        """
        Initialise the sidebar with all visual elements.

        Parameters
        ----------
        master : Any
            The parent widget.
        """
        super().__init__(master, width=220, corner_radius=0, fg_color=COL_PANEL, **kwargs)

        # Prevent the frame from shrinking to fit its children
        self.pack_propagate(False)

        # ----- Logo Section -----
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=(25, 5), padx=15, anchor="w")

        self.logo_label = ctk.CTkLabel(
            logo_frame,
            text="PyX",
            font=("Consolas", 28, "bold"),
            text_color=COL_ACCENT_LIGHT
        )
        self.logo_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="EXE Builder",
            font=FONT_SMALL,
            text_color=COL_MUTED
        )
        self.subtitle_label.pack(anchor="w")

        # ----- Separator -----
        separator = ctk.CTkFrame(self, height=1, fg_color=COL_BORDER)
        separator.pack(fill="x", padx=15, pady=(10, 15))

        # ----- Step Indicators -----
        self.step_labels: List[ctk.CTkLabel] = []
        self.step_dots: List[ctk.CTkLabel] = []
        for step_index, step_name in enumerate(STEP_LABELS):
            step_row = ctk.CTkFrame(self, fg_color="transparent")
            step_row.pack(fill="x", padx=15, pady=3)

            dot_label = ctk.CTkLabel(
                step_row,
                text="○",
                font=FONT_STEP_LABEL,
                text_color=COL_MUTED,
                width=20
            )
            dot_label.pack(side="left", padx=(0, 8))
            self.step_dots.append(dot_label)

            name_label = ctk.CTkLabel(
                step_row,
                text=step_name,
                font=FONT_STEP_LABEL,
                text_color=COL_MUTED,
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True)
            self.step_labels.append(name_label)

        # ----- Bottom Info Section -----
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 15))

        # Version label
        version_label = ctk.CTkLabel(
            bottom_frame,
            text=APP_VERSION,
            font=FONT_SMALL,
            text_color=COL_MUTED
        )
        version_label.pack(anchor="w", pady=(0, 8))

        # Project count label
        self.project_count_label = ctk.CTkLabel(
            bottom_frame,
            text="Projects: 0",
            font=FONT_SMALL,
            text_color=COL_MUTED
        )
        self.project_count_label.pack(anchor="w", pady=(0, 4))

        # Output root path label
        pyx_data_path = _get_base_dir() / "PyX_Data"
        self.output_label = ctk.CTkLabel(
            bottom_frame,
            text=f"Output:\n{pyx_data_path}",
            font=FONT_SMALL,
            text_color=COL_MUTED,
            wraplength=190,
            justify="left"
        )
        self.output_label.pack(anchor="w")

        # ----- Library Categories Status Indicator -----
        self.globe_label = ctk.CTkLabel(
            bottom_frame,
            text="🌐 Checking lib categories...",
            font=FONT_SMALL,
            text_color=COL_MUTED,
            wraplength=190,
            justify="left"
        )
        self.globe_label.pack(anchor="w", pady=(6, 0))

    def update_lib_status(self, loaded: bool) -> None:
        """Update the library-categories globe indicator."""
        if loaded:
            self.globe_label.configure(
                text="🌐 Lib categories downloaded",
                text_color=COL_SUCCESS
            )
        else:
            self.globe_label.configure(
                text="🌐✗ No internet, can't categorise",
                text_color=COL_ERROR
            )

    def update_step(self, current_step: int) -> None:
        """
        Update the step indicators in the sidebar to reflect the current step.

        Steps before the current one show a filled circle (completed).
        The current step shows a target circle (active).
        Steps after the current one show an empty circle (pending).

        Parameters
        ----------
        current_step : int
            The zero-based index of the currently active step.
        """
        for step_index in range(len(STEP_LABELS)):
            if step_index < current_step:
                # Completed step
                self.step_dots[step_index].configure(text="●", text_color=COL_SUCCESS)
                self.step_labels[step_index].configure(text_color=COL_SUCCESS)
            elif step_index == current_step:
                # Current active step
                self.step_dots[step_index].configure(text="◉", text_color=COL_ACCENT_LIGHT)
                self.step_labels[step_index].configure(text_color=COL_TEXT)
            else:
                # Future step
                self.step_dots[step_index].configure(text="○", text_color=COL_MUTED)
                self.step_labels[step_index].configure(text_color=COL_MUTED)

    def refresh_project_count(self) -> None:
        """
        Refresh the displayed project count by recounting the directories
        inside PyX_Data/.
        """
        count = count_existing_projects()
        self.project_count_label.configure(text=f"Projects: {count}")


# =============================================================================
# CLASS – StepWelcome (Step 0)
# =============================================================================
class StepWelcome(ctk.CTkFrame):
    """
    Step 0: Welcome screen.
    Displays a welcome message, an antivirus warning, and a features list.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Welcome step.

        Parameters
        ----------
        master : Any
            The parent widget (the main content area).
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Welcome to PyX",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 5), anchor="w", padx=20)

        # ----- Subtitle -----
        subtitle_label = ctk.CTkLabel(
            self,
            text="Package Python scripts into standalone Windows executables.",
            font=FONT_BODY,
            text_color=COL_MUTED
        )
        subtitle_label.pack(pady=(0, 15), anchor="w", padx=20)

        # ----- Antivirus Warning Card -----
        av_card = ctk.CTkFrame(self, fg_color=COL_CARD, corner_radius=8)
        av_card.pack(fill="x", padx=20, pady=(0, 10))

        av_title = ctk.CTkLabel(
            av_card,
            text="⚠  Antivirus Exclusions",
            font=FONT_HEADER,
            text_color=COL_WARNING
        )
        av_title.pack(pady=(12, 5), padx=15, anchor="w")

        av_text = ctk.CTkLabel(
            av_card,
            text=(
                "Python executables are often flagged as false positives by "
                "antivirus software. To prevent build failures or the output "
                "executable being quarantined, please add the following to "
                "your antivirus exclusions:\n\n"
                "  1. The folder containing your Python script.\n"
                "  2. The target Python script file itself.\n"
                "  3. The PyX_Data/ output directory."
            ),
            font=FONT_BODY,
            text_color=COL_TEXT,
            wraplength=520,
            justify="left"
        )
        av_text.pack(pady=(0, 12), padx=15, anchor="w")

        # ----- Features Card -----
        feat_card = ctk.CTkFrame(self, fg_color=COL_CARD, corner_radius=8)
        feat_card.pack(fill="x", padx=20, pady=(0, 15))

        feat_title = ctk.CTkLabel(
            feat_card,
            text="Features",
            font=FONT_HEADER,
            text_color=COL_ACCENT_LIGHT
        )
        feat_title.pack(pady=(12, 5), padx=15, anchor="w")

        features_list = [
            "Isolated virtual environment per project.",
            "Automatic detection and installation of script dependencies.",
            "Sanitisation of hidden-import arguments (fixes 'numpy as np' style errors).",
            "Bundling of data folders into the EXE.",
            'Access bundled files with "packaged-within-exe:folder/file.ext".',
            "Optional code signing with a PFX certificate (Not for distribution).",
            "Build logs saved to PyX_Data/<project>/logs/.",
            f"Default EXE author: {DEFAULT_AUTHOR}.",
        ]
        for feature_text in features_list:
            feat_item = ctk.CTkLabel(
                feat_card,
                text=f"  ●  {feature_text}",
                font=FONT_BODY,
                text_color=COL_TEXT,
                wraplength=500,
                justify="left",
                anchor="w"
            )
            feat_item.pack(pady=2, padx=15, anchor="w")

        # Add a small spacer after the last feature
        ctk.CTkLabel(feat_card, text="", height=8, fg_color="transparent").pack()

        # ----- Get Started Button -----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 20))

        get_started_button = ctk.CTkButton(
            btn_frame,
            text="Get Started  →",
            font=FONT_HEADER,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            height=40,
            command=lambda: self.wizard.go_to_step(1)
        )
        get_started_button.pack(side="right")


# =============================================================================
# CLASS – StepScript (Step 1)
# =============================================================================
class StepScript(ctk.CTkFrame):
    """
    Step 1: Script Selection.
    Allows the user to browse for a .py file and shows detected third-party
    imports.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Script Selection step.

        Parameters
        ----------
        master : Any
            The parent widget.
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard
        self.selected_script: Optional[Path] = None
        self.detected_imports: List[str] = []

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Select Python Script",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 10), anchor="w", padx=20)

        # ----- Script Path Row -----
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=20, pady=(0, 5))

        self.script_entry = ctk.CTkEntry(
            path_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_TEXT,
            state="readonly",
            height=36
        )
        self.script_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_button = ctk.CTkButton(
            path_row,
            text="Browse",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=36,
            command=self._browse_script
        )
        browse_button.pack(side="left", padx=(0, 8))

        # Validation indicator
        self.validation_label = ctk.CTkLabel(
            path_row,
            text="✕",
            font=("Consolas", 16, "bold"),
            text_color=COL_ERROR,
            width=24
        )
        self.validation_label.pack(side="left")

        # ----- Info Text -----
        info_label = ctk.CTkLabel(
            self,
            text="Dependencies will be automatically detected and installed into the project virtual environment.",
            font=FONT_SMALL,
            text_color=COL_MUTED,
            wraplength=540,
            justify="left"
        )
        info_label.pack(pady=(5, 10), anchor="w", padx=20)

        # ----- Detected Imports Card -----
        self.imports_card = ctk.CTkFrame(self, fg_color=COL_CARD, corner_radius=8)
        self.imports_card.pack(fill="x", padx=20, pady=(0, 10))

        imports_title = ctk.CTkLabel(
            self.imports_card,
            text="Detected Third-Party Imports",
            font=FONT_HEADER,
            text_color=COL_ACCENT_LIGHT
        )
        imports_title.pack(pady=(12, 5), padx=15, anchor="w")

        self.imports_list_label = ctk.CTkLabel(
            self.imports_card,
            text="No script selected.",
            font=FONT_BODY,
            text_color=COL_MUTED,
            wraplength=500,
            justify="left"
        )
        self.imports_list_label.pack(pady=(0, 12), padx=15, anchor="w")

        # ----- Navigation Buttons -----
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(10, 20))

        back_button = ctk.CTkButton(
            nav_frame,
            text="← Back",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=80,
            height=36,
            command=lambda: self.wizard.go_to_step(0)
        )
        back_button.pack(side="left")

        self.next_button = ctk.CTkButton(
            nav_frame,
            text="Next  →",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=36,
            command=self._go_next
        )
        self.next_button.pack(side="right")

    def _browse_script(self) -> None:
        """Open a file dialog to select a Python script."""
        file_path = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if not file_path:
            return

        self.selected_script = Path(file_path)

        # Update the entry field
        self.script_entry.configure(state="normal")
        self.script_entry.delete(0, "end")
        self.script_entry.insert(0, str(self.selected_script))
        self.script_entry.configure(state="readonly")

        # Detect imports
        self.detected_imports = detect_script_imports(self.selected_script)

        # Update validation indicator
        if self.selected_script.exists():
            self.validation_label.configure(text="✓", text_color=COL_SUCCESS)
        else:
            self.validation_label.configure(text="✕", text_color=COL_ERROR)

        # Update imports display (annotate with category if categories are loaded)
        if self.detected_imports:
            if _lib_categories_loaded:
                parts = []
                for lib in self.detected_imports:
                    cat = _get_category(lib)
                    parts.append(f"{lib} [{cat}]" if cat else lib)
                display_text = ", ".join(parts)
            else:
                display_text = ", ".join(self.detected_imports)
            self.imports_list_label.configure(
                text=display_text,
                text_color=COL_TEXT
            )
        else:
            self.imports_list_label.configure(
                text="No third-party imports detected (only standard library modules found).",
                text_color=COL_MUTED
            )

        # Store in wizard data
        self.wizard.data["script_path"] = self.selected_script
        self.wizard.data["detected_imports"] = self.detected_imports

    def _go_next(self) -> None:
        """Validate and proceed to the next step."""
        if self.selected_script is None or not self.selected_script.exists():
            messagebox.showwarning(
                "Validation Error",
                "Please select a valid Python script before proceeding."
            )
            return
        self.wizard.go_to_step(2)


# =============================================================================
# CLASS – StepConfig (Step 2)
# =============================================================================
class StepConfig(ctk.CTkFrame):
    """
    Step 2: Project Configuration.
    Collects the project name, shows the author, allows toggling console mode,
    and optionally selecting a custom icon.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Project Configuration step.

        Parameters
        ----------
        master : Any
            The parent widget.
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard
        self.icon_path: Optional[str] = None

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Project Configuration",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 15), anchor="w", padx=20)

        # ----- Project Name -----
        name_row = ctk.CTkFrame(self, fg_color="transparent")
        name_row.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(
            name_row, text="Project Name:", font=FONT_BODY,
            text_color=COL_TEXT, width=120, anchor="w"
        ).pack(side="left")

        self.name_entry = ctk.CTkEntry(
            name_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_TEXT,
            height=34,
            placeholder_text="Enter project name"
        )
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.name_entry.bind("<KeyRelease>", self._on_name_change)

        self.name_validation_label = ctk.CTkLabel(
            name_row,
            text="✕",
            font=("Consolas", 16, "bold"),
            text_color=COL_ERROR,
            width=24
        )
        self.name_validation_label.pack(side="left")

        # Output path preview
        self.output_path_label = ctk.CTkLabel(
            self,
            text="Output: PyX_Data/",
            font=FONT_SMALL,
            text_color=COL_MUTED
        )
        self.output_path_label.pack(anchor="w", padx=20, pady=(0, 5))

        # Existing project warning
        self.existing_warning_label = ctk.CTkLabel(
            self,
            text="",
            font=FONT_SMALL,
            text_color=COL_WARNING
        )
        self.existing_warning_label.pack(anchor="w", padx=20, pady=(0, 10))

        # ----- Author (read-only) -----
        author_row = ctk.CTkFrame(self, fg_color="transparent")
        author_row.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            author_row, text="Author:", font=FONT_BODY,
            text_color=COL_TEXT, width=120, anchor="w"
        ).pack(side="left")

        author_entry = ctk.CTkEntry(
            author_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_MUTED,
            height=34,
            state="normal"
        )
        author_entry.insert(0, DEFAULT_AUTHOR)
        author_entry.configure(state="readonly")
        author_entry.pack(side="left", fill="x", expand=True)

        # ----- Console Mode Checkbox -----
        self.console_var = ctk.BooleanVar(value=True)
        console_check = ctk.CTkCheckBox(
            self,
            text="Show console window (uncheck for GUI-only applications)",
            font=FONT_BODY,
            text_color=COL_TEXT,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            variable=self.console_var
        )
        console_check.pack(anchor="w", padx=20, pady=(0, 15))

        # ----- Custom Icon -----
        icon_row = ctk.CTkFrame(self, fg_color="transparent")
        icon_row.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(
            icon_row, text="Custom Icon:", font=FONT_BODY,
            text_color=COL_TEXT, width=120, anchor="w"
        ).pack(side="left")

        self.icon_entry = ctk.CTkEntry(
            icon_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_TEXT,
            height=34,
            state="readonly",
            placeholder_text="(optional – uses default if empty)"
        )
        self.icon_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        icon_browse_button = ctk.CTkButton(
            icon_row,
            text="Browse",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=34,
            command=self._browse_icon
        )
        icon_browse_button.pack(side="left")

        icon_info_label = ctk.CTkLabel(
            self,
            text="If no icon is provided, a default icon will be downloaded from GitHub.",
            font=FONT_SMALL,
            text_color=COL_MUTED,
            wraplength=540,
            justify="left"
        )
        icon_info_label.pack(anchor="w", padx=20, pady=(2, 10))

        # ----- Navigation Buttons -----
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(10, 20))

        back_button = ctk.CTkButton(
            nav_frame,
            text="← Back",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=80,
            height=36,
            command=lambda: self.wizard.go_to_step(1)
        )
        back_button.pack(side="left")

        self.next_button = ctk.CTkButton(
            nav_frame,
            text="Next  →",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=36,
            command=self._go_next
        )
        self.next_button.pack(side="right")

    def _on_name_change(self, event: Any = None) -> None:
        """Handle project name changes and update the output path preview."""
        raw_name = self.name_entry.get().strip()
        # Sanitise: replace any characters that are not alphanumeric, underscore,
        # hyphen, or dot with underscores.
        sanitised_name = re.sub(r'[^\w\-.]', '_', raw_name)

        if sanitised_name:
            self.name_validation_label.configure(text="✓", text_color=COL_SUCCESS)
            output_full = _get_base_dir() / "PyX_Data" / sanitised_name
            self.output_path_label.configure(text=f"Output: {output_full}")

            # Check if project already exists
            if output_full.exists():
                self.existing_warning_label.configure(
                    text="⚠ This project already exists. The existing virtual environment will be reused."
                )
            else:
                self.existing_warning_label.configure(text="")
        else:
            self.name_validation_label.configure(text="✕", text_color=COL_ERROR)
            self.output_path_label.configure(text="Output: PyX_Data/")
            self.existing_warning_label.configure(text="")

    def _browse_icon(self) -> None:
        """Open a file dialog to select a custom .ico file."""
        file_path = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("Icon files", "*.ico"), ("All files", "*.*")]
        )
        if not file_path:
            return
        self.icon_path = file_path
        self.icon_entry.configure(state="normal")
        self.icon_entry.delete(0, "end")
        self.icon_entry.insert(0, file_path)
        self.icon_entry.configure(state="readonly")

    def _go_next(self) -> None:
        """Validate the configuration and proceed to the next step."""
        raw_name = self.name_entry.get().strip()
        sanitised_name = re.sub(r'[^\w\-.]', '_', raw_name)

        if not sanitised_name:
            messagebox.showwarning(
                "Validation Error",
                "Please enter a project name before proceeding."
            )
            return

        # Store configuration in wizard data
        self.wizard.data["project_name"] = sanitised_name
        self.wizard.data["console_mode"] = self.console_var.get()
        self.wizard.data["icon_path"] = self.icon_path

        self.wizard.go_to_step(3)


# =============================================================================
# CLASS – StepData (Step 3)
# =============================================================================
class StepData(ctk.CTkFrame):
    """
    Step 3: Data Folders (Optional).
    Allows the user to add folders that will be bundled into the EXE via
    PyInstaller's --add-data flag.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Data Folders step.

        Parameters
        ----------
        master : Any
            The parent widget.
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard
        self.data_folders: List[Path] = []

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Data Folders (Optional)",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 5), anchor="w", padx=20)

        info_label = ctk.CTkLabel(
            self,
            text=(
                "Add folders to bundle into the executable. Files in these folders "
                "can be accessed at runtime using the packaged-within-exe: prefix."
            ),
            font=FONT_BODY,
            text_color=COL_MUTED,
            wraplength=540,
            justify="left"
        )
        info_label.pack(anchor="w", padx=20, pady=(0, 10))

        # ----- Buttons Row -----
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 10))

        add_button = ctk.CTkButton(
            btn_row,
            text="+ Add Folder",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=120,
            height=34,
            command=self._add_folder
        )
        add_button.pack(side="left", padx=(0, 8))

        remove_button = ctk.CTkButton(
            btn_row,
            text="✕ Remove Last",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=120,
            height=34,
            command=self._remove_last
        )
        remove_button.pack(side="left")

        # ----- Folders List Card -----
        self.folders_card = ctk.CTkFrame(self, fg_color=COL_CARD, corner_radius=8)
        self.folders_card.pack(fill="x", padx=20, pady=(0, 5))

        self.folders_list_label = ctk.CTkLabel(
            self.folders_card,
            text="No data folders added.",
            font=FONT_BODY,
            text_color=COL_MUTED,
            wraplength=500,
            justify="left"
        )
        self.folders_list_label.pack(pady=12, padx=15, anchor="w")

        # Total size label
        self.total_size_label = ctk.CTkLabel(
            self,
            text="",
            font=FONT_SMALL,
            text_color=COL_MUTED
        )
        self.total_size_label.pack(anchor="w", padx=20, pady=(0, 10))

        # ----- Navigation Buttons -----
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(10, 20))

        back_button = ctk.CTkButton(
            nav_frame,
            text="← Back",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=80,
            height=36,
            command=lambda: self.wizard.go_to_step(2)
        )
        back_button.pack(side="left")

        next_button = ctk.CTkButton(
            nav_frame,
            text="Next  →",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=36,
            command=self._go_next
        )
        next_button.pack(side="right")

    def _add_folder(self) -> None:
        """Open a directory picker and add the selected folder to the list."""
        folder_path = filedialog.askdirectory(title="Select Data Folder")
        if not folder_path:
            return
        folder = Path(folder_path)
        self.data_folders.append(folder)
        self._refresh_list()

    def _remove_last(self) -> None:
        """Remove the last added folder from the list."""
        if self.data_folders:
            self.data_folders.pop()
            self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the displayed list of data folders with sizes and warnings."""
        if not self.data_folders:
            self.folders_list_label.configure(
                text="No data folders added.",
                text_color=COL_MUTED
            )
            self.total_size_label.configure(text="")
            return

        lines: List[str] = []
        total_bytes = 0
        for folder in self.data_folders:
            size_bytes = folder_size(folder)
            total_bytes += size_bytes
            size_mb = size_bytes / (1024 * 1024)
            dest_name = folder.name
            warning_marker = ""
            if size_mb > 50:
                warning_marker = " ⚠ (>50 MB)"
            lines.append(
                f"  {folder}  →  {dest_name}  "
                f"({size_mb:.1f} MB){warning_marker}"
            )

        self.folders_list_label.configure(
            text="\n".join(lines),
            text_color=COL_TEXT
        )

        total_mb = total_bytes / (1024 * 1024)
        self.total_size_label.configure(
            text=f"Total size: {total_mb:.1f} MB"
        )

    def _go_next(self) -> None:
        """Store the data folders and proceed to the next step."""
        self.wizard.data["data_folders"] = list(self.data_folders)
        self.wizard.go_to_step(4)


# =============================================================================
# CLASS – StepCertificate (Step 4)
# =============================================================================
class StepCertificate(ctk.CTkFrame):
    """
    Step 4: Code Signing (Optional).
    Allows the user to select a PFX/P12 certificate and enter a password for
    code signing.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Certificate step.

        Parameters
        ----------
        master : Any
            The parent widget.
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard
        self.pfx_path: Optional[Path] = None
        self.cert_valid: Optional[bool] = None

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Code Signing (Optional)",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 10), anchor="w", padx=20)

        # ----- Certificate File Row -----
        cert_row = ctk.CTkFrame(self, fg_color="transparent")
        cert_row.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(
            cert_row, text="Certificate:", font=FONT_BODY,
            text_color=COL_TEXT, width=100, anchor="w"
        ).pack(side="left")

        self.cert_entry = ctk.CTkEntry(
            cert_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_TEXT,
            height=34,
            state="readonly",
            placeholder_text="(optional) Select PFX or P12 file"
        )
        self.cert_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        cert_browse_button = ctk.CTkButton(
            cert_row,
            text="Browse",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=34,
            command=self._browse_cert
        )
        cert_browse_button.pack(side="left")

        # ----- Password Row -----
        pwd_row = ctk.CTkFrame(self, fg_color="transparent")
        pwd_row.pack(fill="x", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            pwd_row, text="Password:", font=FONT_BODY,
            text_color=COL_TEXT, width=100, anchor="w"
        ).pack(side="left")

        self.pwd_entry = ctk.CTkEntry(
            pwd_row,
            font=FONT_BODY,
            fg_color=COL_CARD,
            border_color=COL_BORDER,
            text_color=COL_TEXT,
            height=34,
            show="●",
            placeholder_text="Certificate password"
        )
        self.pwd_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        validate_button = ctk.CTkButton(
            pwd_row,
            text="Validate",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=34,
            command=self._validate_cert
        )
        validate_button.pack(side="left", padx=(0, 8))

        self.cert_validation_label = ctk.CTkLabel(
            pwd_row,
            text="",
            font=("Consolas", 16, "bold"),
            text_color=COL_MUTED,
            width=24
        )
        self.cert_validation_label.pack(side="left")

        # ----- Crypto Availability Warning -----
        if not CRYPTOGRAPHY_AVAILABLE:
            crypto_warning = ctk.CTkLabel(
                self,
                text=(
                    "⚠ The 'cryptography' package is not installed. "
                    "Certificate validation is disabled, but signing will still "
                    "be attempted if a certificate is provided."
                ),
                font=FONT_SMALL,
                text_color=COL_WARNING,
                wraplength=540,
                justify="left"
            )
            crypto_warning.pack(anchor="w", padx=20, pady=(5, 5))

        # ----- Info Note -----
        note_label = ctk.CTkLabel(
            self,
            text=(
                "Note: Self-signed certificates are for testing only. Signing "
                "requires signtool.exe in the signtool/ subfolder (relative to "
                "this script or executable). If you are using the .exe from "
                "GitHub, it should have it packaged properly already."
            ),
            font=FONT_SMALL,
            text_color=COL_MUTED,
            wraplength=540,
            justify="left"
        )
        note_label.pack(anchor="w", padx=20, pady=(5, 15))

        # ----- Navigation Buttons -----
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(10, 20))

        back_button = ctk.CTkButton(
            nav_frame,
            text="← Back",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=80,
            height=36,
            command=lambda: self.wizard.go_to_step(3)
        )
        back_button.pack(side="left")

        next_button = ctk.CTkButton(
            nav_frame,
            text="Next  →",
            font=FONT_BODY,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=80,
            height=36,
            command=self._go_next
        )
        next_button.pack(side="right")

    def _browse_cert(self) -> None:
        """Open a file dialog to select a PFX or P12 certificate file."""
        file_path = filedialog.askopenfilename(
            title="Select Certificate File",
            filetypes=[
                ("Certificate files", "*.pfx *.p12"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return
        self.pfx_path = Path(file_path)
        self.cert_entry.configure(state="normal")
        self.cert_entry.delete(0, "end")
        self.cert_entry.insert(0, file_path)
        self.cert_entry.configure(state="readonly")
        self.cert_valid = None
        self.cert_validation_label.configure(text="", text_color=COL_MUTED)

    def _validate_cert(self) -> None:
        """Attempt to validate the selected certificate with the entered password."""
        if self.pfx_path is None:
            messagebox.showinfo("Info", "Please select a certificate file first.")
            return
        if not CRYPTOGRAPHY_AVAILABLE:
            messagebox.showinfo(
                "Info",
                "The 'cryptography' package is not installed. "
                "Validation is not available, but signing can still be attempted."
            )
            return

        password = self.pwd_entry.get()
        is_valid = validate_pfx(self.pfx_path, password)
        self.cert_valid = is_valid

        if is_valid:
            self.cert_validation_label.configure(text="✓", text_color=COL_SUCCESS)
        else:
            self.cert_validation_label.configure(text="✕", text_color=COL_ERROR)

    def _go_next(self) -> None:
        """Validate and proceed to the build step."""
        # If a certificate was selected but validation failed, ask the user
        if self.pfx_path is not None:
            password = self.pwd_entry.get()

            # If cryptography is available and validation was performed but failed
            if CRYPTOGRAPHY_AVAILABLE and self.cert_valid is False:
                proceed = messagebox.askyesno(
                    "Certificate Validation Failed",
                    "The certificate password is invalid or could not be verified. "
                    "Continue without signing?"
                )
                if proceed:
                    # Clear signing data – proceed without signing
                    self.wizard.data["pfx_path"] = None
                    self.wizard.data["pfx_password"] = None
                else:
                    return
            elif CRYPTOGRAPHY_AVAILABLE and self.cert_valid is None:
                # Certificate selected but not validated yet
                is_valid = validate_pfx(self.pfx_path, password)
                if not is_valid:
                    proceed = messagebox.askyesno(
                        "Certificate Validation Failed",
                        "The certificate password is invalid or could not be verified. "
                        "Continue without signing?"
                    )
                    if proceed:
                        self.wizard.data["pfx_path"] = None
                        self.wizard.data["pfx_password"] = None
                    else:
                        return
                else:
                    self.wizard.data["pfx_path"] = self.pfx_path
                    self.wizard.data["pfx_password"] = password
            else:
                # Either cryptography is not available, or validation passed
                self.wizard.data["pfx_path"] = self.pfx_path
                self.wizard.data["pfx_password"] = password
        else:
            self.wizard.data["pfx_path"] = None
            self.wizard.data["pfx_password"] = None

        self.wizard.go_to_step(5)


# =============================================================================
# CLASS – StepBuild (Step 5)
# =============================================================================
class StepBuild(ctk.CTkFrame):
    """
    Step 5: Build.
    Displays the build log, progress bar, and buttons to start/rebuild and
    open output folders.
    """

    def __init__(self, master: Any, wizard: "Wizard", **kwargs: Any) -> None:
        """
        Initialise the Build step.

        Parameters
        ----------
        master : Any
            The parent widget.
        wizard : Wizard
            Reference to the main Wizard application instance.
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.wizard = wizard
        self.build_running = False
        self.build_completed = False
        self.log_lines: List[str] = []

        # ----- Title -----
        title_label = ctk.CTkLabel(
            self,
            text="Build",
            font=FONT_TITLE,
            text_color=COL_TEXT
        )
        title_label.pack(pady=(20, 10), anchor="w", padx=20)

        # ----- Status Label -----
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready to build.",
            font=FONT_BODY,
            text_color=COL_MUTED
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 5))

        # ----- Progress Bar -----
        self.progress_bar = ctk.CTkProgressBar(
            self,
            fg_color=COL_CARD,
            progress_color=COL_ACCENT,
            height=8
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.set(0)

        # ----- Log Text Area -----
        self.log_text = ctk.CTkTextbox(
            self,
            font=FONT_MONO,
            fg_color=COL_LOG_BG,
            text_color=COL_TEXT,
            border_color=COL_BORDER,
            border_width=1,
            corner_radius=6,
            wrap="word",
            height=280
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.log_text.configure(state="disabled")

        # ----- Button Row -----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 5))

        back_button = ctk.CTkButton(
            btn_frame,
            text="← Back",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=80,
            height=36,
            command=lambda: self.wizard.go_to_step(4)
        )
        back_button.pack(side="left")

        self.build_button = ctk.CTkButton(
            btn_frame,
            text="▶  BUILD",
            font=FONT_HEADER,
            fg_color=COL_ACCENT,
            hover_color=COL_ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            width=140,
            height=40,
            command=self._start_build
        )
        self.build_button.pack(side="right")

        # ----- Post-Build Buttons (initially hidden) -----
        self.post_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.post_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.open_output_button = ctk.CTkButton(
            self.post_frame,
            text="Open Output Folder",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=160,
            height=34,
            state="disabled",
            command=self._open_output
        )
        self.open_output_button.pack(side="left", padx=(0, 8))

        self.open_log_button = ctk.CTkButton(
            self.post_frame,
            text="Open Log Folder",
            font=FONT_BODY,
            fg_color=COL_CARD,
            hover_color=COL_BORDER,
            text_color=COL_TEXT,
            corner_radius=6,
            width=160,
            height=34,
            state="disabled",
            command=self._open_logs
        )
        self.open_log_button.pack(side="left")

    def _log(self, message: str) -> None:
        """
        Append a message to the log text area and the log lines list.
        This method is safe to call from any thread because it uses after()
        to schedule the GUI update on the main thread.

        Parameters
        ----------
        message : str
            The log message to append.
        """
        self.log_lines.append(message)

        def _update_gui():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.after(0, _update_gui)

    def _set_status(self, text: str, colour: str = COL_MUTED) -> None:
        """
        Update the status label text and colour.
        Thread-safe via after().

        Parameters
        ----------
        text : str
            The status text.
        colour : str
            The hex colour for the status text.
        """
        self.after(0, lambda: self.status_label.configure(text=text, text_color=colour))

    def _set_progress(self, value: float) -> None:
        """
        Update the progress bar value (0.0 to 1.0).
        Thread-safe via after().

        Parameters
        ----------
        value : float
            Progress value between 0.0 and 1.0.
        """
        self.after(0, lambda: self.progress_bar.set(value))

    def _start_build(self) -> None:
        """Start the build process in a background thread."""
        if self.build_running:
            return

        # Clear previous log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_lines = []

        self.build_running = True
        self.build_button.configure(state="disabled", text="Building...")
        self.open_output_button.configure(state="disabled")
        self.open_log_button.configure(state="disabled")
        self.progress_bar.set(0)

        # Run the build in a background thread
        build_thread = threading.Thread(target=self._build_worker, daemon=True)
        build_thread.start()

    def _build_worker(self) -> None:
        """
        The main build process that runs in a background thread.
        This follows the exact sequence specified in the build process:
        1. Create project folder and subfolders.
        2. Create or reuse virtual environment.
        3. Upgrade pip.
        4. Ensure PyInstaller is installed.
        5. Detect and install dependencies.
        6. Preprocess the target script.
        7. Run PyInstaller.
        8. Locate the generated executable.
        9. Optionally sign the executable.
        10. Write manifest.
        11. Write build log.
        """
        data = self.wizard.data
        script_path: Path = data["script_path"]
        project_name: str = data["project_name"]
        console_mode: bool = data["console_mode"]
        icon_path: Optional[str] = data.get("icon_path")
        data_folders: List[Path] = data.get("data_folders", [])
        pfx_path: Optional[Path] = data.get("pfx_path")
        pfx_password: Optional[str] = data.get("pfx_password")
        detected_imports: List[str] = data.get("detected_imports", [])

        base_dir = _get_base_dir()
        pyx_data_dir = base_dir / "PyX_Data"
        project_dir = pyx_data_dir / project_name
        temp_dir: Optional[Path] = None
        signed = False

        try:
            # =================================================================
            # STEP 1: Create project folder and subfolders
            # =================================================================
            self._set_status("Creating project structure...", COL_TEXT)
            self._set_progress(0.05)
            self._log(f"=== PyX Wizard {APP_VERSION} Build Started ===")
            self._log(f"Project: {project_name}")
            self._log(f"Script: {script_path}")
            self._log(f"Timestamp: {datetime.datetime.now().isoformat()}")
            self._log("")

            for subfolder_name in ["venv", "build", "dist", "logs"]:
                subfolder = project_dir / subfolder_name
                subfolder.mkdir(parents=True, exist_ok=True)
                self._log(f"Ensured directory exists: {subfolder}")

            self._set_progress(0.10)

            # =================================================================
            # STEP 2: Create or reuse virtual environment
            # =================================================================
            self._set_status("Setting up virtual environment...", COL_TEXT)
            self._log("")
            self._log("--- Virtual Environment ---")
            python_exe = create_project_venv(project_dir, self._log)
            self._set_progress(0.20)

            # =================================================================
            # STEP 3: Upgrade pip
            # =================================================================
            self._set_status("Upgrading pip...", COL_TEXT)
            self._log("")
            self._log("--- Upgrading pip ---")
            try:
                run_cmd(
                    [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
                    self._log
                )
            except subprocess.CalledProcessError as pip_error:
                self._log(f"WARNING: pip upgrade failed: {pip_error}")
            self._set_progress(0.25)

            # =================================================================
            # STEP 4: Ensure PyInstaller is installed
            # =================================================================
            self._set_status("Checking PyInstaller...", COL_TEXT)
            self._log("")
            self._log("--- PyInstaller ---")
            if not venv_has_package(python_exe, "PyInstaller"):
                self._log("PyInstaller not found in venv. Installing...")
                venv_pip_install(python_exe, "pyinstaller", log=self._log)
            else:
                self._log("PyInstaller is already installed.")
            self._set_progress(0.35)

            # =================================================================
            # STEP 5: Detect and install dependencies
            # =================================================================
            self._set_status("Installing dependencies...", COL_TEXT)
            self._log("")
            self._log("--- Dependencies ---")
            install_script_deps(python_exe, script_path, self._log)
            self._set_progress(0.45)

            # =================================================================
            # STEP 6: Preprocess the target script
            # =================================================================
            self._set_status("Preprocessing script...", COL_TEXT)
            self._log("")
            self._log("--- Script Preprocessing ---")
            temp_dir = Path(tempfile.mkdtemp(prefix="pyx_build_"))
            preprocessed_script = preprocess_script(script_path, temp_dir)
            self._log(f"Preprocessed script saved to: {preprocessed_script}")
            self._set_progress(0.50)

            # =================================================================
            # STEP 7: Resolve icon
            # =================================================================
            effective_icon: Optional[str] = icon_path
            if effective_icon is None or not Path(effective_icon).exists():
                self._log("")
                self._log("--- Icon ---")
                self._log("No custom icon provided. Attempting to download default icon...")
                effective_icon = _download_icon()
                if effective_icon:
                    self._log(f"Default icon available at: {effective_icon}")
                else:
                    self._log("WARNING: Could not download default icon. Building without icon.")

            # =================================================================
            # STEP 8: Run PyInstaller
            # =================================================================
            self._set_status("Running PyInstaller...", COL_ACCENT_LIGHT)
            self._log("")
            self._log("--- PyInstaller Build ---")

            # Construct the PyInstaller command
            pyinstaller_cmd: List[str] = [
                str(python_exe), "-m", "PyInstaller"
            ]
            # Add standard flags
            pyinstaller_cmd.extend(PYINSTALLER_FLAGS)

            # Add project name
            pyinstaller_cmd.extend(["--name", project_name])

            # Add output paths
            pyinstaller_cmd.extend(["--distpath", str(project_dir / "dist")])
            pyinstaller_cmd.extend(["--workpath", str(project_dir / "build")])

            # Console mode
            if not console_mode:
                pyinstaller_cmd.append("--noconsole")

            # Icon
            if effective_icon and Path(effective_icon).exists():
                pyinstaller_cmd.extend(["--icon", effective_icon])

            # Hidden imports (sanitised)
            for import_name in detected_imports:
                # Ensure import names are sanitised (top-level only, valid identifier)
                top_level = import_name.split(".")[0]
                if top_level.isidentifier() and top_level.lower() != "pyinstaller":
                    pyinstaller_cmd.extend(["--hidden-import", top_level])

            # Collect-all for packages that use dynamic imports (e.g. PyOpenGL).
            # The hardcoded base set is merged with the remotely fetched list
            # (already cached in _lib_collect_all — no second HTTP request).
            _COLLECT_ALL_PACKAGES: Set[str] = {
                # Graphics / OpenGL
                "OpenGL", "glfw", "moderngl", "vispy", "pyglet",
                # GUI toolkits
                "pygame", "wx", "PyQt5", "PyQt6", "PySide2", "PySide6", "kivy",
                # Image processing
                "PIL", "cv2", "imageio", "skimage",
                # Scientific / ML (heavy use of C extensions and lazy loaders)
                "sklearn", "scipy", "matplotlib", "numba", "shapely",
                # Crypto / native bindings
                "cryptography", "cffi", "nacl",
                # Packaging / runtime metadata (often missed)
                "pkg_resources", "importlib_resources", "importlib_metadata",
            }
            if _lib_collect_all:
                _COLLECT_ALL_PACKAGES |= _lib_collect_all

            collected_tops = {imp.split(".")[0] for imp in detected_imports}

            for pkg in _COLLECT_ALL_PACKAGES:
                if pkg in collected_tops:
                    pyinstaller_cmd.extend(["--collect-all", pkg])
                    self._log(f"collect-all: {pkg}")

            # Per-package hidden imports from the remote JSON.
            # These handle packages (like sklearn) that use C extensions or
            # lazy loaders that PyInstaller cannot discover automatically.
            for pkg, hidden_list in _lib_hidden_imports.items():
                if pkg in collected_tops:
                    for hi in hidden_list:
                        pyinstaller_cmd.extend(["--hidden-import", hi])
                    self._log(f"hidden-imports ({pkg}): {', '.join(hidden_list)}")

            # Per-package --copy-metadata from the remote JSON.
            # Required for packages that read their own pip metadata at runtime
            # (e.g. sklearn → scikit-learn), or whose import name differs from
            # their pip distribution name.
            for imp_name, dist_name in _lib_copy_metadata.items():
                if imp_name in collected_tops:
                    pyinstaller_cmd.extend(["--copy-metadata", dist_name])
                    self._log(f"copy-metadata: {dist_name}")

            # Data folders
            separator = ";" if platform.system() == "Windows" else ":"
            for data_folder in data_folders:
                dest_name = data_folder.name
                add_data_arg = f"{data_folder}{separator}{dest_name}"
                pyinstaller_cmd.extend(["--add-data", add_data_arg])

            # The preprocessed script path (must be last)
            pyinstaller_cmd.append(str(preprocessed_script))

            self._log(f"Command: {' '.join(str(c) for c in pyinstaller_cmd)}")
            self._log("")

            try:
                run_cmd(pyinstaller_cmd, self._log, cwd=str(project_dir))
            except subprocess.CalledProcessError:
                # If running with "PyInstaller" module name fails, try lowercase
                self._log("WARNING: PyInstaller run failed. Trying lowercase module name...")
                pyinstaller_cmd_retry = [
                    str(python_exe), "-m", "pyinstaller"
                ] + pyinstaller_cmd[3:]
                run_cmd(pyinstaller_cmd_retry, self._log, cwd=str(project_dir))

            self._set_progress(0.80)

            # =================================================================
            # STEP 9: Locate the generated executable
            # =================================================================
            self._set_status("Locating output executable...", COL_TEXT)
            self._log("")
            self._log("--- Locating Executable ---")

            dist_dir = project_dir / "dist"
            exe_name = project_name + (".exe" if platform.system() == "Windows" else "")
            exe_path = dist_dir / exe_name

            if not exe_path.exists():
                # Search for any executable in the dist directory
                possible_exes = list(dist_dir.glob("*"))
                if possible_exes:
                    exe_path = possible_exes[0]
                    self._log(f"Found executable: {exe_path}")
                else:
                    raise FileNotFoundError(
                        f"No executable found in {dist_dir}. "
                        f"The PyInstaller build may have failed."
                    )
            else:
                self._log(f"Executable located: {exe_path}")

            self._set_progress(0.85)

            # =================================================================
            # STEP 10: Optionally sign the executable
            # =================================================================
            if pfx_path is not None and pfx_password is not None:
                self._set_status("Signing executable...", COL_TEXT)
                self._log("")
                self._log("--- Code Signing ---")
                try:
                    sign_exe(exe_path, pfx_path, pfx_password, self._log)
                    signed = True
                except Exception as sign_error:
                    self._log(f"WARNING: Code signing failed: {sign_error}")
                    signed = False
            else:
                self._log("")
                self._log("--- Code Signing ---")
                self._log("No certificate provided. Skipping code signing.")

            self._set_progress(0.90)

            # =================================================================
            # STEP 11: Write manifest
            # =================================================================
            self._set_status("Writing manifest...", COL_TEXT)
            self._log("")
            self._log("--- Manifest ---")
            manifest_data = {
                "created": datetime.datetime.now().isoformat(),
                "author": DEFAULT_AUTHOR,
                "project": project_name,
                "script": str(script_path),
                "exe": str(exe_path),
                "signed": signed
            }
            write_manifest(project_dir, manifest_data)
            self._log(f"Manifest written to: {project_dir / 'pyx_manifest.json'}")

            # =================================================================
            # STEP 12: Write build log
            # =================================================================
            self._log("")
            self._log("--- Build Log ---")
            write_build_log(project_dir, self.log_lines)
            self._log(f"Build log saved to: {project_dir / 'logs'}")

            self._set_progress(1.0)
            self._set_status("Build completed successfully!", COL_SUCCESS)
            self._log("")
            self._log(f"=== BUILD SUCCESSFUL ===")
            self._log(f"Executable: {exe_path}")

            # Enable post-build buttons
            self.after(0, self._on_build_success)

        except Exception as build_error:
            self._log("")
            self._log(f"=== BUILD FAILED ===")
            self._log(f"Error: {build_error}")
            self._set_status(f"Build failed: {build_error}", COL_ERROR)
            self._set_progress(0)

            # Write the log even on failure
            try:
                if project_dir.exists():
                    write_build_log(project_dir, self.log_lines)
            except Exception:
                pass

            self.after(
                0,
                lambda err=str(build_error): messagebox.showerror("Build Failed", err)
            )
            self.after(0, self._on_build_failure)

        finally:
            # Always clean up temporary files
            if temp_dir is not None and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    self._log(f"WARNING: Could not clean up temp dir: {cleanup_error}")

            self.build_running = False

    def _on_build_success(self) -> None:
        """Called on the main thread after a successful build."""
        self.build_completed = True
        self.build_button.configure(state="normal", text="▶  REBUILD")
        self.open_output_button.configure(state="normal")
        self.open_log_button.configure(state="normal")
        self.wizard.sidebar.refresh_project_count()

    def _on_build_failure(self) -> None:
        """Called on the main thread after a failed build."""
        self.build_button.configure(state="normal", text="▶  BUILD")
        self.open_log_button.configure(state="normal")

    def _open_output(self) -> None:
        """Open the dist folder in the file explorer."""
        project_name = self.wizard.data.get("project_name", "")
        dist_dir = _get_base_dir() / "PyX_Data" / project_name / "dist"
        if dist_dir.exists():
            _open_folder(dist_dir)
        else:
            messagebox.showinfo("Info", f"Output folder not found: {dist_dir}")

    def _open_logs(self) -> None:
        """Open the logs folder in the file explorer."""
        project_name = self.wizard.data.get("project_name", "")
        logs_dir = _get_base_dir() / "PyX_Data" / project_name / "logs"
        if logs_dir.exists():
            _open_folder(logs_dir)
        else:
            messagebox.showinfo("Info", f"Logs folder not found: {logs_dir}")


# =============================================================================
# CLASS – Wizard (Main Application Window)
# =============================================================================
class Wizard(ctk.CTk):
    """
    The main application window for PyX Wizard
    Manages the sidebar, step frames, and navigation between steps.
    """

    def __init__(self) -> None:
        """Initialise the main Wizard window and all step frames."""
        super().__init__()

        # ----- Window Configuration -----
        self.title(f"PyX Wizard {APP_VERSION} – {DEFAULT_AUTHOR}")
        self.geometry("840x680")
        self.minsize(780, 580)
        self.configure(fg_color=COL_BG)

        # Set the appearance mode and default colour theme for customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # ----- Data Dictionary (shared between steps) -----
        self.data: Dict[str, Any] = {
            "script_path": None,
            "detected_imports": [],
            "project_name": "",
            "console_mode": True,
            "icon_path": None,
            "data_folders": [],
            "pfx_path": None,
            "pfx_password": None,
        }

        # ----- Layout: Sidebar + Main Content -----
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Main content container
        self.content_frame = ctk.CTkFrame(self, fg_color=COL_BG, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # ----- Create Step Frames -----
        self.steps: List[ctk.CTkFrame] = []

        # Step 0: Welcome
        step_welcome = StepWelcome(self.content_frame, wizard=self)
        self.steps.append(step_welcome)

        # Step 1: Script Selection
        step_script = StepScript(self.content_frame, wizard=self)
        self.steps.append(step_script)

        # Step 2: Project Configuration
        step_config = StepConfig(self.content_frame, wizard=self)
        self.steps.append(step_config)

        # Step 3: Data Folders
        step_data = StepData(self.content_frame, wizard=self)
        self.steps.append(step_data)

        # Step 4: Certificate
        step_cert = StepCertificate(self.content_frame, wizard=self)
        self.steps.append(step_cert)

        # Step 5: Build
        step_build = StepBuild(self.content_frame, wizard=self)
        self.steps.append(step_build)

        # ----- Current Step Tracking -----
        self.current_step: int = -1

        # ----- Show the first step -----
        self.go_to_step(0)

        # ----- Refresh project count on startup -----
        self.sidebar.refresh_project_count()

        # ----- Fetch library categories in the background -----
        def _bg_fetch() -> None:
            success = _fetch_lib_categories()
            # Update the globe indicator on the main thread
            self.after(0, lambda: self.sidebar.update_lib_status(success))

        threading.Thread(target=_bg_fetch, daemon=True).start()

    def go_to_step(self, step_index: int) -> None:
        """
        Navigate to the specified step by hiding the current step frame and
        showing the target step frame.

        Parameters
        ----------
        step_index : int
            The zero-based index of the step to navigate to.
        """
        if step_index < 0 or step_index >= len(self.steps):
            return

        # Hide the current step frame if one is displayed
        if self.current_step >= 0:
            self.steps[self.current_step].grid_forget()

        # Show the new step frame
        self.current_step = step_index
        self.steps[step_index].grid(row=0, column=0, sticky="nsew")

        # Update the sidebar step indicators
        self.sidebar.update_step(step_index)

        # Refresh the project count whenever we change steps
        self.sidebar.refresh_project_count()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # freeze_support is required for Windows frozen builds that use
    # multiprocessing. It must be called at the very start of the main
    # entry point.
    multiprocessing.freeze_support()

    # Create and run the main wizard application
    app = Wizard()
    app.mainloop()