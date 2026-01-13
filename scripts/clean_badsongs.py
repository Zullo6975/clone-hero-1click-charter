#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def normalize_path(s: str) -> Path:
    s = s.strip()
    if not s:
        raise ValueError("empty")

    # Strip surrounding quotes
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    # Normalize macOS mount prefix case
    if s.startswith("/volumes/"):
        s = "/Volumes/" + s[len("/volumes/") :]

    return Path(s)


def iter_paths(file_path: Path) -> list[Path]:
    paths: list[Path] = []
    for raw in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue

        try:
            p = normalize_path(line)
        except ValueError:
            continue

        if str(p).startswith("/"):
            paths.append(p)

    # De-dupe preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        s = str(p)
        if s not in seen:
            seen.add(s)
            out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Delete filesystem paths listed one-per-line in a text file")
    ap.add_argument("list_file", type=Path, help="Text file with one absolute path per line")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted")
    ap.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    ap.add_argument("--files-too", action="store_true", help="Also delete files (default: directories only)")
    ap.add_argument("--ignore-missing", action="store_true", help="Do not fail if a path doesn't exist")

    args = ap.parse_args()

    if not args.list_file.exists():
        print(f"❌ File not found: {args.list_file}", file=sys.stderr)
        sys.exit(1)

    paths = iter_paths(args.list_file)

    if not paths:
        print("✅ No paths found in list file.")
        return

    existing: list[Path] = []
    skipped: list[tuple[Path, str]] = []

    for p in paths:
        if not p.exists():
            if not args.ignore_missing:
                skipped.append((p, "missing"))
            continue

        if p.is_dir():
            existing.append(p)
        elif p.is_file():
            if args.files_too:
                existing.append(p)
            else:
                skipped.append((p, "file (use --files-too)"))
        else:
            skipped.append((p, "not file/dir"))

    if not existing:
        print("✅ No deletable paths found.")
        if skipped:
            print("\nSkipped:")
            for p, reason in skipped[:50]:
                print(f"  {p}  [{reason}]")
            if len(skipped) > 50:
                print(f"  ... ({len(skipped) - 50} more)")
        return

    print("Will delete:")
    for p in existing:
        print(f"  {p}")

    if skipped:
        print("\nSkipped:")
        for p, reason in skipped[:50]:
            print(f"  {p}  [{reason}]")
        if len(skipped) > 50:
            print(f"  ... ({len(skipped) - 50} more)")

    if args.dry_run:
        print("\n🟡 Dry run enabled — nothing deleted.")
        return

    if not args.yes:
        confirm = input("\nType 'delete' to permanently remove these paths: ")
        if confirm.lower() != "delete":
            print("❌ Aborted.")
            return

    for p in existing:
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            print(f"🗑️  Deleted: {p}")
        except Exception as e:
            print(f"⚠️  Failed to delete {p}: {e}")

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
