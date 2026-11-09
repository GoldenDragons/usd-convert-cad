# Local deployment (Windows)

Runtime: Python 3.12, isolated in `.venv`.
Converter: `usd-convert-cad==0.3.0`.

Run from PowerShell in this project directory:

```powershell
.\Convert-CAD.cmd --help
.\Convert-CAD.cmd -i "D:\Models\assembly.step" -o "D:\Models\assembly.usdc"
```

The launcher also works from another directory when invoked by its full path.
Input and output relative paths are resolved against your current directory.
No environment activation, server, port, Omniverse Kit, or separate OpenUSD installation is needed.
Output extensions: `.usd`, `.usda`, `.usdc`, `.usdz`.
Check `$LASTEXITCODE` and the output file after conversion.

To recreate the environment with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install usd-convert-cad==0.3.0
.\Convert-CAD.cmd --help
```

Deployment verification artifacts are under `.local-deployment`.
The small STL smoke test verifies runtime conversion and USD mesh readability;
it does not validate a particular CAD assembly, proprietary reader, or source material fidelity.
See `LICENSE.md` for NVIDIA terms and `LIMITATIONS.md` for format limitations.
