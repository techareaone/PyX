"""
PyX Wizard — Example 04: Code Signing
=======================================
Demonstrates signing the built EXE with a PFX/P12 certificate.
Signed EXEs pass Windows SmartScreen checks and display your
publisher name in the UAC prompt.

Requirements:
    pip install pyxwizard
    A valid .pfx or .p12 code-signing certificate

Usage:
    python build.py

Notes:
    - signtool.exe ships with the Windows SDK / Visual Studio.
    - If signtool is on your PATH, you can omit the third argument to cert().
    - Store your PFX password securely; never hard-code it in production.
      Use an environment variable or a secrets manager instead.
"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure we're in the script's directory

import pyxwizard

# ── Configuration ────────────────────────────────────────────────────────────
CERT_PATH   = "certs/my_cert.pfx"
CERT_PASS   = os.environ.get("PFX_PASSWORD", "change_me")   # use env var in prod
SIGNTOOL    = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
# ─────────────────────────────────────────────────────────────────────────────

pyxwizard.begin()
pyxwizard.location("release_app.py")
pyxwizard.name("ReleaseApp")
pyxwizard.console(False)
pyxwizard.author("ACME Corp")
pyxwizard.version("2.0.0", "ACME Release Application")

# Sign the EXE after it is built
# cert(pfx_path, password, signtool_path?)
# signtool_path is optional if signtool.exe is on your system PATH
pyxwizard.cert(CERT_PATH, CERT_PASS, SIGNTOOL)

result = pyxwizard.build()

if result:
    print(f"✅ Built and signed: {result.exe_path}")
    print(f"   Signed  : {result.signed}")
    print(f"   Version : {result.version_string}")
else:
    print(f"❌ Failed: {result.error_message}")
