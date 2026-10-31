# 🔍 Circle to Search for Windows

A faithful, smooth, and high-performance **Circle to Search** experience for Windows 10 & 11, inspired by Android (Samsung Galaxy & Google Pixel).

![App Icon](assets/app_icon.png)

---

## ✨ Features

- 🌈 **Google Rainbow Glowing Lasso**: Draw freehand circles, scribbles, or lasso selections with vibrant multi-layer glowing strokes (Google Blue, Red, Yellow, Green, Cyan) and trailing stardust particles.
- 🔍 **Instant Google Lens Visual Search**: Automatically uploads the circled area directly to Google Lens and opens the comprehensive visual search results page in your default browser.
- ⚡ **Windows 10/11 Native Offline OCR**: Powered by the built-in Windows OCR engine (`winsdk.windows.media.ocr`). Instantly detects text from images, videos, and games with zero cloud delay (< 30ms) and 100% privacy.
- 📋 **One-Click Text Actions**:
  - **Copy Text**: Copies recognized text immediately to your clipboard.
  - **Search Text**: Searches the recognized query on Google Web Search.
  - **Translate**: Automatically opens Google Translate with the recognized text.
- 📱 **Floating Android Gesture Bar**: Optional subtle pill at the bottom center of the screen that expands with a Google glow on hover and triggers Circle to Search with a single click.
- 🔔 **Android-Style Floating HUD Pill**: Sleek frosted glassmorphism toast that displays search progress, extracted text snippets, and action buttons.
- 🔊 **Synthesized Audio Feedback**: Ethereal activation chime and crisp selection pop for satisfying tactile audio feedback.
- 🛡️ **System Tray & Hotkey Manager**: Runs quietly in your system tray with full customizable settings and startup with Windows.

---

## 🚀 Quick Start

### 1. Requirements
Ensure you have Python 3.10+ installed. The following packages are required:
```bash
pip install PyQt5 keyboard winsdk pillow requests
```

### 2. Launch
- **Double click `run.bat`** to start silently in the background.
- Or run in terminal:
  ```bash
  python main.py
  ```

### 3. Usage
- Press **`Alt + C`** anywhere on your PC (or click the floating gesture pill at the bottom edge of your screen).
- **Draw a circle, scribble, or lasso** around any image, video, document, or game on your screen.
- Upon releasing the mouse:
  - Google Lens opens instantly with visual results!
  - If text was selected, the floating pill offers 1-click **Copy Text** and **Translate**.
- Press **`Esc`** or right-click anytime to dismiss without searching.

---

## ⚙️ Settings & Customization

Click the System Tray icon and select **Settings** (or right-click the tray icon):
- **Global Hotkey**: Choose between `Alt + C`, `Ctrl + Alt + S`, `Ctrl + Space`, `Alt + Space`, or `Ctrl + Shift + S`.
- **Search Behavior**:
  - *Instant Google Lens*: Opens Google Lens immediately in your browser on circle release.
  - *Action Sheet Preview*: Shows full preview card with image thumbnail, editable OCR text, and action buttons before launching.
- **Auto-copy OCR text**: Automatically copies any detected text to your clipboard.
- **Sound Effects**: Toggle futuristic chimes on/off.
- **Floating Gesture Bar**: Toggle the bottom screen navigation pill.
- **Start with Windows**: Toggle automatic startup on Windows boot.

---

## 📁 Project Architecture

```
k:/circletosearch/
├── main.py              # Application controller, system tray icon, global hotkey hook
├── overlay.py           # Fullscreen translucent overlay, neon lasso, particles, screen grab
├── search_engine.py     # Google Lens v3 upload engine, web search & translate helpers
├── ocr_engine.py        # Windows 10/11 native offline OCR integration
├── hud.py               # Android-style floating toast pill & Action Sheet
├── floating_bar.py      # Bottom screen gesture navigation bar
├── sound.py             # Asynchronous audio chime feedback
├── config.py            # Settings persistence & Windows startup registry sync
├── settings_dialog.py   # Modern dark-mode settings UI
├── assets_gen.py        # Icon and audio chime asset generator
├── run.bat              # One-click Windows silent launcher
├── run_debug.bat        # Debug launcher with live terminal logs
└── assets/              # Icons (PNG, ICO) and WAV chimes
```

---

## 🔒 Privacy & Performance
- OCR is processed **100% locally** using your operating system's native Windows OCR API.
- Low memory footprint and zero CPU usage when idle in the system tray.
