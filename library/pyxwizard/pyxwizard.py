#!/usr/bin/env python3
"""
PyX Wizard – Terminal Library Edition
==========================================
A Python library that packages Python scripts into standalone Windows
executables using PyInstaller, with automatic dependency detection,
virtual environment isolation, optional code signing, and data bundling.

Now with:
  • Step-by-step callback hooks for GUI integration
  • Rich build result objects with full metadata
  • Version info embedding (file properties on Windows)
  • Splash screen support (auto-installs Pillow, validates Tk)
  • Cleanup / uninstall helpers
  • Pre/post build hooks
  • Dependency report & environment snapshot
  • On-the-fly progress subscription
  • Extra PyInstaller flags passthrough
  • One-click rebuild from manifest
  • Dry-run mode

Usage (Original – still works identically)
-------------------------------------------
    import pyxwizard

    pyxwizard.begin()
    pyxwizard.location("my_script.py")
    pyxwizard.name("MyProject")
    pyxwizard.build()

Usage (New – step callbacks for a GUI)
--------------------------------------
    import pyxwizard

    pyxwizard.feedback("none")                        # can set before begin()
    pyxwizard.on_progress(my_progress_bar_func)       # persists across begin()
    pyxwizard.on_log(my_log_textbox_func)
    pyxwizard.on_step(my_step_indicator_func)

    pyxwizard.begin()
    pyxwizard.location("my_script.py")
    pyxwizard.name("MyProject")
    pyxwizard.version("2.1.0")
    pyxwizard.splash("splash.png", timeout=5)          # auto-installs Pillow
    pyxwizard.extra_flags("--uac-admin")
    pyxwizard.hook_pre(my_pre_func)
    pyxwizard.hook_post(my_post_func)
    result = pyxwizard.build()                         # returns BuildResult

    # After build
    pyxwizard.report()                                 # print dependency report
    snap = pyxwizard.snapshot()                         # environment snapshot dict
    pyxwizard.clean("MyProject")                       # remove build artefacts
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
import hashlib
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Set, Tuple, Union
from dataclasses import dataclass, field, asdict

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
APP_VERSION = "0.29.4"
DEFAULT_AUTHOR = "TRADELY.DEV"
PYINSTALLER_FLAGS = ["--onefile", "--clean", "--noconfirm"]
DEFAULT_ICON_URL = "https://doc.tradely.dev/images/tradely.ico"
SIGNTOOL_RELATIVE_PATH = "signtool/signtool.exe"
LIBRARIES_CATEGORY_FILE = "https://doc.tradely.dev/PyX/lib_categories.json"

# =============================================================================
# CONSTANTS – Build Step IDs (for callback identification)
# =============================================================================
STEP_INIT            = "init"
STEP_PROJECT_DIRS    = "project_dirs"
STEP_VENV            = "venv"
STEP_PIP_UPGRADE     = "pip_upgrade"
STEP_PYINSTALLER     = "pyinstaller_check"
STEP_DEPENDENCIES    = "dependencies"
STEP_PREPROCESS      = "preprocess"
STEP_ICON            = "icon"
STEP_VERSION_INFO    = "version_info"
STEP_SPLASH          = "splash"
STEP_PRE_HOOK        = "pre_hook"
STEP_BUILD           = "build"
STEP_LOCATE_EXE      = "locate_exe"
STEP_SIGNING         = "signing"
STEP_POST_HOOK       = "post_hook"
STEP_MANIFEST        = "manifest"
STEP_REPORT          = "report"
STEP_LOG             = "log"
STEP_COMPLETE        = "complete"

ALL_STEPS = [
    STEP_INIT, STEP_PROJECT_DIRS, STEP_VENV, STEP_PIP_UPGRADE,
    STEP_PYINSTALLER, STEP_DEPENDENCIES, STEP_PREPROCESS,
    STEP_ICON, STEP_VERSION_INFO, STEP_SPLASH, STEP_PRE_HOOK,
    STEP_BUILD, STEP_LOCATE_EXE, STEP_SIGNING, STEP_POST_HOOK,
    STEP_MANIFEST, STEP_REPORT, STEP_LOG, STEP_COMPLETE,
]

# Human-readable labels for each step
STEP_LABELS = {
    STEP_INIT:          "Initialising build",
    STEP_PROJECT_DIRS:  "Creating project structure",
    STEP_VENV:          "Setting up virtual environment",
    STEP_PIP_UPGRADE:   "Upgrading pip",
    STEP_PYINSTALLER:   "Checking PyInstaller",
    STEP_DEPENDENCIES:  "Installing dependencies",
    STEP_PREPROCESS:    "Preprocessing script",
    STEP_ICON:          "Resolving icon",
    STEP_VERSION_INFO:  "Embedding version info",
    STEP_SPLASH:        "Configuring splash screen",
    STEP_PRE_HOOK:      "Running pre-build hook",
    STEP_BUILD:         "Running PyInstaller",
    STEP_LOCATE_EXE:    "Locating executable",
    STEP_SIGNING:       "Code signing",
    STEP_POST_HOOK:     "Running post-build hook",
    STEP_MANIFEST:      "Writing manifest",
    STEP_REPORT:        "Generating dependency report",
    STEP_LOG:           "Saving build log",
    STEP_COMPLETE:      "Build complete",
}

# Progress values for each step (0.0 – 1.0)
STEP_PROGRESS = {
    STEP_INIT:          0.02,
    STEP_PROJECT_DIRS:  0.05,
    STEP_VENV:          0.15,
    STEP_PIP_UPGRADE:   0.22,
    STEP_PYINSTALLER:   0.30,
    STEP_DEPENDENCIES:  0.42,
    STEP_PREPROCESS:    0.50,
    STEP_ICON:          0.53,
    STEP_VERSION_INFO:  0.55,
    STEP_SPLASH:        0.57,
    STEP_PRE_HOOK:      0.58,
    STEP_BUILD:         0.80,
    STEP_LOCATE_EXE:    0.85,
    STEP_SIGNING:       0.90,
    STEP_POST_HOOK:     0.92,
    STEP_MANIFEST:      0.94,
    STEP_REPORT:        0.96,
    STEP_LOG:           0.98,
    STEP_COMPLETE:      1.00,
}

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


INJECTED_SPLASH_CLOSER = textwrap.dedent('''\
# --- PyX Wizard: injected splash closer (start) ---
# Close the PyInstaller splash screen once the app's Python code begins
# executing.  pyi_splash is only available inside a frozen --splash build,
# so the ImportError is expected during normal script execution.
try:
    import pyi_splash as _pyx_splash  # type: ignore[import-not-found]
    _pyx_splash.close()
except ImportError:
    pass
# --- PyX Wizard: injected splash closer (end) ---
''')


# =============================================================================
# DATA CLASSES – Build Results & Dependency Info
# =============================================================================
@dataclass
class DependencyInfo:
    """Information about a single detected dependency."""
    name: str
    category: Optional[str] = None
    pip_name: Optional[str] = None
    installed: bool = False
    install_error: Optional[str] = None


@dataclass
class StepResult:
    """Result of a single build step."""
    step_id: str
    label: str
    success: bool
    duration_seconds: float = 0.0
    message: str = ""
    skipped: bool = False


@dataclass
class BuildResult:
    """
    Comprehensive result object returned by pyxwizard.build().
    Provides everything a GUI or caller needs to display results.
    """
    success: bool = False
    exe_path: Optional[Path] = None
    exe_size_bytes: int = 0
    exe_size_mb: float = 0.0
    signed: bool = False
    project_dir: Optional[Path] = None
    dist_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    manifest_path: Optional[Path] = None
    report_path: Optional[Path] = None
    build_duration_seconds: float = 0.0
    project_name: str = ""
    author: str = ""
    script_path: Optional[Path] = None
    console_mode: bool = True
    icon_used: Optional[str] = None
    version_string: Optional[str] = None
    data_folders_count: int = 0
    data_total_size_mb: float = 0.0
    dependencies: List[DependencyInfo] = field(default_factory=list)
    step_results: List[StepResult] = field(default_factory=list)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    log_lines: List[str] = field(default_factory=list)
    pyx_version: str = APP_VERSION
    python_version: str = ""
    platform_info: str = ""
    script_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a dictionary (paths become strings)."""
        d = asdict(self)
        for key in ["exe_path", "project_dir", "dist_dir", "log_dir",
                     "manifest_path", "report_path", "script_path"]:
            if d.get(key) is not None:
                d[key] = str(d[key])
        return d

    def to_json(self, indent: int = 4) -> str:
        """Serialise to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def summary(self) -> str:
        """Return a human-readable summary string."""
        lines = []
        status = "SUCCESS" if self.success else "FAILED"
        lines.append(f"Build {status}: {self.project_name}")
        lines.append(f"  Duration: {self.build_duration_seconds:.1f}s")
        if self.exe_path:
            lines.append(f"  Executable: {self.exe_path}")
            lines.append(f"  Size: {self.exe_size_mb:.1f} MB")
        lines.append(f"  Signed: {'Yes' if self.signed else 'No'}")
        lines.append(f"  Dependencies: {len(self.dependencies)}")
        if self.error_message:
            lines.append(f"  Error: {self.error_message}")
        lines.append(f"  Steps completed: {sum(1 for s in self.step_results if s.success)}/{len(self.step_results)}")
        return "\n".join(lines)

    def __bool__(self) -> bool:
        """Allow ``if result:`` for backwards compatibility."""
        return self.success


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
    print(f"  {_TermStyle.GREEN}●{_TermStyle.RESET}  {msg}")

def _warn(msg: str) -> None:
    print(f"  {_TermStyle.YELLOW}⚠{_TermStyle.RESET}  {_TermStyle.YELLOW}{msg}{_TermStyle.RESET}")

def _error(msg: str) -> None:
    print(f"  {_TermStyle.RED}✕{_TermStyle.RESET}  {_TermStyle.RED}{msg}{_TermStyle.RESET}")

def _success(msg: str) -> None:
    print(f"  {_TermStyle.GREEN}✓{_TermStyle.RESET}  {_TermStyle.GREEN}{msg}{_TermStyle.RESET}")

def _detail(msg: str) -> None:
    print(f"  {_TermStyle.GREY}   {msg}{_TermStyle.RESET}")

def _progress_bar(label: str, current: float, total: float = 1.0, width: int = 40) -> None:
    S = _TermStyle
    ratio = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    print(f"\r  {S.GREEN}{bar}{S.RESET}  {pct:>3}%  {S.GREY}{label}{S.RESET}", end="", flush=True)
    if ratio >= 1.0:
        print()


# =============================================================================
# CORE HELPER FUNCTIONS (unchanged from v1 – backwards compatible)
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
    """Validate a PFX/P12 certificate file."""
    if not CRYPTOGRAPHY_AVAILABLE:
        return False
    try:
        pfx_data = pfx_path.read_bytes()
        pkcs12.load_key_and_certificates(
            pfx_data, password.encode("utf-8"), default_backend()
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
            process.returncode, cmd, output="\n".join(output_lines)
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
    python_exe: Path, *packages: str, log: Callable[[str], None]
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
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, creationflags=creation_flags
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_script_deps(
    python_exe: Path, script_path: Path, log: Callable[[str], None]
) -> List[DependencyInfo]:
    """
    Detect and install third-party imports into the virtual environment.
    Returns a list of DependencyInfo for each dependency (NEW in v2).
    """
    detected_imports = detect_script_imports(script_path)
    dep_results: List[DependencyInfo] = []

    if not detected_imports:
        log("No third-party dependencies detected.")
        return dep_results

    log(f"Detected third-party imports: {', '.join(detected_imports)}")

    for package_name in detected_imports:
        dep = DependencyInfo(
            name=package_name,
            category=_get_category(package_name),
            pip_name=_lib_copy_metadata.get(package_name, package_name),
        )
        if venv_has_package(python_exe, package_name):
            log(f"  Package '{package_name}' is already installed.")
            dep.installed = True
        else:
            pip_name = dep.pip_name or package_name
            log(f"  Installing '{pip_name}'...")
            try:
                venv_pip_install(python_exe, pip_name, log=log)
                dep.installed = True
            except subprocess.CalledProcessError as install_error:
                log(
                    f"  WARNING: Failed to install '{pip_name}'. "
                    f"It may be a local module or have a different pip name. "
                    f"Error: {install_error}"
                )
                dep.install_error = str(install_error)
        dep_results.append(dep)

    return dep_results


def sign_exe(
    exe: Path, pfx: Path, pwd: str, log: Callable[[str], None],
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
        str(signtool_path), "sign",
        "/f", str(pfx), "/p", pwd,
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


def preprocess_script(
    script_path: Path,
    temp_dir: Path,
    splash_enabled: bool = False,
) -> Path:
    """Create a preprocessed copy of the target script with injected helpers.

    Parameters
    ----------
    script_path : Path
        The original (or self-stripped) script to preprocess.
    temp_dir : Path
        Temporary directory for the preprocessed output.
    splash_enabled : bool
        When True, inject code that closes the PyInstaller splash screen
        once the app's Python code begins executing.
    """
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

        # Inject splash closer right after the path helper block
        if splash_enabled and "# --- PyX Wizard: injected splash closer (start) ---" not in source_code:
            # Find the end of the path helper we just inserted
            splash_pos = None
            for idx, line in enumerate(lines):
                if "# --- PyX Wizard: injected path helper (end) ---" in line:
                    splash_pos = idx + 1
                    break
            if splash_pos is None:
                # Path helper wasn't injected (had top-level resolver) —
                # fall back to right after the last import.
                splash_pos = last_import_line_index + 1 if last_import_line_index >= 0 else 0
            splash_lines = INJECTED_SPLASH_CLOSER.split("\n")
            for offset, splash_line in enumerate(splash_lines):
                lines.insert(splash_pos + offset, splash_line)

        modified_source = "\n".join(lines)

        packaged_pattern = re.compile(
            r"""(?P<quote>["'])packaged-within-exe:(?P<relpath>[^"']+)(?P=quote)"""
        )
        modified_source = packaged_pattern.sub(
            r'_resolve_packaged_path("\g<relpath>")',
            modified_source
        )

    # Even if has_toplevel_resolver was True we still need splash closer
    if has_toplevel_resolver and splash_enabled:
        if "# --- PyX Wizard: injected splash closer (start) ---" not in modified_source:
            modified_source = INJECTED_SPLASH_CLOSER + "\n" + modified_source

    temp_script_path = temp_dir / script_path.name
    temp_script_path.write_text(modified_source, encoding="utf-8")
    return temp_script_path


def _strip_pyxwizard_from_script(script_path: Path, temp_dir: Path) -> Path:
    """For 'self' mode: remove all pyxwizard references from the script."""
    source = script_path.read_text(encoding="utf-8", errors="replace")
    lines = source.split("\n")
    cleaned: List[str] = []

    for line in lines:
        stripped = line.strip()
        if re.match(r'^(import\s+pyxwizard|from\s+pyxwizard\s+import)', stripped, re.IGNORECASE):
            continue
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
# NEW v2 HELPER – Version Info File Generation (Windows EXE properties)
# =============================================================================
def _generate_version_info(
    version_str: str,
    project_name: str,
    author: str,
    description: str = "",
    output_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Generate a PyInstaller-compatible version info file that embeds
    File Version, Product Name, Company Name, etc. into the EXE
    properties (right-click → Properties → Details on Windows).

    Parameters
    ----------
    version_str : str
        A version string like "1.2.3" or "2.0.0.1".
    project_name : str
        Used as ProductName and InternalName.
    author : str
        Used as CompanyName and LegalCopyright.
    description : str
        Used as FileDescription.
    output_path : Path, optional
        Where to write the version file.  If None, a temp file is created.

    Returns
    -------
    Path or None
        The path to the generated .py version file, or None on error.
    """
    parts = version_str.replace("-", ".").split(".")
    while len(parts) < 4:
        parts.append("0")
    numeric = []
    for p in parts[:4]:
        digits = re.sub(r'[^0-9]', '', p)
        numeric.append(int(digits) if digits else 0)

    ver_tuple = tuple(numeric)
    ver_csv = ", ".join(str(v) for v in ver_tuple)

    content = textwrap.dedent(f'''\
# UTF-8
# PyX Wizard auto-generated version info
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({ver_csv}),
    prodvers=({ver_csv}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'{author}'),
            StringStruct(u'FileDescription', u'{description or project_name}'),
            StringStruct(u'FileVersion', u'{version_str}'),
            StringStruct(u'InternalName', u'{project_name}'),
            StringStruct(u'LegalCopyright', u'© {datetime.datetime.now().year} {author}'),
            StringStruct(u'OriginalFilename', u'{project_name}.exe'),
            StringStruct(u'ProductName', u'{project_name}'),
            StringStruct(u'ProductVersion', u'{version_str}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
''')
    try:
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix="_version.py", prefix="pyx_"))
        output_path.write_text(content, encoding="utf-8")
        return output_path
    except Exception:
        return None


# =============================================================================
# NEW v2 HELPER – Dependency Report Writer
# =============================================================================
def _write_dependency_report(
    project_dir: Path,
    deps: List[DependencyInfo],
    script_path: Path,
    project_name: str,
) -> Path:
    """
    Write a dependency_report.txt into the project directory showing
    all detected imports, their categories, install status, and pip names.
    """
    report_path = project_dir / "dependency_report.txt"
    lines = [
        f"PyX Wizard – Dependency Report",
        f"{'=' * 50}",
        f"Project:  {project_name}",
        f"Script:   {script_path}",
        f"Date:     {datetime.datetime.now().isoformat()}",
        f"",
        f"{'Library':<25} {'Category':<18} {'Pip Name':<22} {'Status'}",
        f"{'-' * 25} {'-' * 18} {'-' * 22} {'-' * 12}",
    ]
    for dep in deps:
        cat = dep.category or "—"
        pip = dep.pip_name or dep.name
        if dep.installed:
            status = "✓ Installed"
        elif dep.install_error:
            status = "✕ Failed"
        else:
            status = "? Unknown"
        lines.append(f"{dep.name:<25} {cat:<18} {pip:<22} {status}")

    if not deps:
        lines.append("  (no third-party dependencies detected)")

    lines.append("")
    lines.append(f"Total: {len(deps)} dependencies, "
                 f"{sum(1 for d in deps if d.installed)} installed, "
                 f"{sum(1 for d in deps if d.install_error)} failed")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# =============================================================================
# NEW v2 HELPER – Environment Snapshot
# =============================================================================
def _create_snapshot(
    project_dir: Path,
    python_exe: Path,
    log: Callable[[str], None]
) -> Dict[str, Any]:
    """
    Capture a snapshot of the virtual environment: installed packages,
    Python version, platform, etc.  Saved as environment_snapshot.json.
    """
    snapshot: Dict[str, Any] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_sys": sys.version,
        "packages": [],
    }

    # Get pip freeze from the venv
    try:
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "freeze"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=30, creationflags=creation_flags
        )
        if result.returncode == 0:
            snapshot["packages"] = [
                line.strip() for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
    except Exception as e:
        log(f"WARNING: Could not capture pip freeze: {e}")

    snapshot_path = project_dir / "environment_snapshot.json"
    snapshot_path.write_text(
        json.dumps(snapshot, indent=4, default=str), encoding="utf-8"
    )

    return snapshot


# =============================================================================
# NEW v2 HELPER – File Hash
# =============================================================================
def _file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# PyX WIZARD CLASS – The Library Interface (v2 with callbacks)
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

        # --- NEW v2 state ---
        self._version_string: Optional[str] = None
        self._description: str = ""
        self._splash_image: Optional[str] = None
        self._splash_timeout: int = 5
        self._extra_flags: List[str] = []
        self._hook_pre_fn: Optional[Callable[[], None]] = None
        self._hook_post_fn: Optional[Callable[[BuildResult], None]] = None
        self._on_progress_fn: Optional[Callable[[float, str], None]] = None
        self._on_log_fn: Optional[Callable[[str], None]] = None
        self._on_step_fn: Optional[Callable[[str, str, float], None]] = None
        self._dry_run: bool = False
        self._feedback_mode: str = "full"  # "full", "step", "finish", "none"

    def _reset(self) -> None:
        """Reset all state for a fresh configuration.

        Feedback mode and callbacks are intentionally preserved so that
        callers can set them before ``begin()`` without losing them.
        """
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

        # Reset v2 build-config state (NOT feedback/callbacks)
        self._version_string = None
        self._description = ""
        self._splash_image = None
        self._splash_timeout = 5
        self._extra_flags = []
        self._hook_pre_fn = None
        self._hook_post_fn = None
        self._dry_run = False
        # NOTE: _feedback_mode, _on_progress_fn, _on_log_fn, _on_step_fn
        #       are deliberately NOT reset here so they persist across
        #       begin() calls.  Users may set feedback("none") and wire
        #       callbacks before calling begin().

    def _log(self, message: str) -> None:
        """Log a message to internal buffer, terminal (if full), and external callback."""
        self._log_lines.append(message)
        if self._feedback_mode == "full":
            _detail(message)
        if self._on_log_fn is not None:
            try:
                self._on_log_fn(message)
            except Exception:
                pass

    def _emit_progress(self, value: float, label: str) -> None:
        """Emit progress to terminal (if full) and callback."""
        if self._feedback_mode == "full":
            _progress_bar(label, value)
        if self._on_progress_fn is not None:
            try:
                self._on_progress_fn(value, label)
            except Exception:
                pass

    def _emit_step(self, step_id: str) -> None:
        """Emit a step change to terminal (if full or step) and callback."""
        label = STEP_LABELS.get(step_id, step_id)
        progress = STEP_PROGRESS.get(step_id, 0.0)
        if self._feedback_mode in ("full", "step"):
            _header(label.upper())
        if self._on_step_fn is not None:
            try:
                self._on_step_fn(step_id, label, progress)
            except Exception:
                pass

    # Shorthand feedback-level checks used throughout the class
    def _fb_full(self) -> bool:
        """True when full terminal output is enabled."""
        return self._feedback_mode == "full"

    def _fb_any(self) -> bool:
        """True when any terminal output is enabled (full, step, or finish)."""
        return self._feedback_mode != "none"

    def _fb_step(self) -> bool:
        """True when step-level or full output is enabled."""
        return self._feedback_mode in ("full", "step")

    def _fb_finish(self) -> bool:
        """True when at least finish-level output is enabled."""
        return self._feedback_mode in ("full", "step", "finish")

    def _get_base_dir(self) -> Path:
        if self._out_location is not None:
            return self._out_location
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        if self._script_path:
            return self._script_path.parent
        return Path.cwd()

    # -------------------------------------------------------------------------
    # PUBLIC API METHODS (v1 – unchanged signatures)
    # -------------------------------------------------------------------------
    def begin(self) -> None:
        """Initialise PyX Wizard. Must be called first."""
        self._reset()
        self._initialised = True
        if self._fb_full():
            _banner()
            _info("PyX Wizard initialised.")
            _info(f"Platform: {platform.system()} {platform.machine()}")
            _info(f"Python: {sys.version.split()[0]}")
            _info(f"Default author: {self._author}")

        if not self._lib_fetch_done:
            if self._fb_full():
                _info("Fetching library categories from remote...")
            success = _fetch_lib_categories()
            self._lib_fetch_done = True
            if success:
                cat_count = len(_lib_categories)
                if self._fb_full():
                    _success(f"Library categories loaded ({cat_count} libraries catalogued).")
            else:
                if self._fb_full():
                    _warn("Could not fetch library categories (no internet?). Build will continue without categorisation.")

    def location(self, script_path: str) -> None:
        """Set the Python script to package."""
        if not self._initialised:
            _error("pyxwizard.begin() must be called before pyxwizard.location().")
            raise RuntimeError("pyxwizard.begin() must be called first.")

        if self._fb_full():
            _header("SCRIPT LOCATION")

        if script_path.lower() == "self":
            _this_file = os.path.abspath(__file__)
            caller_file = None
            for _frame in inspect.stack():
                if os.path.abspath(_frame.filename) != _this_file:
                    caller_file = _frame.filename
                    break
            if caller_file and os.path.isfile(caller_file):
                self._script_path = Path(caller_file).resolve()
                self._self_mode = True
                if self._fb_full():
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
                if self._fb_full():
                    _warn(f"File does not have .py extension: {resolved}")
            self._script_path = resolved
            self._self_mode = False
            if self._fb_full():
                _info(f"Script: {self._script_path}")

        self._detected_imports = detect_script_imports(self._script_path)
        if self._fb_full():
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

        if self._fb_full():
            _header("PROJECT NAME")

        sanitised = re.sub(r'[^\w\-.]', '_', project_name.strip())
        if not sanitised:
            _error(f"Invalid project name: '{project_name}'")
            raise ValueError(f"Invalid project name: '{project_name}'")

        self._project_name = sanitised
        if self._fb_full():
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
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._author = author_name.strip() if author_name.strip() else DEFAULT_AUTHOR
        if self._fb_full():
            _header("AUTHOR")
            _info(f"Author set to: {self._author}")

    def console(self, enabled: bool = True) -> None:
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._console_mode = bool(enabled)
        if self._fb_full():
            _header("CONSOLE MODE")
            if self._console_mode:
                _info("Console mode: ON (console window will be shown)")
            else:
                _info("Console mode: OFF (no console window — GUI/windowed mode)")

    def icon(self, icon_path: str) -> None:
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._fb_full():
            _header("CUSTOM ICON")
        resolved = Path(icon_path).resolve()
        if not resolved.exists():
            _error(f"Icon file not found: {resolved}")
            raise FileNotFoundError(f"Icon file not found: {resolved}")
        if resolved.suffix.lower() != ".ico":
            if self._fb_full():
                _warn(f"Icon file is not .ico format: {resolved.suffix}")
        self._icon_path = str(resolved)
        if self._fb_full():
            _info(f"Custom icon: {self._icon_path}")
            _info(f"Icon size: {resolved.stat().st_size:,} bytes")

    def data(self, *folder_paths: str) -> None:
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._fb_full():
            _header("DATA FOLDERS")
        if not folder_paths:
            if self._fb_full():
                _info("No data folders specified.")
            return

        total_bytes = 0
        for fp in folder_paths:
            resolved = Path(fp).resolve()
            if not resolved.exists():
                raise FileNotFoundError(f"Data folder not found: {resolved}")
            if not resolved.is_dir():
                raise NotADirectoryError(f"Not a directory: {resolved}")
            size = folder_size(resolved)
            total_bytes += size
            size_mb = size / (1024 * 1024)
            self._data_folders.append(resolved)
            if self._fb_full():
                marker = "  ⚠ (>50 MB — large!)" if size_mb > 50 else ""
                _info(f"Added: {resolved}")
                _detail(f"  → bundled as '{resolved.name}/' ({size_mb:.1f} MB){marker}")

        total_mb = total_bytes / (1024 * 1024)
        if self._fb_full():
            _info(f"Total data size: {total_mb:.1f} MB across {len(folder_paths)} folder(s)")
            if total_mb > 100:
                _warn("Total data exceeds 100 MB. The EXE may be very large.")

    def cert(self, certificate_path: str, password: str, signtool_path: Optional[str] = None) -> None:
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._fb_full():
            _header("CODE SIGNING CERTIFICATE")
        resolved = Path(certificate_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Certificate not found: {resolved}")
        self._pfx_path = resolved
        self._pfx_password = password
        if self._fb_full():
            _info(f"Certificate: {self._pfx_path}")
        if signtool_path:
            st = Path(signtool_path).resolve()
            if not st.exists():
                if self._fb_full():
                    _warn(f"signtool.exe not found at: {st}")
            else:
                if self._fb_full():
                    _info(f"signtool.exe: {st}")
            self._signtool_path = str(st)
        if CRYPTOGRAPHY_AVAILABLE:
            if self._fb_full():
                _info("Validating certificate...")
            if validate_pfx(self._pfx_path, self._pfx_password):
                if self._fb_full():
                    _success("Certificate validated successfully.")
            else:
                if self._fb_full():
                    _error("Certificate validation failed (bad password or corrupted file).")
                    _warn("Signing will still be attempted during build.")
        else:
            if self._fb_full():
                _warn("'cryptography' package not installed — cannot pre-validate certificate.")

    def outlocation(self, path: str) -> None:
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._fb_full():
            _header("OUTPUT LOCATION")
        resolved = Path(path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        self._out_location = resolved
        if self._fb_full():
            _info(f"Output base: {self._out_location}")
            _info(f"PyX_Data will be created at: {self._out_location / 'PyX_Data'}")

    # -------------------------------------------------------------------------
    # NEW v2 PUBLIC API METHODS
    # -------------------------------------------------------------------------
    def version(self, version_str: str, description: str = "") -> None:
        """Set a version string to embed in the EXE file properties (Windows)."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._version_string = version_str.strip()
        self._description = description.strip()
        if self._fb_full():
            _header("VERSION INFO")
            _info(f"Version: {self._version_string}")
            if self._description:
                _info(f"Description: {self._description}")

    def splash(self, image_path: str, timeout: int = 5) -> None:
        """Configure a splash screen image shown during EXE startup."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        resolved = Path(image_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Splash image not found: {resolved}")
        self._splash_image = str(resolved)
        self._splash_timeout = max(1, timeout)
        if self._fb_full():
            _header("SPLASH SCREEN")
            _info(f"Splash image: {self._splash_image}")
            _info(f"Timeout: {self._splash_timeout}s")

    def extra_flags(self, *flags: str) -> None:
        """Add extra PyInstaller CLI flags (e.g. '--uac-admin', '--debug all')."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._extra_flags.extend(flags)
        if self._fb_full():
            _header("EXTRA FLAGS")
            _info(f"Added: {' '.join(flags)}")

    def hook_pre(self, fn: Callable[[], None]) -> None:
        """Register a function to run just before PyInstaller executes."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._hook_pre_fn = fn
        if self._fb_full():
            _info("Pre-build hook registered.")

    def hook_post(self, fn: Callable) -> None:
        """Register a function to run after a successful build.  Receives BuildResult."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        self._hook_post_fn = fn
        if self._fb_full():
            _info("Post-build hook registered.")

    def on_progress(self, fn: Callable[[float, str], None]) -> None:
        """Subscribe to progress updates.  fn(value: 0.0–1.0, label: str)."""
        self._on_progress_fn = fn

    def on_log(self, fn: Callable[[str], None]) -> None:
        """Subscribe to log messages.  fn(message: str)."""
        self._on_log_fn = fn

    def on_step(self, fn: Callable[[str, str, float], None]) -> None:
        """Subscribe to step changes.  fn(step_id, label, progress)."""
        self._on_step_fn = fn

    def feedback(self, mode: str = "full") -> None:
        """
        Set the terminal output level.

        Parameters
        ----------
        mode : str
            One of:
            - "full"   — all output: banner, headers, progress bars, per-line detail (default)
            - "step"   — step headers and summary only, no per-line detail
            - "finish" — only the final BUILD SUCCESSFUL / BUILD FAILED summary
            - "none"   — no terminal output at all (callbacks still fire)
        """
        mode = mode.strip().lower()
        if mode not in ("full", "step", "finish", "none"):
            raise ValueError(
                f"Invalid feedback mode '{mode}'. "
                f"Must be one of: 'full', 'step', 'finish', 'none'."
            )
        self._feedback_mode = mode

    def dry_run(self, enabled: bool = True) -> None:
        """Enable dry-run mode – validates everything but skips PyInstaller."""
        self._dry_run = bool(enabled)
        if self._fb_full():
            if enabled:
                _info("Dry-run mode enabled — PyInstaller will be skipped.")
            else:
                _info("Dry-run mode disabled.")

    # -------------------------------------------------------------------------
    # BUILD (v2 – returns BuildResult, fires callbacks at each step)
    # -------------------------------------------------------------------------
    def build(self) -> "BuildResult":
        """
        Execute the full build process.

        Returns
        -------
        BuildResult
            A comprehensive result object.  BuildResult is truthy when
            success=True (so ``if pyxwizard.build():`` still works)
            and has an ``exe_path`` attribute.
        """
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")
        if self._script_path is None:
            raise RuntimeError("No script specified.")
        if self._project_name is None:
            raise RuntimeError("No project name specified.")

        result = BuildResult(
            project_name=self._project_name,
            author=self._author,
            script_path=self._script_path,
            console_mode=self._console_mode,
            version_string=self._version_string,
            data_folders_count=len(self._data_folders),
            python_version=sys.version.split()[0],
            platform_info=f"{platform.system()} {platform.machine()}",
        )

        # Script hash
        try:
            result.script_hash = _file_sha256(self._script_path)
        except Exception:
            pass

        # Data size
        total_data_bytes = sum(folder_size(f) for f in self._data_folders)
        result.data_total_size_mb = total_data_bytes / (1024 * 1024)

        self._emit_step(STEP_INIT)
        S = _TermStyle
        if self._fb_full():
            print()
            print(f"  {S.BOLD}{S.WHITE}Project:  {S.GREEN}{self._project_name}{S.RESET}")
            print(f"  {S.BOLD}{S.WHITE}Script:   {S.RESET}{self._script_path}")
            print(f"  {S.BOLD}{S.WHITE}Author:   {S.RESET}{self._author}")
            print(f"  {S.BOLD}{S.WHITE}Console:  {S.RESET}{'Yes' if self._console_mode else 'No'}")
            print(f"  {S.BOLD}{S.WHITE}Icon:     {S.RESET}{self._icon_path or '(default Tradely)'}")
            print(f"  {S.BOLD}{S.WHITE}Data:     {S.RESET}{len(self._data_folders)} folder(s)")
            print(f"  {S.BOLD}{S.WHITE}Signing:  {S.RESET}{'Yes' if self._pfx_path else 'No'}")
            if self._version_string:
                print(f"  {S.BOLD}{S.WHITE}Version:  {S.RESET}{self._version_string}")
            if self._splash_image:
                print(f"  {S.BOLD}{S.WHITE}Splash:   {S.RESET}{self._splash_image}")
            if self._extra_flags:
                print(f"  {S.BOLD}{S.WHITE}Flags:    {S.RESET}{' '.join(self._extra_flags)}")
            if self._dry_run:
                print(f"  {S.BOLD}{S.YELLOW}DRY RUN{S.RESET}")
            print()

        base_dir = self._get_base_dir()
        pyx_data_dir = base_dir / "PyX_Data"
        project_dir = pyx_data_dir / self._project_name
        result.project_dir = project_dir
        result.dist_dir = project_dir / "dist"
        result.log_dir = project_dir / "logs"

        temp_dir: Optional[Path] = None
        signed = False
        build_start = time.time()
        self._log_lines = []
        step_results: List[StepResult] = []
        python_exe: Optional[Path] = None

        def _do_step(step_id: str, fn: Callable[[], str]) -> StepResult:
            """Run a step, time it, record the result."""
            self._emit_step(step_id)
            label = STEP_LABELS.get(step_id, step_id)
            progress = STEP_PROGRESS.get(step_id, 0.0)
            self._emit_progress(progress, label)
            t0 = time.time()
            try:
                msg = fn()
                sr = StepResult(step_id, label, True, time.time() - t0, msg or "")
            except Exception as e:
                sr = StepResult(step_id, label, False, time.time() - t0, str(e))
                raise
            finally:
                step_results.append(sr)
            return sr

        try:
            # STEP: Project structure
            def _step_project_dirs():
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
                return "Project structure created"
            _do_step(STEP_PROJECT_DIRS, _step_project_dirs)

            # STEP: Virtual environment
            def _step_venv():
                nonlocal python_exe
                self._log("")
                self._log("--- Virtual Environment ---")
                python_exe = create_project_venv(project_dir, self._log)
                if self._fb_full():
                    _success(f"Virtual environment ready: {python_exe}")
                return str(python_exe)
            _do_step(STEP_VENV, _step_venv)

            # STEP: Upgrade pip
            def _step_pip():
                self._log("")
                self._log("--- Upgrading pip ---")
                try:
                    run_cmd([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], self._log)
                    return "pip upgraded"
                except subprocess.CalledProcessError as e:
                    self._log(f"WARNING: pip upgrade failed: {e}")
                    return f"pip upgrade failed (non-fatal): {e}"
            _do_step(STEP_PIP_UPGRADE, _step_pip)

            # STEP: PyInstaller check
            def _step_pyinstaller():
                self._log("")
                self._log("--- PyInstaller ---")
                if not venv_has_package(python_exe, "PyInstaller"):
                    self._log("PyInstaller not found in venv. Installing...")
                    venv_pip_install(python_exe, "pyinstaller", log=self._log)
                    return "PyInstaller installed"
                else:
                    self._log("PyInstaller is already installed.")
                    return "PyInstaller already present"
            _do_step(STEP_PYINSTALLER, _step_pyinstaller)

            # STEP: Dependencies
            def _step_deps():
                self._log("")
                self._log("--- Dependencies ---")
                dep_infos = install_script_deps(python_exe, self._script_path, self._log)
                result.dependencies = dep_infos
                return f"{len(dep_infos)} dependencies processed"
            _do_step(STEP_DEPENDENCIES, _step_deps)

            # STEP: Preprocess script
            def _step_preprocess():
                nonlocal temp_dir
                self._log("")
                self._log("--- Script Preprocessing ---")
                temp_dir = Path(tempfile.mkdtemp(prefix="pyx_build_"))

                # Splash closer is injected into the script so it
                # auto-closes once the app's Python code starts running.
                _splash = bool(self._splash_image)

                if self._self_mode:
                    if self._fb_full():
                        _info("Stripping pyxwizard commands from self-referencing script...")
                    self._log("Stripping pyxwizard library calls from script (self mode)...")
                    stripped_script = _strip_pyxwizard_from_script(self._script_path, temp_dir)
                    cleaned_in_project = project_dir / self._script_path.name
                    cleaned_in_project.write_text(
                        stripped_script.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                    self._log(f"Cleaned script written to: {cleaned_in_project}")
                    preprocessed = preprocess_script(stripped_script, temp_dir, splash_enabled=_splash)
                else:
                    preprocessed = preprocess_script(self._script_path, temp_dir, splash_enabled=_splash)

                self._log(f"Preprocessed script: {preprocessed}")
                return str(preprocessed)
            sr_preprocess = _do_step(STEP_PREPROCESS, _step_preprocess)
            preprocessed_script = Path(sr_preprocess.message)

            # STEP: Icon
            def _step_icon():
                effective = self._icon_path
                if effective is None or not Path(effective).exists():
                    self._log("")
                    self._log("--- Icon ---")
                    self._log("No custom icon provided. Downloading default icon...")
                    effective = _download_icon(base_dir)
                    if effective:
                        self._log(f"Default icon: {effective}")
                    else:
                        self._log("WARNING: Could not download default icon.")
                result.icon_used = effective
                return effective or "no icon"
            _do_step(STEP_ICON, _step_icon)

            # STEP: Version info (NEW v2)
            version_file: Optional[Path] = None
            def _step_version_info():
                nonlocal version_file
                if self._version_string:
                    self._log("")
                    self._log("--- Version Info ---")
                    version_file = _generate_version_info(
                        self._version_string, self._project_name,
                        self._author, self._description,
                        output_path=temp_dir / "version_info.py" if temp_dir else None
                    )
                    if version_file:
                        self._log(f"Version info file: {version_file}")
                        return str(version_file)
                return "skipped"
            sr_vi = _do_step(STEP_VERSION_INFO, _step_version_info)
            if sr_vi.message == "skipped":
                step_results[-1].skipped = True

            # STEP: Splash (NEW v2)
            def _step_splash():
                if self._splash_image:
                    self._log("")
                    self._log(f"--- Splash Screen ---")
                    self._log(f"Splash image: {self._splash_image}")

                    # PyInstaller --splash requires Pillow for image processing
                    if not venv_has_package(python_exe, "PIL"):
                        self._log("Splash requires Pillow — installing into venv...")
                        try:
                            venv_pip_install(python_exe, "Pillow", log=self._log)
                        except subprocess.CalledProcessError as e:
                            self._log(f"WARNING: Could not install Pillow: {e}")
                            self._log("Splash screen will be skipped.")
                            self._splash_image = None
                            return "skipped (Pillow install failed)"

                    # PyInstaller --splash also requires tkinter at build time
                    if not venv_has_package(python_exe, "tkinter"):
                        self._log(
                            "WARNING: tkinter is not available in the build "
                            "environment.  The --splash flag requires Tk.  "
                            "Splash screen will be skipped."
                        )
                        if self._fb_step():
                            _warn(
                                "tkinter not available — splash screen skipped. "
                                "Re-install Python with Tk support to enable it."
                            )
                        self._splash_image = None
                        return "skipped (tkinter unavailable)"

                    return self._splash_image
                return "skipped"
            sr_splash = _do_step(STEP_SPLASH, _step_splash)
            if sr_splash.message.startswith("skipped"):
                step_results[-1].skipped = True

            # STEP: Pre-build hook (NEW v2)
            def _step_pre_hook():
                if self._hook_pre_fn:
                    self._log("")
                    self._log("--- Pre-Build Hook ---")
                    self._hook_pre_fn()
                    return "executed"
                return "skipped"
            sr_pre = _do_step(STEP_PRE_HOOK, _step_pre_hook)
            if sr_pre.message == "skipped":
                step_results[-1].skipped = True

            # STEP: PyInstaller build
            def _step_build():
                self._log("")
                self._log("--- PyInstaller Build ---")

                if self._dry_run:
                    self._log("DRY RUN — skipping PyInstaller execution.")
                    return "dry run"

                pyinstaller_cmd: List[str] = [
                    str(python_exe), "-m", "PyInstaller"
                ]
                pyinstaller_cmd.extend(PYINSTALLER_FLAGS)
                pyinstaller_cmd.extend(["--name", self._project_name])
                pyinstaller_cmd.extend(["--distpath", str(project_dir / "dist")])
                pyinstaller_cmd.extend(["--workpath", str(project_dir / "build")])

                if not self._console_mode:
                    pyinstaller_cmd.append("--noconsole")

                if result.icon_used and Path(result.icon_used).exists():
                    pyinstaller_cmd.extend(["--icon", result.icon_used])

                # Version info file
                if version_file and version_file.exists():
                    pyinstaller_cmd.extend(["--version-file", str(version_file)])

                # Splash screen
                if self._splash_image and Path(self._splash_image).exists():
                    pyinstaller_cmd.extend(["--splash", self._splash_image])

                # Hidden imports
                detected_imports = self._detected_imports
                for import_name in detected_imports:
                    top_level = import_name.split(".")[0]
                    if top_level.isidentifier() and top_level.lower() != "pyinstaller":
                        pyinstaller_cmd.extend(["--hidden-import", top_level])

                # Collect-all
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

                # Extra flags (NEW v2)
                if self._extra_flags:
                    pyinstaller_cmd.extend(self._extra_flags)
                    self._log(f"extra flags: {' '.join(self._extra_flags)}")

                pyinstaller_cmd.append(str(preprocessed_script))

                self._log(f"Command: {' '.join(str(c) for c in pyinstaller_cmd)}")
                self._log("")

                try:
                    run_cmd(pyinstaller_cmd, self._log, cwd=str(project_dir))
                except subprocess.CalledProcessError as pyi_error:
                    # Extract useful details from the PyInstaller output
                    output_text = getattr(pyi_error, "output", "") or ""
                    # Surface the real error instead of just the exit code
                    short_output = "\n".join(output_text.splitlines()[-30:]) if output_text else ""
                    self._log(f"PyInstaller failed (exit code {pyi_error.returncode}).")
                    if short_output:
                        self._log(f"Last output:\n{short_output}")
                    raise

                return "build complete"
            _do_step(STEP_BUILD, _step_build)

            # STEP: Locate executable
            exe_path: Optional[Path] = None
            def _step_locate():
                nonlocal exe_path
                self._log("")
                self._log("--- Locating Executable ---")

                if self._dry_run:
                    self._log("DRY RUN — no executable to locate.")
                    return "dry run"

                dist_dir = project_dir / "dist"
                exe_name = self._project_name + (".exe" if platform.system() == "Windows" else "")
                exe_path = dist_dir / exe_name

                if not exe_path.exists():
                    possible_exes = list(dist_dir.glob("*"))
                    if possible_exes:
                        exe_path = possible_exes[0]
                        self._log(f"Found executable: {exe_path}")
                    else:
                        raise FileNotFoundError(
                            f"No executable found in {dist_dir}. Build may have failed."
                        )
                else:
                    self._log(f"Executable located: {exe_path}")

                result.exe_path = exe_path
                result.exe_size_bytes = exe_path.stat().st_size
                result.exe_size_mb = result.exe_size_bytes / (1024 * 1024)
                return str(exe_path)
            _do_step(STEP_LOCATE_EXE, _step_locate)

            # STEP: Code signing
            def _step_signing():
                nonlocal signed
                if self._pfx_path is not None and self._pfx_password is not None:
                    self._log("")
                    self._log("--- Code Signing ---")
                    if self._dry_run:
                        self._log("DRY RUN — skipping code signing.")
                        return "dry run"
                    try:
                        sign_exe(exe_path, self._pfx_path, self._pfx_password,
                                 self._log, self._signtool_path)
                        signed = True
                        return "signed"
                    except Exception as sign_error:
                        self._log(f"WARNING: Code signing failed: {sign_error}")
                        return f"signing failed: {sign_error}"
                else:
                    self._log("")
                    self._log("--- Code Signing ---")
                    self._log("No certificate provided. Skipping.")
                    return "skipped"
            sr_sign = _do_step(STEP_SIGNING, _step_signing)
            result.signed = signed
            if sr_sign.message == "skipped":
                step_results[-1].skipped = True

            # STEP: Post-build hook (NEW v2)
            def _step_post_hook():
                if self._hook_post_fn:
                    self._log("")
                    self._log("--- Post-Build Hook ---")
                    self._hook_post_fn(result)
                    return "executed"
                return "skipped"
            sr_post = _do_step(STEP_POST_HOOK, _step_post_hook)
            if sr_post.message == "skipped":
                step_results[-1].skipped = True

            # STEP: Manifest
            def _step_manifest():
                self._log("")
                self._log("--- Manifest ---")
                manifest_data = {
                    "created": datetime.datetime.now().isoformat(),
                    "author": self._author,
                    "project": self._project_name,
                    "script": str(self._script_path),
                    "exe": str(exe_path) if exe_path else None,
                    "signed": signed,
                    "pyx_version": APP_VERSION,
                    "console_mode": self._console_mode,
                    "version_string": self._version_string,
                    "data_folders": [str(f) for f in self._data_folders],
                    "script_hash": result.script_hash,
                    "dry_run": self._dry_run,
                }
                write_manifest(project_dir, manifest_data)
                result.manifest_path = project_dir / "pyx_manifest.json"
                self._log(f"Manifest: {result.manifest_path}")
                return str(result.manifest_path)
            _do_step(STEP_MANIFEST, _step_manifest)

            # STEP: Dependency report (NEW v2)
            def _step_report():
                self._log("")
                self._log("--- Dependency Report ---")
                report_path = _write_dependency_report(
                    project_dir, result.dependencies,
                    self._script_path, self._project_name
                )
                result.report_path = report_path
                self._log(f"Report: {report_path}")

                # Environment snapshot
                if python_exe:
                    _create_snapshot(project_dir, python_exe, self._log)
                    self._log(f"Snapshot: {project_dir / 'environment_snapshot.json'}")

                return str(report_path)
            _do_step(STEP_REPORT, _step_report)

            # STEP: Build log
            def _step_log():
                self._log("")
                self._log("--- Build Log ---")
                write_build_log(project_dir, self._log_lines)
                self._log(f"Log saved to: {project_dir / 'logs'}")
                return str(project_dir / "logs")
            _do_step(STEP_LOG, _step_log)

            # COMPLETE
            elapsed = time.time() - build_start
            result.success = True
            result.build_duration_seconds = elapsed
            result.step_results = step_results
            result.log_lines = list(self._log_lines)

            self._emit_step(STEP_COMPLETE)
            self._emit_progress(1.0, "Build complete")

            self._log("")
            self._log(f"=== BUILD SUCCESSFUL ===")
            self._log(f"Executable: {exe_path}")
            self._log(f"Build time: {elapsed:.1f}s")

            if self._fb_finish():
                print()
                print(f"  {S.GREEN}{S.BOLD}╔══════════════════════════════════════════════════╗{S.RESET}")
                print(f"  {S.GREEN}{S.BOLD}║              BUILD SUCCESSFUL                    ║{S.RESET}")
                print(f"  {S.GREEN}{S.BOLD}╚══════════════════════════════════════════════════╝{S.RESET}")
                print()
                if exe_path:
                    _success(f"Executable:  {exe_path}")
                    _success(f"Size:        {result.exe_size_mb:.1f} MB")
                _success(f"Signed:      {'Yes' if signed else 'No'}")
                _success(f"Build time:  {elapsed:.1f}s")
                _success(f"Log folder:  {project_dir / 'logs'}")
                _success(f"Report:      {result.report_path}")
                print()

            # Save full result as JSON
            try:
                result_json_path = project_dir / "build_result.json"
                result_json_path.write_text(result.to_json(), encoding="utf-8")
            except Exception:
                pass

            return result

        except Exception as build_error:
            elapsed = time.time() - build_start
            self._log("")
            self._log(f"=== BUILD FAILED ===")
            self._log(f"Error: {build_error}")

            result.success = False
            result.build_duration_seconds = elapsed
            result.error_message = str(build_error)
            result.error_traceback = traceback.format_exc()
            result.step_results = step_results
            result.log_lines = list(self._log_lines)

            try:
                if project_dir.exists():
                    write_build_log(project_dir, self._log_lines)
            except Exception:
                pass

            if self._fb_finish():
                print()
                print(f"  {S.RED}{S.BOLD}╔══════════════════════════════════════════════════╗{S.RESET}")
                print(f"  {S.RED}{S.BOLD}║              BUILD FAILED                        ║{S.RESET}")
                print(f"  {S.RED}{S.BOLD}╚══════════════════════════════════════════════════╝{S.RESET}")
                print()
                _error(f"Error: {build_error}")
                _error(f"Build time: {elapsed:.1f}s")
                print()

            return result

        finally:
            if temp_dir is not None and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    self._log(f"WARNING: Could not clean up temp dir: {cleanup_error}")

    # -------------------------------------------------------------------------
    # NEW v2: REPORT / SNAPSHOT / CLEAN / REBUILD
    # -------------------------------------------------------------------------
    def get_report(self) -> str:
        """Print and return the last dependency report as a formatted string."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")

        base_dir = self._get_base_dir()
        if self._project_name:
            report_path = base_dir / "PyX_Data" / self._project_name / "dependency_report.txt"
            if report_path.exists():
                text = report_path.read_text(encoding="utf-8")
                if self._fb_full():
                    print(text)
                return text

        if self._fb_full():
            _warn("No dependency report found. Run a build first.")
        return ""

    def get_snapshot(self) -> Dict[str, Any]:
        """Return the last environment snapshot as a dictionary."""
        if not self._initialised:
            raise RuntimeError("pyxwizard.begin() must be called first.")

        base_dir = self._get_base_dir()
        if self._project_name:
            snap_path = base_dir / "PyX_Data" / self._project_name / "environment_snapshot.json"
            if snap_path.exists():
                return json.loads(snap_path.read_text(encoding="utf-8"))

        if self._fb_full():
            _warn("No snapshot found. Run a build first.")
        return {}

    def clean(self, project_name: Optional[str] = None) -> bool:
        """
        Remove build artefacts (build/, dist/) for a project, keeping the
        venv and logs.  Pass a project name or uses the current project.
        """
        pname = project_name or self._project_name
        if not pname:
            if self._fb_full():
                _warn("No project name specified for clean.")
            return False

        base_dir = self._get_base_dir()
        project_dir = base_dir / "PyX_Data" / pname

        if not project_dir.exists():
            if self._fb_full():
                _warn(f"Project directory not found: {project_dir}")
            return False

        removed = []
        for folder_name in ["build", "dist"]:
            folder = project_dir / folder_name
            if folder.exists():
                shutil.rmtree(folder)
                removed.append(folder_name)

        if self._fb_full():
            if removed:
                _success(f"Cleaned: {', '.join(removed)} from {project_dir}")
            else:
                _info("Nothing to clean.")

        return bool(removed)

    def purge(self, project_name: Optional[str] = None) -> bool:
        """
        Completely remove a project directory (venv, build, dist, logs, everything).
        """
        pname = project_name or self._project_name
        if not pname:
            if self._fb_full():
                _warn("No project name specified for purge.")
            return False

        base_dir = self._get_base_dir()
        project_dir = base_dir / "PyX_Data" / pname

        if not project_dir.exists():
            if self._fb_full():
                _warn(f"Project directory not found: {project_dir}")
            return False

        shutil.rmtree(project_dir)
        if self._fb_full():
            _success(f"Purged: {project_dir}")
        return True

    def rebuild(self) -> "BuildResult":
        """Re-run the build with the current configuration (shortcut)."""
        return self.build()


# =============================================================================
# MODULE-LEVEL SINGLETON & PUBLIC API
# =============================================================================
_wizard = _PyXWizard()


# --- v1 API (unchanged) ---
def begin() -> None:
    """Initialise PyX Wizard. Must be called before any other pyxwizard command."""
    _wizard.begin()

def location(script_path: str) -> None:
    """Set the Python script to package (path or "self")."""
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
    """Add data folders to bundle into the executable."""
    _wizard.data(*folder_paths)

def cert(certificate_path: str, password: str, signtool_path: Optional[str] = None) -> None:
    """Set a PFX/P12 certificate for code signing."""
    _wizard.cert(certificate_path, password, signtool_path)

def outlocation(path: str) -> None:
    """Set the base directory where PyX_Data/ will be created."""
    _wizard.outlocation(path)

def build() -> BuildResult:
    """Execute the full build process. Returns a BuildResult object."""
    return _wizard.build()


# --- v2 API (new) ---
def version(version_str: str, description: str = "") -> None:
    """Set a version string to embed in the EXE file properties (Windows)."""
    _wizard.version(version_str, description)

def splash(image_path: str, timeout: int = 5) -> None:
    """Configure a splash screen image shown during EXE startup."""
    _wizard.splash(image_path, timeout)

def extra_flags(*flags: str) -> None:
    """Add extra PyInstaller CLI flags (e.g. '--uac-admin')."""
    _wizard.extra_flags(*flags)

def hook_pre(fn: Callable[[], None]) -> None:
    """Register a function to run just before PyInstaller executes."""
    _wizard.hook_pre(fn)

def hook_post(fn: Callable) -> None:
    """Register a function to run after a successful build. Receives BuildResult."""
    _wizard.hook_post(fn)

def on_progress(fn: Callable[[float, str], None]) -> None:
    """Subscribe to progress updates. fn(value: 0.0–1.0, label: str)."""
    _wizard.on_progress(fn)

def on_log(fn: Callable[[str], None]) -> None:
    """Subscribe to log messages. fn(message: str)."""
    _wizard.on_log(fn)

def on_step(fn: Callable[[str, str, float], None]) -> None:
    """Subscribe to step changes. fn(step_id, label, progress)."""
    _wizard.on_step(fn)

def feedback(mode: str = "full") -> None:
    """
    Set the terminal output level.

    Parameters
    ----------
    mode : str
        "full"   — all output: banner, headers, progress bars, per-line detail (default)
        "step"   — step headers and summary only, no per-line detail
        "finish" — only the final BUILD SUCCESSFUL / BUILD FAILED summary
        "none"   — no terminal output at all (callbacks still fire)
    """
    _wizard.feedback(mode)

def dry_run(enabled: bool = True) -> None:
    """Enable dry-run mode — validates everything but skips PyInstaller."""
    _wizard.dry_run(enabled)

def report() -> str:
    """Print and return the last dependency report."""
    return _wizard.get_report()

def snapshot() -> Dict[str, Any]:
    """Return the last environment snapshot as a dictionary."""
    return _wizard.get_snapshot()

def clean(project_name: Optional[str] = None) -> bool:
    """Remove build artefacts (build/, dist/) for a project."""
    return _wizard.clean(project_name)

def purge(project_name: Optional[str] = None) -> bool:
    """Completely remove a project directory."""
    return _wizard.purge(project_name)

def rebuild() -> BuildResult:
    """Re-run the build with the current configuration."""
    return _wizard.rebuild()

def get_steps() -> List[Dict[str, Any]]:
    """Return the list of all build steps with their IDs, labels, and progress values."""
    return [
        {"id": s, "label": STEP_LABELS[s], "progress": STEP_PROGRESS[s]}
        for s in ALL_STEPS
    ]

def get_version() -> str:
    """Return the pyxwizard library version string."""
    return APP_VERSION
