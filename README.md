# SL:Arise Artifact Unified Crafter

An intelligent, fully automated, local OCR-based reroll bot for Solo Leveling: Arise. 
It automatically scans your screen using Tesseract OCR, strictly verifies the substats on your artifacts against 9 different best-in-slot preset profiles, and automatically rerolls until it finds a perfect 4/4 match!

## Features
- **Unified Master Script:** No need to manage 9 different folders. Just run the script and select your desired artifact from the main menu.
- **Flawless OCR Validation:** Uses advanced color-inversion image processing to slice through in-game particle animations and perfectly read white text on dark backgrounds.
- **Local & Safe:** Runs entirely locally on your CPU using Tesseract OCR. It does not hook into game memory, read network packets, or inject code. It purely reads your screen.
- **Fail-Safe Pausing:** Automatically takes a screenshot of the 4/4 match, saves it to the `screenshots/` folder, and instantly pauses itself so you never miss a god-roll.

## Prerequisites

You only need two things to run this script:

1. **Python 3.10+**: Download from [python.org](https://www.python.org/downloads/). 
   - ⚠️ **CRITICAL:** When installing Python, you MUST check the box that says `"Add python.exe to PATH"` at the very bottom of the installer window.
2. **Tesseract OCR**: Download the Windows installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). 
   - ⚠️ **CRITICAL:** Install it using the default settings so it installs to `C:\Program Files\Tesseract-OCR\tesseract.exe`.

## How to Run

1. **Double-click `Run.bat`**. 
   - The `.bat` file will automatically check if you have Python installed, quietly install all required background packages (`pyautogui`, `pytesseract`, `Pillow`, `pynput`), and launch the script for you.
2. **Select your Preset**: Type the number of the artifact you are rolling (e.g., `1` for Boots) and hit `Enter`.
3. **Calibrate (First Time Only)**:
   - Hover your mouse cursor over the **Top-Left** corner of the substats box and press `F1`.
   - Hover your mouse cursor over the **Bottom-Right** corner of the substats box and press `F1`.
   - Hover your mouse over the **Readjust Stats** button and press `F1`.
4. **Start**: Press `F2` to let the bot take over!

## Hotkeys

- `F1`: Calibrate the screen region (Only needed once, saves to `config.json`).
- `F2`: Start the auto-reroller.
- `F3`: Pause/Resume the bot manually.
- `F5`: Emergency stop / Exit the script completely.

## Troubleshooting

- **"Tesseract OCR is not installed or not found!"**
  - The script expects Tesseract to be at `C:\Program Files\Tesseract-OCR\tesseract.exe`. If you installed it somewhere else, simply open `auto_reroll_master.py` in a text editor and change the `TESSERACT_PATH` variable at the top.
- **The script is clicking but never matching anything.**
  - Make sure your game language is set to English.
  - Make sure nothing is physically blocking the text on your screen (like a Discord overlay).
  - Recalibrate using `F1` and ensure the box tightly surrounds the 4 substat text lines.

## Disclaimer
Use responsibly. This is an accessibility/automation macro based entirely on computer vision.
