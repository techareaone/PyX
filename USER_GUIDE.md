# PyX User Guide

Hey! So you want to turn your Python script into a proper `.exe` file that you can share with people who don't have Python installed? That's exactly what PyX does. This guide will walk you through every step and cover the stuff that commonly goes wrong.

---

## Before You Start

A couple of things to sort out before you open PyX:

**Make sure Python is installed on your machine.**
PyX bundles itself without needing Python, but it needs to find Python on your system to actually *build* your script. Open a terminal and type `python --version`. If you get a version number back, you're good. If you get an error, head to [python.org](https://python.org) and install it — and make sure to tick the "Add Python to PATH" box during installation.

**Add some antivirus exclusions.**
This is boring but important. Windows antivirus (and most third-party ones) will often freak out at PyInstaller-built executables because they look suspicious to automated scanners — even when they're completely safe. Before you build anything, add these folders/files to your antivirus exclusions:

- The folder where your `.py` script lives.
- The script file itself.
- The `PyX_Data` folder that PyX will create next to the app.

If you skip this step, your antivirus might delete your script mid-build, or quarantine your freshly built `.exe` the moment it appears.

---

## Opening PyX

Just double-click `PyX.exe`. That's it. No installation, no setup.

When it loads, you'll see a dark green window with a step list on the left side. You'll move through those steps one by one.

---

## Step 0 — Welcome

