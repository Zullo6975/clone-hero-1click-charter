import sys
from pathlib import Path
from PIL import Image


def main():
    # Detect repo root relative to this script (repo/scripts/make_icons.py)
    root = Path(__file__).resolve().parents[1]

    # Source and Destination Paths
    src = root / "assets" / "icons" / "icon_og.png"
    icon_dir = root / "assets" / "icons"

    if not src.exists():
        print(f"[ERROR] Source icon not found at {src}")
        sys.exit(1)

    print(f"Processing icons from: {src.name}")

    try:
        img = Image.open(src)
    except Exception as e:
        print(f"[ERROR] Error opening source image: {e}")
        sys.exit(1)

    # 1. Generate ICO (Windows)
    # Standard sizes for Windows icons
    ico_dest = icon_dir / "AppIcon.ico"
    try:
        img.save(ico_dest, format="ICO", sizes=[
                 (256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"[OK] Created: {ico_dest.name}")
    except Exception as e:
        print(f"[WARNING] Failed to create ICO: {e}")

    # 2. Generate ICNS (macOS)
    # Pillow supports writing ICNS. Best results when source is 512x512 or 1024x1024.
    icns_dest = icon_dir / "AppIcon.icns"
    try:
        img.save(icns_dest, format="ICNS")
        print(f"[OK] Created: {icns_dest.name}")
    except Exception as e:
        print(f"[WARNING] Failed to create ICNS: {e}")


if __name__ == "__main__":
    main()
