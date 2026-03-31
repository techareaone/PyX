"""
PyX Wizard
==========
A Python library that packages Python scripts into standalone Windows
executables using PyInstaller, with automatic dependency detection,
virtual environment isolation, optional code signing, and data bundling.

Version: 0.29.3
Author:  TRADELY.DEV
"""

from .pyxwizard import (
    # Core v1 API
    begin,
    location,
    name,
    author,
    console,
    icon,
    data,
    cert,
    outlocation,
    build,

    # Extended v2 API
    version,
    splash,
    extra_flags,
    hook_pre,
    hook_post,
    on_progress,
    on_log,
    on_step,
    feedback,
    dry_run,
    report,
    snapshot,
    clean,
    purge,
    rebuild,
    get_steps,
    get_version,

    # Public types
    BuildResult,

    # Step ID constants
    STEP_INIT,
    STEP_PROJECT_DIRS,
    STEP_VENV,
    STEP_PIP_UPGRADE,
    STEP_PYINSTALLER,
    STEP_DEPENDENCIES,
    STEP_PREPROCESS,
    STEP_ICON,
    STEP_VERSION_INFO,
    STEP_SPLASH,
    STEP_PRE_HOOK,
    STEP_BUILD,
    STEP_LOCATE_EXE,
    STEP_SIGNING,
    STEP_POST_HOOK,
    STEP_MANIFEST,
    STEP_REPORT,
    STEP_LOG,
    STEP_COMPLETE,

    # Step metadata
    ALL_STEPS,
    STEP_LABELS,
    STEP_PROGRESS,

    # Package metadata
    APP_VERSION,
    DEFAULT_AUTHOR,
)

__version__ = APP_VERSION
__author__ = DEFAULT_AUTHOR

__all__ = [
    # Core v1 API
    "begin",
    "location",
    "name",
    "author",
    "console",
    "icon",
    "data",
    "cert",
    "outlocation",
    "build",

    # Extended v2 API
    "version",
    "splash",
    "extra_flags",
    "hook_pre",
    "hook_post",
    "on_progress",
    "on_log",
    "on_step",
    "feedback",
    "dry_run",
    "report",
    "snapshot",
    "clean",
    "purge",
    "rebuild",
    "get_steps",
    "get_version",

    # Public types
    "BuildResult",

    # Step ID constants
    "STEP_INIT",
    "STEP_PROJECT_DIRS",
    "STEP_VENV",
    "STEP_PIP_UPGRADE",
    "STEP_PYINSTALLER",
    "STEP_DEPENDENCIES",
    "STEP_PREPROCESS",
    "STEP_ICON",
    "STEP_VERSION_INFO",
    "STEP_SPLASH",
    "STEP_PRE_HOOK",
    "STEP_BUILD",
    "STEP_LOCATE_EXE",
    "STEP_SIGNING",
    "STEP_POST_HOOK",
    "STEP_MANIFEST",
    "STEP_REPORT",
    "STEP_LOG",
    "STEP_COMPLETE",

    # Step metadata
    "ALL_STEPS",
    "STEP_LABELS",
    "STEP_PROGRESS",

    # Package metadata
    "APP_VERSION",
    "DEFAULT_AUTHOR",
]
