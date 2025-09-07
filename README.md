# AutoClickTool for Codex IDE Plugin and CLI

An intelligent auto-click tool built with Python and Tkinter that uses image recognition to automatically confirm file write operations in Codex IDE plugin and CLI environments.

## ✨ Features

- 🎯 **Smart Image Matching**: Uses OpenCV template matching algorithm for accurate image recognition
- 🪟 **Multi-Window Support**: Monitor multiple windows simultaneously for parallel automation
- 🔧 **Flexible Configuration**: Adjustable check intervals and matching thresholds
- 📝 **Real-time Logging**: Detailed operation logs and debugging information
- 💾 **Configuration Persistence**: Automatic saving and loading of configuration files
- 🎮 **User-Friendly Interface**: Intuitive GUI interface for easy operation
- 🔄 **Click Mode Selection**: Support for "Extension" (click only) and "CLI" (click + Enter) modes

## 🛠️ Technology Stack

- **GUI Framework**: Tkinter
- **Image Processing**: OpenCV, Pillow
- **Screen Capture**: MSS, PyAutoGUI, pywin32
- **Window Operations**: Windows API (win32gui)
- **Build Tool**: PyInstaller

## 📋 System Requirements

- **Operating System**: Windows only (depends on win32 API)
- **Python Version**: Python 3.13+
- **Dependencies**: See `pyproject.toml`

## 🚀 Installation Guide

### Method 1: Using UV Package Manager (Recommended)

```bash
# Clone the project
git clone <repository-url>
cd auto_apply

# Install dependencies with UV
uv sync

# Run the application
uv run python auto_click_gui.py
```

### Method 2: Using pip

```bash
# Clone the project
git clone <repository-url>
cd auto_apply

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python auto_click_gui.py
```

### Method 3: Using Pre-built Executable

If the project includes a built exe file, you can run it directly:

```bash
.\dist\AutoClickTool.exe
```

## 📖 Usage Guide

### 1. Launch the Application
Run `auto_click_gui.py` to start the GUI interface.

### 2. Add Template Images
- Click "Add Template" button to select target image files
- Supports PNG, JPG, JPEG, BMP, GIF formats
- Multi-select for batch template addition
- Automatically loads default templates (`image1.png`, `image2.png`)

### 3. Select Windows to Monitor
- Application automatically lists all visible windows
- Double-click window list items to add/remove monitoring
- Monitored windows show "✅ Monitoring" status

### 4. Configure Click Mode
- **Extension Mode**: Mouse click only
- **CLI Mode**: Click followed by Enter key press

### 5. Adjust Parameters
- **Check Interval**: Set scanning frequency (0.1-5 seconds)
- **Match Threshold**: Adjust image matching accuracy (0.1-1.0)

### 6. Start Monitoring
- Click "Start Monitoring" button to begin auto-clicking
- Application searches for template images in specified windows and clicks automatically
- View real-time logs for operation status

## 🎛️ Interface Layout

```
┌─────────────────┬─────────────────┐
│   Window List   │ Template Mgmt   │
│                 │                 │
│ [Refresh Btn]   │ [Template Btns] │
├─────────────────┼─────────────────┤
│                 │ Monitor Params  │
│                 │                 │
│                 │ Monitor Control │
├─────────────────┴─────────────────┤
│            Runtime Logs           │
│                                   │
└───────────────────────────────────┘
```

## ⚙️ Configuration File

The application uses `auto_click_config.json` to store configuration:

```json
{
  "check_interval": 1.0,
  "match_threshold": 0.8,
  "templates": [
    {
      "name": "image_yes1.png",
      "path": "C:/path/to/image_yes1.png",
      "size": "37x15"
    }
  ]
}
```

## 🏗️ Building Executable

Build exe file using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller AutoClickTool.spec

# Generated exe file is located in dist/ directory
```

## 📁 Project Structure

```
auto_apply/
├── auto_click_gui.py          # Main application file
├── auto_click_config.json     # Configuration file
├── AutoClickTool.spec         # PyInstaller configuration
├── pyproject.toml             # Project dependencies
├── uv.lock                    # UV lock file
├── image1.png                 # Default template image 1
├── image2.png                 # Default template image 2
├── image_yes.png             # Template image
├── image_yes1.png            # Template image
├── build/                     # Build temporary files
├── dist/                      # Build output directory
└── .venv/                     # Virtual environment
```

## 🔧 Core Functionality

### Image Matching Algorithm
- Uses OpenCV's `cv2.matchTemplate()` for template matching
- Employs `TM_CCOEFF_NORMED` normalized correlation coefficient matching
- Supports custom matching thresholds to balance accuracy and sensitivity

### Window Screenshot Technology
- Uses Windows PrintWindow API for window capture
- DPI-aware support for high-resolution displays
- Automatic handling of minimized window states

### Multi-threaded Monitoring
- Monitoring loop runs in separate thread, doesn't block GUI
- Uses queue mechanism for safe log message passing
- Supports real-time start/stop monitoring

## ⚠️ Important Notes

1. **Permission Requirements**: Application needs screen capture and mouse control permissions
2. **Target Windows**: Windows platform only for window operations
3. **Image Quality**: Template images should be clear and avoid compression artifacts
4. **Performance Considerations**: Reducing check intervals may increase CPU usage
5. **Window State**: Minimized target windows may affect screenshot effectiveness

## 🎯 Codex Integration

This tool is specifically designed for:
- **Codex IDE Plugin**: Automatically clicking confirmation dialogs when writing files
- **Codex CLI**: Confirming file operations in command-line interface
- **Windows Only**: Leverages Windows-specific APIs for reliable window interaction

The tool monitors for specific UI elements (buttons, dialogs) that appear during Codex file operations and automatically confirms them, streamlining the development workflow.

## 🐛 Common Issues

**Q: Application cannot recognize images?**
A: Check matching threshold settings, lower threshold for higher sensitivity; ensure template images are clear and complete.

**Q: Monitored window disappeared?**
A: Application automatically skips invalid windows. Re-add monitoring after reopening target application.

**Q: Click position inaccurate?**
A: Ensure target window is not scaled, adjust DPI settings; verify template image completeness.

## 🤝 Contributing

1. Fork the project
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

This project is licensed under MIT License - see LICENSE file for details.

## 📞 Contact

For questions or suggestions, please contact through:

- Create Issue
- Send Email
- Submit Pull Request

---

**⚡ Quick Start**: `uv run python auto_click_gui.py`