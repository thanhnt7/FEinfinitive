# build_v5.py
# Complete build script for FurTorch v5 with fixed log path

import subprocess
import sys
import os
import shutil
from datetime import datetime

print("="*70)
print("FurTorch v5.0 - Portable Builder")
print("FIXED: Correct log path with \\UE_game\\ folder")
print("="*70)
print()

# Step 1: Check files
print("[1/6] Checking required files...")
required = {
    "furtorch_v5.py": "Main application",
    "full_table.json": "Item database",
    "id_table.json": "Item ID mappings"
}

missing = []
for file, desc in required.items():
    if os.path.exists(file):
        size = os.path.getsize(file) / 1024
        print(f"  ✓ {file} ({size:.1f} KB) - {desc}")
    else:
        print(f"  ❌ {file} - MISSING!")
        missing.append(file)

if missing:
    print(f"\n❌ Missing files: {', '.join(missing)}")
    print("\nMake sure you have:")
    print("  • furtorch_v5.py (the new fixed code)")
    print("  • full_table.json (from original)")
    print("  • id_table.json (from original)")
    input("\nPress Enter to exit...")
    sys.exit(1)

print("✓ All files present\n")

# Step 2: Install dependencies
print("[2/6] Installing dependencies...")
deps = ["pywin32", "psutil", "pyinstaller"]
for dep in deps:
    try:
        print(f"  Installing {dep}...", end=" ")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        print("✓")
    except:
        print("⚠ (might be already installed)")

print("✓ Dependencies ready\n")

# Step 3: Clean old builds
print("[3/6] Cleaning old builds...")
to_remove = ["build", "dist", "__pycache__", "FurTorch_v5_Portable"]
to_remove_files = ["furtorch_v5.spec"]

for folder in to_remove:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"  ✓ Removed {folder}/")

for file in to_remove_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"  ✓ Removed {file}")

print("✓ Cleanup done\n")

# Step 4: Build executable
print("[4/6] Building executable...")
print("  This takes 3-5 minutes, please wait...\n")

build_cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--name=FurTorch_v5",
    "--add-data=full_table.json;.",
    "--add-data=id_table.json;.",
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

print("  Running PyInstaller...")
try:
    result = subprocess.run(build_cmd, 
                          capture_output=True, 
                          text=True,
                          check=True)
    print("✓ Build successful!\n")
except subprocess.CalledProcessError as e:
    print("❌ Build failed!\n")
    print("Error output:")
    print(e.stderr)
    input("\nPress Enter to exit...")
    sys.exit(1)

# Step 5: Create portable package
print("[5/6] Creating portable package...")

portable_dir = "FurTorch_v5_Portable"
os.makedirs(portable_dir, exist_ok=True)

# Copy exe
if not os.path.exists("dist/FurTorch_v5.exe"):
    print("❌ Executable not found!")
    input("Press Enter to exit...")
    sys.exit(1)

shutil.copy2("dist/FurTorch_v5.exe", portable_dir)
exe_size = os.path.getsize(f"{portable_dir}/FurTorch_v5.exe") / 1024 / 1024
print(f"  ✓ FurTorch_v5.exe ({exe_size:.1f} MB)")

# Copy data files
shutil.copy2("full_table.json", portable_dir)
shutil.copy2("id_table.json", portable_dir)
print("  ✓ Data files copied")

