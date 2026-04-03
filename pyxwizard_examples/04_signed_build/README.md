# Example 04 — Code Signing

**What it shows:** Signing the finished EXE with a PFX certificate so
Windows SmartScreen trusts it and your publisher name shows in UAC prompts.

## Files
| File | Purpose |
|---|---|
| `build.py` | PyX Wizard build script |
| `release_app.py` | The app being packaged and signed |
| `certs/` | *(create this folder)* Place your `.pfx` here |

## Setup
1. Obtain a code-signing certificate (`.pfx` or `.p12`).
2. Place it at `certs/my_cert.pfx`.
3. Set the `PFX_PASSWORD` environment variable:
   ```
   set PFX_PASSWORD=your_secret_password
   ```
4. Update `SIGNTOOL` in `build.py` to point to your `signtool.exe`  
   (or remove it if `signtool` is already on your PATH).
5. Run `python build.py`.

## Key API call
```python
pyxwizard.cert("certs/my_cert.pfx", password, signtool_path)
```
`signtool_path` is optional when `signtool.exe` is on your PATH.

## Security note
Never hard-code your PFX password. Use `os.environ.get("PFX_PASSWORD")` or
a secrets manager in production.
