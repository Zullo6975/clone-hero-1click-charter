#!/bin/bash

# Configuration
INPUT_FILE="images/icon_og.png"
ICONSET_NAME="images/icon.iconset"
OUTPUT_ICNS="images/icon.icns"
OUTPUT_ICO="images/icons.ico"
OUTPUT_LINUX="images/icon.png" #

# Check input
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: $INPUT_FILE not found."
    exit 1
fi

# Clean previous runs
rm -rf "$ICONSET_NAME"
mkdir -p "$ICONSET_NAME"

echo "🎨 Processing $INPUT_FILE..."

# ---------------------------------------------------------
# STRATEGY 1: PYTHON (Optimized)
# ---------------------------------------------------------
if python3 -c "import PIL" 2>/dev/null; then
    echo "⚡ Using Python (Pillow) for optimized resizing..."
    
    python3 - <<END
import os
from PIL import Image

input_file = "$INPUT_FILE"
output_dir = "$ICONSET_NAME"

# macOS Sizes
sizes = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png")
]

img = Image.open(input_file)

# 1. Generate macOS parts
for px, name in sizes:
    out_path = os.path.join(output_dir, name)
    resized = img.resize((px, px), Image.Resampling.LANCZOS)
    resized.save(out_path, format="PNG", optimize=True, compress_level=9)

# 2. Generate Windows .ico
ico_sizes = [(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)]
img.save("$OUTPUT_ICO", format='ICO', sizes=ico_sizes)

# 3. Generate Linux .png (512x512 is standard high-res for Linux Docks)
linux_img = img.resize((512, 512), Image.Resampling.LANCZOS)
linux_img.save("$OUTPUT_LINUX", format="PNG", optimize=True, compress_level=9)
END
    
    echo "🎉 Created Windows icon: $OUTPUT_ICO"
    echo "🎉 Created Linux icon:   $OUTPUT_LINUX"

# ---------------------------------------------------------
# STRATEGY 2: MACOS NATIVE (Fallback)
# ---------------------------------------------------------
else
    echo "⚠️  Python Pillow not found. Falling back to 'sips'."
    
    # Generate macOS sizes
    sips -z 16 16     "$INPUT_FILE" --out "${ICONSET_NAME}/icon_16x16.png" > /dev/null
    sips -z 32 32     "$INPUT_FILE" --out "${ICONSET_NAME}/icon_16x16@2x.png" > /dev/null
    sips -z 32 32     "$INPUT_FILE" --out "${ICONSET_NAME}/icon_32x32.png" > /dev/null
    sips -z 64 64     "$INPUT_FILE" --out "${ICONSET_NAME}/icon_32x32@2x.png" > /dev/null
    sips -z 128 128   "$INPUT_FILE" --out "${ICONSET_NAME}/icon_128x128.png" > /dev/null
    sips -z 256 256   "$INPUT_FILE" --out "${ICONSET_NAME}/icon_128x128@2x.png" > /dev/null
    sips -z 256 256   "$INPUT_FILE" --out "${ICONSET_NAME}/icon_256x256.png" > /dev/null
    sips -z 512 512   "$INPUT_FILE" --out "${ICONSET_NAME}/icon_256x256@2x.png" > /dev/null
    sips -z 512 512   "$INPUT_FILE" --out "${ICONSET_NAME}/icon_512x512.png" > /dev/null
    sips -z 1024 1024 "$INPUT_FILE" --out "${ICONSET_NAME}/icon_512x512@2x.png" > /dev/null

    # Generate Linux single file
    sips -z 512 512   "$INPUT_FILE" --out "$OUTPUT_LINUX" > /dev/null
    
    echo "🎉 Created Linux icon: $OUTPUT_LINUX"
    echo "ℹ️  Skipped Windows .ico (requires Python Pillow)."
fi

# ---------------------------------------------------------
# FINALIZE
# ---------------------------------------------------------

echo "📦 Packing macOS .icns..."
iconutil -c icns "$ICONSET_NAME" -o "$OUTPUT_ICNS"
rm -rf "$ICONSET_NAME"

echo "✅ Done! Generated: $OUTPUT_ICNS"