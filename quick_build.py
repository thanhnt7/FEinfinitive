#!/usr/bin/env python3
# Quick build script for FurTorch v5 - Fast iteration during development

import subprocess
import sys
import os
import shutil

print("FurTorch v5 - Quick Build")
print("-" * 40)

# Quick file check
if not os.path.exists("furtorch_v5.py"):
    print("❌ furtorch_v5.py not found!")
    sys.exit(1)

if not os.path.exists("full_table.json"):
    print("❌ full_table.json not found!")
    sys.exit(1)

print("✓ Files found")

# Clean old build
print("\nCleaning old build...")
for item in ["build", "dist", "furtorch_v5.spec"]:
    if os.path.exists(item):
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

# Build
print("\nBuilding (this takes ~3 minutes)...")
build_cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--name=FurTorch_v5",
    "--add-data=full_table.json;.",
    "--hidden-import=win32gui",
    "--hidden-import=win32process",
    "--hidden-import=win32api",
    "--hidden-import=psutil",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.ttk",
    "--collect-all=win32",
    "--clean",
    "--noconfirm",
    "furtorch_v5.py"
]

try:
    subprocess.run(build_cmd, check=True, capture_output=True)
    print("✓ Build complete!")

    if os.path.exists("dist/FurTorch_v5.exe"):
        size_mb = os.path.getsize("dist/FurTorch_v5.exe") / 1024 / 1024
        print(f"\n✓✓✓ SUCCESS! ✓✓✓")
        print(f"Executable: dist/FurTorch_v5.exe ({size_mb:.1f} MB)")
    else:
        print("❌ Executable not found in dist/")
        sys.exit(1)

except subprocess.CalledProcessError as e:
    print("❌ Build failed!")
    print(e.stderr.decode() if e.stderr else "Unknown error")
    sys.exit(1)
