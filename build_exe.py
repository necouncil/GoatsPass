#!/usr/bin/env python3
"""
GoatsPass — Build script for Windows EXE (and Linux binary)
Usage:
    python build_exe.py              # auto-detect platform
    python build_exe.py --windows    # cross-compile hint (run on Windows)
    python build_exe.py --onefile    # single .exe (default)
    python build_exe.py --onedir     # folder with exe (faster startup)
"""

import sys
import subprocess
import shutil
import platform
import argparse
from pathlib import Path

HERE = Path(__file__).parent
MAIN = HERE / "goatspass.py"
ICON = HERE / "icon.png"
ICON_ICO = HERE / "icon.ico"
DIST = HERE / "dist"
BUILD = HERE / "build"

IS_WIN = platform.system() == "Windows"


def banner():
    print("\n  GoatsPass — EXE Builder")
    print("  " + "─" * 40)


def ensure_pyinstaller():
    try:
        import PyInstaller
        print(f"  [✓] PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("  [~] Installing PyInstaller...")
        flags = ["--quiet"]
        if not IS_WIN:
            flags.append("--break-system-packages")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + flags + ["pyinstaller"])
        print("  [✓] PyInstaller installed")


def png_to_ico():
    """Convert icon.png to icon.ico for Windows EXE"""
    if ICON_ICO.exists():
        print(f"  [✓] icon.ico already exists")
        return str(ICON_ICO)
    if not ICON.exists():
        print("  [!] No icon.png found, using default")
        return None
    try:
        from PIL import Image
        img = Image.open(ICON)
        sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
        ico_imgs = []
        for s in sizes:
            resized = img.resize(s, Image.LANCZOS)
            if resized.mode != "RGBA":
                resized = resized.convert("RGBA")
            ico_imgs.append(resized)
        ico_imgs[0].save(
            ICON_ICO, format="ICO",
            sizes=[i.size for i in ico_imgs],
            append_images=ico_imgs[1:]
        )
        print(f"  [✓] icon.ico created")
        return str(ICON_ICO)
    except Exception as e:
        print(f"  [!] Could not convert icon: {e}")
        return None


def build(onefile=True):
    banner()
    ensure_pyinstaller()

    icon_path = None
    if IS_WIN:
        icon_path = png_to_ico()
    elif ICON.exists():
        icon_path = str(ICON)

    # Clean previous builds
    for d in [DIST, BUILD]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  [~] Cleaned {d.name}/")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "GoatsPass",
        "--clean",
        "--noconfirm",
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Windows: no console window
    if IS_WIN:
        cmd.append("--windowed")

    if icon_path:
        cmd += ["--icon", icon_path]

    # Bundle icon.png as data file
    if ICON.exists():
        sep = ";" if IS_WIN else ":"
        cmd += ["--add-data", f"{ICON}{sep}."]

    # Hidden imports
    cmd += [
        "--hidden-import", "cryptography",
        "--hidden-import", "argon2",
        "--hidden-import", "PIL",
        "--hidden-import", "tkinter",
    ]

    cmd.append(str(MAIN))

    print(f"\n  [~] Running PyInstaller...")
    print(f"  [~] Mode: {'onefile' if onefile else 'onedir'}")
    print()

    result = subprocess.run(cmd, cwd=str(HERE))

    if result.returncode != 0:
        print("\n  [ERROR] Build failed!")
        sys.exit(1)

    # Find output
    if onefile:
        if IS_WIN:
            out = DIST / "GoatsPass.exe"
        else:
            out = DIST / "GoatsPass"
    else:
        if IS_WIN:
            out = DIST / "GoatsPass" / "GoatsPass.exe"
        else:
            out = DIST / "GoatsPass" / "GoatsPass"

    print()
    if out.exists():
        size_mb = out.stat().st_size / 1024 / 1024
        print(f"  ✅  Build successful!")
        print(f"  ─────────────────────────────────────")
        print(f"  Output: {out}")
        print(f"  Size:   {size_mb:.1f} MB")
    else:
        print(f"  ✅  Build done! Check dist/ folder")
    print()

    # Clean build artifacts (keep dist)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    spec_file = HERE / "GoatsPass.spec"
    if spec_file.exists():
        spec_file.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build GoatsPass executable")
    parser.add_argument("--onedir", action="store_true",
                        help="Build as folder (faster startup)")
    args = parser.parse_args()
    build(onefile=not args.onedir)
