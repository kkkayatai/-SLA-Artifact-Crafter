import pyautogui
import pytesseract
import time
import threading
import json
import os
import re
import sys
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from pynput import keyboard

# ── Tesseract Path ──
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ── Configuration ──
CLICK_DELAY = 2.0   # seconds between clicks
OCR_WAIT = 1.6   # seconds to wait after click before taking screenshot
DOUBLE_READ_DELAY = 0.3  # seconds between 1st and 2nd OCR read for confirmation
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
#  RULE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

def check_add_atk(line):
    return any(x in line for x in ["attack", "atta", "attk", "atack", "altack"]) and any(x in line for x in ["additional", "addit", "addl"])

def check_atk_pct(line):
    return any(x in line for x in ["attack", "atta", "attk", "atack", "altack"]) and not any(x in line for x in ["additional", "addit", "addl"])

def check_crit_rate(line):
    return any(x in line for x in ["critical", "critic", "crit", "crtl", "cril"]) and any(x in line for x in ["rate", "rat", "rte"]) and not any(x in line for x in ["damage", "dama", "dmg"])

def check_crit_dmg(line):
    return any(x in line for x in ["critical", "critic", "crit", "crtl", "cril", "itical"]) and any(x in line for x in ["damage", "dama", "dmg", "ce", "hj ce"]) and not any(x in line for x in ["reduction", "reduct"])

def check_def_pen(line):
    return any(x in line for x in ["penetrat", "pene", "pent", "pnrt"])

def check_dmg_inc(line):
    return any(x in line for x in ["damage", "dama", "dmg"]) and any(x in line for x in ["increase", "incr", "lncr", "ncre", "incyease", "inc"]) and not any(x in line for x in ["reduction", "reduct"])

def check_add_def(line):
    return any(x in line for x in ["defense", "defen", "defn", "dfns"]) and any(x in line for x in ["additional", "addit", "addl"])

ALL_RULES = {
    "Additional Attack": check_add_atk,
    "Attack (%)": check_atk_pct,
    "Critical Hit Rate": check_crit_rate,
    "Critical Hit Damage": check_crit_dmg,
    "Defense Penetration": check_def_pen,
    "Damage Increase": check_dmg_inc,
    "Additional Defense": check_add_def
}

def make_rule(name, is_mandatory):
    return {
        "display": name,
        "mandatory": is_mandatory,
        "check": ALL_RULES[name]
    }

# ══════════════════════════════════════════════════════════════════════
#  PRESETS
# ══════════════════════════════════════════════════════════════════════

PRESETS = {
    "1": {
        "name": "Boots",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Attack (%)", True),
            make_rule("Critical Hit Rate", True),
            make_rule("Critical Hit Damage", False),
            make_rule("Defense Penetration", False),
            make_rule("Damage Increase", False)
        ]
    },
    "2": {
        "name": "Bracelet",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Attack (%)", True),
            make_rule("Critical Hit Damage", False),
            make_rule("Defense Penetration", False),
            make_rule("Damage Increase", False)
        ]
    },
    "3": {
        "name": "Earrings",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Attack (%)", True),
            make_rule("Defense Penetration", True),
            make_rule("Critical Hit Damage", False),
            make_rule("Damage Increase", False)
        ]
    },
    "4": {
        "name": "Gloves",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Critical Hit Rate", True),
            make_rule("Defense Penetration", True),
            make_rule("Damage Increase", True)
        ]
    },
    "5": {
        "name": "Hunter - Helmet",
        "rules": [
            make_rule("Additional Defense", True),
            make_rule("Critical Hit Rate", True),
            make_rule("Defense Penetration", True),
            make_rule("Damage Increase", True)
        ]
    },
    "6": {
        "name": "Player - Body Armor",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Attack (%)", True),
            make_rule("Critical Hit Rate", True),
            make_rule("Defense Penetration", False),
            make_rule("Damage Increase", False)
        ]
    },
    "7": {
        "name": "Player - Helmet",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Critical Hit Rate", True),
            make_rule("Defense Penetration", True),
            make_rule("Damage Increase", True)
        ]
    },
    "8": {
        "name": "Ring",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Critical Hit Damage", True),
            make_rule("Defense Penetration", True),
            make_rule("Damage Increase", True)
        ]
    },
    "9": {
        "name": "Necklace",
        "rules": [
            make_rule("Additional Attack", True),
            make_rule("Attack (%)", True),
            make_rule("Critical Hit Damage", False),
            make_rule("Defense Penetration", False),
            make_rule("Damage Increase", False)
        ]
    }
}

