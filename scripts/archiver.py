import shutil
import re
from pathlib import Path

def get_current_version(root_path: Path) -> str:
    """Reads the version string from pyproject.toml."""
    toml_path = root_path / "pyproject.toml"
    if not toml_path.exists():
        raise FileNotFoundError("pyproject.toml not found!")

    content = toml_path.read_text(encoding="utf-8")
    # robust regex to find version = "X.Y.Z"
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Could not find version string in pyproject.toml")

def archive_current_version():
    # If this script is in /scripts/, parent[1] is still the repo root.
    root = Path(__file__).resolve().parents[1]

    try:
        version = get_current_version(root)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    legacy_dir_name = f"legacy_v{version}"
    legacy_dir = root / legacy_dir_name

    if legacy_dir.exists():
        print(f"⚠️  Archive already exists: {legacy_dir_name}")
        return

    print(f"📦 Archiving version {version} to '{legacy_dir_name}'...")
    legacy_dir.mkdir()

    # 1. Folders to copy (Updated for new structure)
    # 'icons' -> 'assets'
    # 'tools' -> 'scripts'
    # Added 'docs'
    dirs_to_copy = ["charter", "gui", "scripts", "bin", "assets", "docs"]

    for folder in dirs_to_copy:
        src = root / folder
        dest = legacy_dir / folder
        if src.exists():
            shutil.copytree(src, dest)
            print(f"   + Copied {folder}/")

    # 2. Files to copy (Root Configs)
    # Most MD files are now in /docs, so we just grab the root essentials
    extensions = ["*.py", "*.toml", "Makefile", "LICENSE", "README.md", "MANIFEST.in", "requirements.txt"]

    for ext in extensions:
        for file_path in root.glob(ext):
            # Don't copy directories matching the glob (unlikely but safe)
            if file_path.is_file():
                shutil.copy(file_path, legacy_dir / file_path.name)
                print(f"   + Copied {file_path.name}")

    print(f"\n✅ Successfully created archive: {legacy_dir}")

if __name__ == "__main__":
    archive_current_version()
