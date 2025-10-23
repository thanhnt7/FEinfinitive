# FurTorch v5 - Setup Guide

This guide explains how to set up FurTorch v5 on a new PC.

---

## 📦 Two Setup Options

### Option 1: End-User (Just Run the App)
### Option 2: Developer (Build from Source)

---

## 🎮 Option 1: End-User Setup

**For users who just want to run FurTorch without modifying code.**

### Requirements
- ✅ Windows OS (Windows 10/11 recommended)
- ✅ Torchlight: Infinite game installed

### Installation Steps

1. **Download the portable package:**
   - Get `FurTorch_v5_Portable.zip` from releases
   - Extract to any folder

2. **Verify folder contents:**
   ```
   FurTorch_v5_Portable/
   ├── FurTorch_v5.exe       ← Main application
   ├── full_table_en.json       ← Item database
   ├── README.txt            ← User guide
   ├── Start.bat             ← Quick launcher
   └── Start_Debug.bat       ← Debug mode
   ```

3. **Run the application:**
   - Double-click `Start.bat` for normal use
   - Or `Start_Debug.bat` to see debug messages

### ✅ No Python or dependencies required!

---

## 🔧 Option 2: Developer Setup

**For developers who want to modify code or build the executable.**

### Pre-Installation Requirements

#### 1. Install Python 3.7+
- Download: https://www.python.org/downloads/
- **⚠️ IMPORTANT:** Check "Add Python to PATH" during installation
- Recommended: Python 3.9 or 3.10

#### 2. Install Git (Optional)
- Download: https://git-scm.com/downloads
- Only needed if cloning from GitHub

### Project Setup

#### Step 1: Get the Code

**Option A - Clone with Git:**
```bash
git clone https://github.com/thanhnt7/FEinfinitive.git
cd FEinfinitive
```

**Option B - Download ZIP:**
1. Download ZIP from GitHub
2. Extract to your preferred folder
3. Open terminal in that folder

#### Step 2: Install Dependencies

**Automatic (recommended):**
```bash
pip install -r requirements.txt
```

**Manual:**
```bash
pip install pywin32>=305
pip install psutil>=5.9.0
pip install pyinstaller>=5.0
```

#### Step 3: Verify Files

Make sure you have:
- ✅ `furtorch_v5.py` - Main application code
- ✅ `full_table_en.json` - Item database
- ✅ `build_v5_complete.py` - Build script

#### Step 4: Build the Executable

```bash
python build_v5_complete.py
```

The build process will:
1. Check required files
2. Install dependencies (if missing)
3. Clean old builds
4. Build executable with PyInstaller (takes 3-5 minutes)
5. Create portable package in `FurTorch_v5_Portable/`

---

## 📚 Dependencies Explained

| Package | Version | Purpose |
|---------|---------|---------|
| `pywin32` | ≥305 | Windows API access (detect game process, find log files) |
| `psutil` | ≥5.9.0 | Process monitoring and system info |
| `pyinstaller` | ≥5.0 | Build standalone executable |
| `tkinter` | Built-in | GUI library (included with Python) |

---

## 🐛 Troubleshooting

### Python Installation Issues

**Problem: "python is not recognized as a command"**
- Solution: Reinstall Python and check "Add Python to PATH"
- Or manually add Python to system PATH

**Problem: tkinter not found**
- Windows: Reinstall Python with "tcl/tk and IDLE" option checked
- Linux: `sudo apt-get install python3-tk`

### Dependency Installation Issues

**Problem: pywin32 installation fails**
```bash
# Try these steps in order:
pip install --upgrade pip
pip install pywin32 --no-cache-dir
python -m pywin32_postinstall -install
```

**Problem: Permission denied during pip install**
```bash
# Use user installation:
pip install --user -r requirements.txt
```

### Build Issues

**Problem: "Missing files" error**
- Make sure `furtorch_v5.py` and `full_table_en.json` are in the same folder as `build_v5_complete.py`

**Problem: Build succeeds but exe doesn't work**
- Run `Start_Debug.bat` to see error messages
- Check if Windows Defender blocked the exe
- Verify the game is running before starting FurTorch

---

## 🚀 Quick Start Commands

```bash
# Clone repository
git clone https://github.com/thanhnt7/FEinfinitive.git
cd FEinfinitive

# Install dependencies
pip install -r requirements.txt

# Build executable
python build_v5_complete.py

# Test the app (run directly with Python)
python furtorch_v5.py
```

---

## 📁 Project Structure

```
FEinfinitive/
├── furtorch_v5.py           # Main application code
├── full_table_en.json          # Item database (prices, names, types)
├── build_v5_complete.py     # Build script for creating .exe
├── requirements.txt         # Python dependencies
├── SETUP.md                 # This file
└── README.txt               # User guide (created during build)
```

---

## 💡 Development Tips

### Run Without Building
```bash
# Test your changes quickly without building exe:
python furtorch_v5.py
```

### Update Item Database
- Edit `full_table_en.json` to update item prices
- Format: `{"item_id": {"name": "...", "type": "...", "price": 0.0}}`
- Rebuild after changes: `python build_v5_complete.py`

### Debugging
```bash
# Run with Python to see console output:
python furtorch_v5.py

# Or use the debug launcher after building:
Start_Debug.bat
```

---

## 🔄 Updating to a New PC

### Developer Migration
1. Copy the entire project folder
2. Install Python on new PC
3. Run: `pip install -r requirements.txt`
4. Done! You can now build and run

### End-User Migration
1. Copy the `FurTorch_v5_Portable` folder
2. Done! No installation needed

---

## 📞 Support

If you encounter issues:
1. Check this SETUP.md guide
2. Read `README.txt` (created after building)
3. Run with `Start_Debug.bat` to see error messages
4. Report issues on GitHub

---

## 🎯 What's Next?

After setup:
1. Read the user guide in `README.txt`
2. Start Torchlight: Infinite
3. Enable logging in game: Settings → Other → "开启日志"
4. **Restart the game** (important!)
5. Run FurTorch
6. Pick up items and see them tracked!

---

**Version:** v5.0
**Last Updated:** 2025-10-23
**Build Status:** Fixed (id_table.json removed)