# Globals to hold the selected rules
DESIRED_MATCH_RULES = []
MANDATORY_STATS = []


def clean_ocr_text(raw_text):
    text = raw_text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    lines = [re.sub(r'[^\S\n]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)


def split_into_stat_lines(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) >= 2:
        return lines
    
    single = text.strip()
    stat_patterns = [
        r'additional\s+attack\w*',
        r'additional\s+defense\w*',
        r'additional\s+hp\w*',
        r'additional\s+mp\w*',
        r'defense\s+penetrat\w*',
        r'damage\s+(?:increase|incr\w*)',
        r'damage\s+(?:reduction|reduct\w*)',
        r'mp\s+consumption\s+reduction\w*',
        r'mp\s+recovery\s+rate\s+increase\w*',
        r'critical\s+hit\s+damage\w*',
        r'attack\w*(?:\s*\(?%\)?)?',
        r'defense\w*(?:\s*\(?%\)?)?',
        r'hp\w*(?:\s*\(?%\)?)?',
        r'mp\b',
    ]
    combined = '|'.join(stat_patterns)
    matches = re.findall(combined, single)
    if matches:
        return [m.strip() for m in matches if m.strip()]
    
    return lines


def match_wanted_stats(text):
    lines = split_into_stat_lines(text)
    found = set()
    for line in lines:
        for rule in DESIRED_MATCH_RULES:
            if rule["check"](line):
                found.add(rule["display"])
    return list(found), lines


def check_substats(text):
    found, lines = match_wanted_stats(text)
    if len(found) < 4:
        return False, found, lines
    
    for mandatory in MANDATORY_STATS:
        if mandatory not in found:
            return False, found, lines
            
    return True, found, lines


def capture_and_ocr(region_tl, region_br):
    x = region_tl[0]
    y = region_tl[1]
    w = region_br[0] - region_tl[0]
    h = region_br[1] - region_tl[1]
    
    raw_screenshot = pyautogui.screenshot(region=(x, y, w, h))
    
    img = raw_screenshot.convert("L")
    img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
    img = ImageOps.invert(img)
    
    raw_text = pytesseract.image_to_string(img, config="--psm 6")
    cleaned_text = clean_ocr_text(raw_text)
    
    return raw_screenshot, cleaned_text, img


# ── State ──
calibration_step = 0
region_tl = None
region_br = None
click_pos = None
state = "IDLE"
roll_count = 0
lock = threading.Lock()
exit_event = threading.Event()
calibrated = False


def save_config():
    data = {
        "region_tl": list(region_tl),
        "region_br": list(region_br),
        "click_pos": list(click_pos),
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  💾 Config saved to {CONFIG_FILE}")


def load_config():
    global region_tl, region_br, click_pos, calibrated, state
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        region_tl = tuple(data["region_tl"])
        region_br = tuple(data["region_br"])
        click_pos = tuple(data["click_pos"])
        calibrated = True
        state = "CALIBRATED"
        print(f"  ✓ Loaded saved calibration:")
        print(f"    Stat area: ({region_tl[0]},{region_tl[1]}) → ({region_br[0]},{region_br[1]})")
        print(f"    Button:    ({click_pos[0]},{click_pos[1]})")
        print(f"  Press F2 to start, or F1 to recalibrate\n")
        return True
    return False


def on_press(key):
    global region_tl, region_br, click_pos, state, roll_count
    global calibration_step, calibrated

    try:
        if key == keyboard.Key.f1:
            with lock:
                pos = pyautogui.position()

                if calibration_step == 0:
                    region_tl = (pos.x, pos.y)
                    calibration_step = 1
                    print(f"\n  ✓ Step 1/3: Top-left of stat area saved ({pos.x}, {pos.y})")
                    print("  → Now hover over BOTTOM-RIGHT corner of the stat names area, press F1\n")

                elif calibration_step == 1:
                    region_br = (pos.x, pos.y)
                    calibration_step = 2
                    print(f"  ✓ Step 2/3: Bottom-right of stat area saved ({pos.x}, {pos.y})")
                    print("  → Now hover over the 'Readjust Stats' button, press F1\n")

                elif calibration_step == 2:
                    click_pos = (pos.x, pos.y)
                    calibration_step = 0
                    calibrated = True
                    state = "CALIBRATED"
                    save_config()
                    print(f"  ✓ Step 3/3: Button position saved ({pos.x}, {pos.y})")
                    print(f"\n  ✅ Calibration complete!")
                    print(f"    Stat area: ({region_tl[0]},{region_tl[1]}) → ({region_br[0]},{region_br[1]})")
                    print(f"    Button:    ({click_pos[0]},{click_pos[1]})")
                    
                    print("\n  --- RUNNING CALIBRATION TEST ---")
                    try:
                        x = region_tl[0]
                        y = region_tl[1]
                        w = region_br[0] - region_tl[0]
                        h = region_br[1] - region_tl[1]
                        
                        raw, txt, processed = capture_and_ocr(region_tl, region_br)
                        raw.save(os.path.join(SCREENSHOT_DIR, "debug_raw.png"))
                        processed.save(os.path.join(SCREENSHOT_DIR, "debug_processed.png"))
                        
                        match_1, found_1, lines_1 = check_substats(txt)
                        print(f"  OCR raw lines: {lines_1}")
                        print(f"  Found wanted stats: {found_1}")
                        print(f"  Match 4/4?: {match_1}")
                        print(f"  Saved debug screenshots to: {SCREENSHOT_DIR}")
                        print("  --------------------------------")
                    except Exception as e:
                        print(f"  Test failed: {e}")
                    
                    print(f"\n  Press F2 to START auto-reroll.")

        elif key == keyboard.Key.f2:
            with lock:
                if not calibrated:
                    print("  ⚠️ You must calibrate first using F1!")
                    return
                if state == "RUNNING":
                    print("  ⚠️ Already running.")
                else:
                    state = "RUNNING"
                    print("  ▶️ Started auto-reroll.")

        elif key == keyboard.Key.f3:
            with lock:
                if state == "RUNNING":
                    state = "PAUSED"
                    print("  ⏸ Paused auto-reroll.")
                elif state == "PAUSED":
                    state = "RUNNING"
                    print("  ▶️ Resumed auto-reroll.")

        elif key == keyboard.Key.f5:
            print("  🛑 Stopping and returning to menu...")
            exit_event.set()
            return False

    except Exception as e:
        print(f"  Error handling keypress: {e}")


def show_menu_and_setup():
    global DESIRED_MATCH_RULES, MANDATORY_STATS
    
    print("\n" + "=" * 50)
    print("      SL:ARISE ARTIFACT UNIFIED CRAFTER")
    print("=" * 50)
    print("Select the artifact preset you want to roll for:")
    for k in sorted(PRESETS.keys(), key=int):
        print(f"  [{k}] {PRESETS[k]['name']}")
    print("  [0] Quit")
    print("=" * 50)
    
    while True:
        try:
            choice = input("Enter number (0-9): ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return "0"
            
        if choice == "0":
            return choice
        if choice in PRESETS:
            preset = PRESETS[choice]
            print(f"\n✅ Selected Preset: {preset['name']}")
            DESIRED_MATCH_RULES.clear()
            DESIRED_MATCH_RULES.extend(preset["rules"])
            MANDATORY_STATS.clear()
            MANDATORY_STATS.extend([r["display"] for r in DESIRED_MATCH_RULES if r["mandatory"]])
            return choice
        else:
            print("❌ Invalid choice. Please enter a number from 0 to 9.")


def main():
    global roll_count, state
    
    # 0. Check Tesseract
    if not os.path.exists(TESSERACT_PATH):
        print("\n❌ CRITICAL ERROR: Tesseract OCR is not installed or not found!")
        print(f"   Expected to find it at: {TESSERACT_PATH}")
        print("\n   Please download and install Tesseract OCR from:")
        print("   https://github.com/UB-Mannheim/tesseract/wiki")
        print("\n   Make sure to install it for 'All Users' so it goes to C:\\Program Files\\")
        print("   Press Enter to exit...")
        input()
        sys.exit(1)

    while True:
        # 1. Interactive Menu
        choice = show_menu_and_setup()
        if choice == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)

        print("\n  ╔═══════════════════════════════════════════════╗")
        print("  ║    SL:Arise Artifact Auto-Reroll (SMART)      ║")
        print("  ╠═══════════════════════════════════════════════╣")
        print("  ║  F1  Calibrate (3 steps)                     ║")
        print("  ║  F2  Start auto-rerolling                    ║")
        print("  ║  F3  Pause / Resume                          ║")
        print("  ║  F5  Return to Menu                          ║")
        print("  ╠═══════════════════════════════════════════════╣")
        print(f"  ║  Delay: {CLICK_DELAY}s | OCR wait: {OCR_WAIT}s               ║")
        print("  ╚═══════════════════════════════════════════════╝")
        print()
        print(f"  Target substats (need 4/4):")
        for rule in DESIRED_MATCH_RULES:
            tag = " [MUST]" if rule["mandatory"] else ""
            print(f"    • {rule['display']}{tag}")
        print()

        if not load_config():
            print("  No saved calibration found.")
            print("  Hover over the TOP-LEFT corner of the stat names area and press F1\n")

        # Reset states for the new session
        exit_event.clear()
        if not calibrated:
            state = "IDLE"
        else:
            state = "CALIBRATED"

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        try:
            while not exit_event.is_set():
                if state == "RUNNING" and calibrated:
                    pyautogui.click(click_pos[0], click_pos[1])
                    roll_count += 1
                    time.sleep(OCR_WAIT)

                    try:
                        raw_screenshot, cleaned_text_1, _ = capture_and_ocr(region_tl, region_br)
                        match_1, found_1, lines_1 = check_substats(cleaned_text_1)

                        if match_1:
                            match_filename = f"MATCH_4of4_Roll_{roll_count}.png"
                            match_filepath = os.path.join(SCREENSHOT_DIR, match_filename)
                            raw_screenshot.save(match_filepath)
                            
                            with lock:
                                state = "PAUSED"
                            
                            print(f"\n  {'='*50}")
                            print(f"  🎉 Roll #{roll_count} — PERFECT 4/4 MATCH! 🎉")
                            print(f"  {'='*50}")
                            print(f"  Found: {', '.join(sorted(found_1))}")
                            print(f"  Screenshot: {os.path.join('screenshots', match_filename)}")
                            print(f"  ⏸ Auto-paused. Go check your screen!")
                            print(f"  Press F2 to resume, F5 to return to menu.\n")
                        else:
                            if len(found_1) >= 2:
                                print(f"  Roll #{roll_count} | {len(found_1)}/4: {', '.join(sorted(found_1))}")
                                print(f"    OCR: {' | '.join(lines_1)}")
                            elif len(found_1) > 0:
                                print(f"  Roll #{roll_count} | {len(found_1)}/4: {', '.join(sorted(found_1))}")
                            else:
                                print(f"  Roll #{roll_count} | 0/4")

                    except Exception as e:
                        print(f"  Roll #{roll_count} | OCR error: {e}")

                    remaining = max(0, CLICK_DELAY - OCR_WAIT)
                    for _ in range(int(remaining * 20)):
                        if state != "RUNNING" or exit_event.is_set():
                            break
                        time.sleep(0.05)
                else:
                    time.sleep(0.05)
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()


if __name__ == "__main__":
    main()
