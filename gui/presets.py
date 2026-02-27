from __future__ import annotations
import json
from pathlib import Path

# "Standard" is now much harder to serve as a proper Expert baseline.
DEFAULT_PRESETS: dict[str, dict[str, float | int]] = {
    "1) Casual": {
        "max_nps": 9.0, "min_gap_ms": 75, "sustain": 40, "chord": 15,
        "hard_gap": 150, "med_gap": 350, "easy_gap": 600
    },
    "2) Standard": {
        "max_nps": 13.0, "min_gap_ms": 55, "sustain": 25, "chord": 22,
        "hard_gap": 120, "med_gap": 220, "easy_gap": 450
    },
    "3) Shred": {
        "max_nps": 17.0, "min_gap_ms": 35, "sustain": 10, "chord": 30,
        "hard_gap": 90, "med_gap": 180, "easy_gap": 350
    },
    "4) Lose Fingerprints": {
        "max_nps": 22.0, "min_gap_ms": 25, "sustain": 5,  "chord": 40,
        "hard_gap": 60, "med_gap": 120, "easy_gap": 250
    },
}

def get_user_preset_path() -> Path:
    p = Path.home() / ".1clickcharter" / "presets.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def load_all_presets() -> dict[str, dict[str, float | int]]:
    # Start with defaults
    merged = DEFAULT_PRESETS.copy()

    user_path = get_user_preset_path()
    if user_path.exists():
        try:
            user_data = json.loads(user_path.read_text(encoding="utf-8"))
            # Filter out any user presets that try to overwrite defaults
            clean_user_data = {k: v for k, v in user_data.items() if k not in DEFAULT_PRESETS}
            merged.update(clean_user_data)
        except Exception:
            pass # Ignore corrupted file

    return merged

def save_user_preset(name: str, data: dict[str, float | int]) -> None:
    user_path = get_user_preset_path()
    current = {}
    if user_path.exists():
        try:
            current = json.loads(user_path.read_text(encoding="utf-8"))
        except Exception:
            current = {}

    current[name] = data
    user_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

def delete_user_preset(name: str) -> None:
    user_path = get_user_preset_path()
    if not user_path.exists():
        return

    try:
        current = json.loads(user_path.read_text(encoding="utf-8"))
        if name in current:
            del current[name]
            user_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    except Exception:
        pass