# Create README
readme = """FurTorch v5.0 - Drop Tracker
=============================

WHAT'S NEW IN v5:
✓ FIXED: Correct log path detection (now includes \\UE_game\\)
✓ Better error messages
✓ Console output for debugging
✓ Dual-path search (compatible with different installations)

QUICK START:
1. Start Torchlight: Infinite
2. Enable logging: Settings → Other → "开启日志"
3. RESTART the game (very important!)
4. Double-click FurTorch_v5.exe
5. Status should say "✓ Game detected! Log monitoring active!"
6. Play and pick up items!

TROUBLESHOOTING:

Q: Status says "Game not detected"
A: Make sure game is running BEFORE starting FurTorch

Q: Status says "Log file not found"
A: 1. Enable logging in game settings
   2. RESTART the game completely
   3. Log file will be created at:
      Game\\UE_game\\Torchlight\\Saved\\Logs\\UE_game.log

Q: No drops showing
A: 1. Make sure you PICK UP items (not just see them drop)
   2. Check console window for debug messages
   3. Check if drop_log.txt is being created

Q: How to see debug messages?
A: Run from command prompt to see console output:
   cmd → cd to folder → FurTorch_v5.exe

FEATURES:
• Real-time drop tracking
• Automatic map detection
• Profit calculation with tax option
• English UI with Chinese data support
• Export statistics to JSON
• Original parser (same as index.py)

CONTROLS:
• ▶ Start - Manually start map tracking
• ⏹ End - Manually end map tracking  
• Total/Current - Toggle view mode
• Drops - View detailed drop list
• Settings - Configure options
• Export - Save to JSON
• Reset - Clear all stats

SETTINGS:
• Map Cost - Entry fee deducted per map
• Opacity - Window transparency (0.1-1.0)
• Apply Tax - Calculate with 12.5% market fee

FILES CREATED:
• config.json - Your settings
• drop_log.txt - All drops with timestamps

LOG PATH INFO:
The tool searches for log at:
  Method 1: Game\\UE_game\\Torchlight\\Saved\\Logs\\UE_game.log
  Method 2: Game\\TorchLight\\Saved\\Logs\\UE_game.log (fallback)

Version: 4.0
Build Date: {build_date}
"""

with open(f"{portable_dir}/README.txt", "w", encoding="utf-8") as f:
    f.write(readme.format(build_date=datetime.now().strftime("%Y-%m-%d")))
print("  ✓ README.txt created")

# Create launcher
launcher = """@echo off
title FurTorch v5 Launcher
color 0A
echo ==========================================
echo   FurTorch v5.0 - Drop Tracker
echo ==========================================
echo.
echo Make sure Torchlight: Infinite is running!
echo.
echo Starting FurTorch...
start "" "FurTorch_v5.exe"
echo.
echo FurTorch started!
echo.
timeout /t 2 >nul
"""

with open(f"{portable_dir}/Start.bat", "w") as f:
    f.write(launcher)
print("  ✓ Start.bat created")

# Create debug launcher
debug_launcher = """@echo off
title FurTorch v5 - Debug Mode
color 0E
echo ==========================================
echo   FurTorch v5.0 - DEBUG MODE
echo ==========================================
echo.
echo This window shows debug messages.
echo Keep it open to see what's happening!
echo.
pause
FurTorch_v5.exe
echo.
echo FurTorch closed.
pause
"""

with open(f"{portable_dir}/Start_Debug.bat", "w") as f:
    f.write(debug_launcher)
print("  ✓ Start_Debug.bat created")

print("✓ Package complete\n")

# Step 6: Summary
print("[6/6] Build Summary")
print("-"*70)

total_size = sum(os.path.getsize(os.path.join(portable_dir, f)) 
                for f in os.listdir(portable_dir)) / 1024 / 1024

print(f"Location: {os.path.abspath(portable_dir)}")
print(f"Total size: {total_size:.1f} MB")
print()
print("Contents:")
print("  • FurTorch_v5.exe      - Main application")
print("  • full_table.json      - Item database")
print("  • id_table.json        - Item mappings")
print("  • README.txt           - User guide")
print("  • Start.bat            - Quick launcher")
print("  • Start_Debug.bat      - Debug mode launcher")
print()

print("="*70)
print("✓✓✓ BUILD SUCCESSFUL! ✓✓✓")
print("="*70)
print()
print("NEXT STEPS:")
print()
print("1. TEST IT:")
print("   • Start your game")
print("   • Run Start_Debug.bat to see console messages")
print("   • Check if it says 'Game detected!'")
print("   • Play and pick up items")
print()
print("2. IF IT WORKS:")
print("   • Use Start.bat for normal use")
print("   • Zip the folder to share with others")
print()
print("3. IF IT DOESN'T WORK:")
print("   • Run Start_Debug.bat")
print("   • Copy the console messages")
print("   • Share them for troubleshooting")
print()
print("="*70)

input("\nPress Enter to exit...")
