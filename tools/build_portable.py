"""Build a GUI EXE plus an isolated CPython/CAD runtime without freezing USD."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "win32" or sys.version_info[:2] != (3, 12):
        raise SystemExit("Build with Windows x64 Python 3.12")
    if importlib.metadata.version("usd-convert-cad") != "0.3.0":
        raise SystemExit("Expected usd-convert-cad==0.3.0")
    # Never erase an existing release; each build has a unique directory.
    from datetime import datetime
    tag = datetime.now().strftime("%Y%m%d-%H%M%S")
    release = ROOT / "dist" / tag
    release.mkdir(parents=True)
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
        "--onedir", "--name", "CADConverter", "--paths", str(ROOT),
        "--distpath", str(release), "--workpath", str(ROOT / "build" / tag),
        "--specpath", str(ROOT / "build"), str(ROOT / "desktop" / "main.py"),
    ], cwd=ROOT, check=True)
    bundle = release / "CADConverter"
    runtime = bundle / "runtime"
    runtime.mkdir()
    base = Path(sys.base_prefix)
    for pattern in ("python.exe", "python3.dll", "python312.dll", "vcruntime*.dll", "LICENSE.txt"):
        for item in base.glob(pattern):
            shutil.copy2(item, runtime / item.name)
    shutil.copytree(base / "DLLs", runtime / "DLLs",
                    ignore=shutil.ignore_patterns("*.pdb", "*.lib", "*.exp"))
    shutil.copytree(base / "Lib", runtime / "Lib",
                    ignore=shutil.ignore_patterns("site-packages", "__pycache__", "test", "tests", "idlelib", "ensurepip"))
    site = Path(sys.prefix) / "Lib" / "site-packages"
    target = runtime / "Lib" / "site-packages"
    target.mkdir()
    for name in ("usd_convert_cad", "omni"):
        shutil.copytree(site / name, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.lib"))
    for item in site.glob("usd_convert_cad-*.dist-info"):
        shutil.copytree(item, target / item.name)
    (runtime / "python312._pth").write_text(".\nLib\nDLLs\nLib/site-packages\n", encoding="ascii")
    for name in ("LICENSE.md", "THIRD_PARTY_NOTICES.md", "LIMITATIONS.md", "DESKTOP-README.md"):
        shutil.copy2(ROOT / name, bundle / name)
    manifest = {"converter": "0.3.0", "python": sys.version, "files": {}}
    for file in sorted(bundle.rglob("*")):
        if file.is_file():
            manifest["files"][file.relative_to(bundle).as_posix()] = hashlib.file_digest(file.open("rb"), "sha256").hexdigest()
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = release / "CADConverter-Windows-x64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for file in bundle.rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(release))
    print(json.dumps({"folder": str(bundle), "zip": str(archive)}, ensure_ascii=False))
    (ROOT / ".local-deployment" / "latest-build.json").write_text(
        json.dumps({"folder": str(bundle), "zip": str(archive)}), encoding="utf-8")


if __name__ == "__main__":
    main()