The first screen is the welcome screen. It shows you a summary of features and reminds you about antivirus exclusions (yes, again — it's that important).

Hit **Get Started →** when you're ready.

---

## Step 1 — Select Your Script

Click **Browse** and find your `.py` file.

Once you select it, PyX will scan it and show you all the third-party libraries it detected — things like `requests`, `pandas`, `customtkinter`, etc. These will all be automatically installed before the build starts, so you don't have to worry about them.

Standard Python stuff (`os`, `sys`, `json`, etc.) won't show up here because they're built in and PyX knows to ignore them.

> **Heads up:** PyX detects imports by reading your code statically. If your script imports something in a weird dynamic way (like `__import__("some_lib")`), it might not catch it. You can still build and the worst that happens is the exe crashes on that specific line — just something to be aware of.

Hit **Next →** when you're happy.

---

## Step 2 — Project Config

This is where you name your project and set a few options.

**Project Name**
This becomes the name of your `.exe` file and the folder PyX creates for it. Keep it simple — letters, numbers, hyphens, and underscores are all fine. Spaces and special characters get automatically replaced with underscores.

**Show console window**
If your script opens a GUI (a window, a dashboard, anything visual), uncheck this. If your script prints stuff to a terminal and that output matters, leave it checked. If you're not sure, leave it checked — you can always rebuild.

**Custom Icon**
Optionally browse for a `.ico` file to use as the exe's icon. If you leave this blank, PyX will download the default Tradely icon from the internet. No icon file on your machine is fine — it handles it automatically.

> **Tip:** You can convert a PNG to ICO for free using [icoconvert.com](https://icoconvert.com) if you want a custom icon but only have a PNG.

Hit **Next →**.

---

## Step 3 — Data Folders (Optional)

Got files your script needs to read at runtime? Images, config files, databases, sounds? This is where you bundle them into your exe.

Click **+ Add Folder** and select the folder containing those files. You can add multiple folders.

**Important:** In your script, instead of loading files with a normal path like:
```python
open("assets/image.png")
```

You need to use the special prefix that PyX understands:
```python
open("packaged-within-exe:assets/image.png")
```

PyX automatically rewrites those strings before building so that when the exe runs, it knows to look inside itself for that file. If you don't use this prefix for files you've bundled, they won't be found when the exe runs.

If your script doesn't need any extra files, just skip this step and hit **Next →**.

---

## Step 4 — Code Signing (Optional)

Code signing lets you attach a digital certificate to your exe so Windows (and users) can verify it came from you. This is completely optional — your exe will work fine without it.

If you have a `.pfx` or `.p12` certificate file, browse for it here and enter the password. Click **Validate** to check the password is correct before proceeding.

A couple of things to know:

- **Self-signed certificates** are fine for testing or internal use, but Windows SmartScreen will still warn users about the exe. For a certificate that removes the SmartScreen warning, you need a commercially issued code-signing certificate from a provider like DigiCert or Sectigo.
- The `cryptography` Python package needs to be installed for the certificate validation button to work. If it's not installed, PyX will tell you — but signing will still be *attempted* at build time even without it.

Skip this step entirely if you don't need signing.

---

## Step 5 — Build

You're here! Hit the big **▶ BUILD** button.

The log area will fill up with output as PyX:
1. Creates a project folder under `PyX_Data/`
2. Sets up a clean Python virtual environment
3. Installs your script's dependencies
4. Runs PyInstaller to package everything
5. Optionally signs the exe
6. Saves a build log and a manifest file

The progress bar gives you a rough sense of where things are. Builds typically take anywhere from 30 seconds to a few minutes depending on how many dependencies your script has.

When it's done, you'll see **Build completed successfully!** and two new buttons appear: **Open Output Folder** and **Open Log Folder**.

Your exe lives in `PyX_Data/<ProjectName>/dist/<ProjectName>.exe`.

If you need to rebuild (you changed your script, for example), hit **▶ REBUILD**. The existing virtual environment is reused so subsequent builds are faster.

---

## Common Errors and How to Fix Them

### "Could not find a Python interpreter on PATH"

PyX can't find Python. Either Python isn't installed, or it wasn't added to your system PATH during installation.

**Fix:** Reinstall Python from [python.org](https://python.org) and make sure you tick **"Add Python to PATH"** on the installer screen. After reinstalling, close and reopen PyX.

---

### The build finishes but the exe crashes immediately when run

This usually means a dependency wasn't detected or included correctly.

**Fix:** Open the log folder and look at the build log. Search for `WARNING` lines — they'll often tell you which package failed to install. If it's a package with an unusual name (where the import name differs from the pip name, like `sklearn` vs `scikit-learn`), PyX usually handles this automatically via its remote library manifest. If it's something custom or local, you may need to make sure that module is on the same machine.

---

### The exe works on your machine but not on someone else's

**Most likely cause:** A Visual C++ redistributable is missing on their machine, or your script is reading files from absolute paths that only exist on your computer.

**Fix for the file path issue:** Use the `packaged-within-exe:` prefix for any files you bundle (see Step 3 above), and make sure those files are actually added as data folders. Never use absolute paths like `C:\Users\YourName\Documents\config.json` in scripts you intend to distribute.

---

### Antivirus quarantines the output exe

This is a known false-positive issue with PyInstaller. It doesn't mean your exe is malware — it's just that PyInstaller executables look structurally similar to some malware packing techniques.

**Fix:** Add the `PyX_Data/` folder and its contents to your antivirus exclusions. If you're distributing the exe to others, consider getting it code-signed (Step 4) with a commercial certificate — this significantly reduces false positive rates.

---

### "Build Failed" dialog pops up with a long error message

Check the build log for the full details. The most common causes are:

- **Antivirus interfering mid-build** — add the exclusions mentioned at the top of this guide.
- **A required package can't be installed** — the package might have a different pip name, or might require a C compiler. The log will show exactly which `pip install` failed.
- **Script has a syntax error** — PyX runs the script through an AST parser; if your script has a Python syntax error, it'll fail at the import detection stage. Fix the syntax error in your script and try again.

---

### The globe icon at the bottom shows "No internet, can't categorise"

This just means PyX couldn't download its remote library categories file. Your build will still work — PyX falls back to a built-in list of common packages. The library categories are only used to label imports in the UI, and to load additional PyInstaller hints for certain packages.

**Fix:** Check your internet connection. If you're behind a corporate firewall or proxy, PyX might not be able to reach `doc.tradely.dev`. The build will still proceed normally.

---

### PyX opens but immediately closes, or shows nothing

This can happen if `customtkinter` isn't installed when running the `.py` source file directly.

**Fix:** If you're running the source file (not the `.exe`), install the dependency:
```
pip install customtkinter
```
If you're running the exe and it's closing immediately, check the Windows Event Viewer or try running it from a terminal to see any error output.

---

### "This project already exists. The existing virtual environment will be reused."

This isn't an error — it's just a heads-up. If you've built this project before, PyX will reuse the virtual environment it already created, which makes rebuilds faster. Everything else gets rebuilt fresh.

If you suspect the virtual environment is corrupted or has a bad package install, delete the `PyX_Data/<ProjectName>/venv/` folder and rebuild. PyX will recreate it.

---

## Where Are My Files?

Everything PyX creates lives in the `PyX_Data/` folder next to `PyX.exe`.

```
PyX_Data/
└── YourProjectName/
    ├── dist/           ← Your finished exe is here
    ├── build/          ← PyInstaller temporary files (safe to ignore)
    ├── logs/           ← Timestamped build logs
    ├── venv/           ← Virtual environment (safe to delete to force a clean rebuild)
    └── pyx_manifest.json  ← Info about the build
```

---

## That's It!

If something goes wrong that isn't covered here, open the log folder — the build log has the full output from every command PyX ran, which is usually enough to diagnose what went wrong.

Good luck with your project! 🚀
