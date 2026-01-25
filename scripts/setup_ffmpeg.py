import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path


def report_progress(block_num, block_size, total_size):
    if total_size > 0:
        percent = int(block_num * block_size * 100 / total_size)
        sys.stdout.write(f"\r... Downloading FFmpeg... {percent}%")
        sys.stdout.flush()


def setup_ffmpeg():
    root = Path(__file__).resolve().parents[1]
    bin_dir = root / "bin"
    bin_dir.mkdir(exist_ok=True)

    ffmpeg_exe = bin_dir / \
        ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    ffprobe_exe = bin_dir / \
        ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")

    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        print(f"[OK] FFmpeg found in {bin_dir}")
        return

    print(f"[INFO] FFmpeg not found. Downloading for {sys.platform}...")

    try:
        if sys.platform == "win32":
            # Windows: Download Essentials Zip
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            zip_path = bin_dir / "ffmpeg.zip"
            urllib.request.urlretrieve(url, zip_path, report_progress)
            print("\n[INFO] Extracting...")

            with zipfile.ZipFile(zip_path, 'r') as z:
                # Flatten: Find exe inside nested folders and copy to /bin
                for name in z.namelist():
                    if name.endswith("bin/ffmpeg.exe"):
                        with z.open(name) as source, open(ffmpeg_exe, "wb") as target:
                            shutil.copyfileobj(source, target)
                    elif name.endswith("bin/ffprobe.exe"):
                        with z.open(name) as source, open(ffprobe_exe, "wb") as target:
                            shutil.copyfileobj(source, target)

            zip_path.unlink()

        elif sys.platform == "darwin":
            # macOS: Download separate zips
            # 1. FFmpeg
            urllib.request.urlretrieve(
                "https://evermeet.cx/ffmpeg/getrelease/zip", bin_dir / "ffmpeg.zip", report_progress)
            print("\n[INFO] Extracting ffmpeg...")
            with zipfile.ZipFile(bin_dir / "ffmpeg.zip", 'r') as z:
                with z.open("ffmpeg") as src, open(ffmpeg_exe, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            (bin_dir / "ffmpeg.zip").unlink()

            # 2. FFprobe
            urllib.request.urlretrieve(
                "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip", bin_dir / "ffprobe.zip", report_progress)
            print("\n[INFO] Extracting ffprobe...")
            with zipfile.ZipFile(bin_dir / "ffprobe.zip", 'r') as z:
                with z.open("ffprobe") as src, open(ffprobe_exe, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            (bin_dir / "ffprobe.zip").unlink()

            # Executable permissions
            ffmpeg_exe.chmod(0o755)
            ffprobe_exe.chmod(0o755)

        else:
            print("\n[WARNING] Linux detected: Please install ffmpeg via your package manager (e.g., sudo apt install ffmpeg).")
            return

        print(f"\n[OK] FFmpeg setup complete: {bin_dir}")

    except Exception as e:
        print(f"\n[ERROR] Failed to setup FFmpeg: {e}")


if __name__ == "__main__":
    setup_ffmpeg()
