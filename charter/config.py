from __future__ import annotations
from dataclasses import dataclass

# Constants used across the app
TRACK_NAME = "PART GUITAR"
SP_PITCH = 116

# CLONE HERO PITCH MAPS (MIDI Note Numbers)
DIFFICULTY_PITCHES = {
    "Expert": {0: 96, 1: 97, 2: 98, 3: 99, 4: 100},
    "Hard":   {0: 84, 1: 85, 2: 86, 3: 87, 4: 88},
    "Medium": {0: 72, 1: 73, 2: 74, 3: 75, 4: 76},
    "Easy":   {0: 60, 1: 61, 2: 62, 3: 63, 4: 64}
}

# Default to Expert for the base generation
LANE_PITCHES = DIFFICULTY_PITCHES["Expert"]

# --- SUPPORT INFO (v2.0) ---
SUPPORT_EMAIL = "oneclickcharter-support@outlook.com"
VENMO_HANDLE = "oneclickcharter"
VENMO_URL = "https://venmo.com/u/oneclickcharter"
REPO_URL = "https://github.com/zullo6975/clone-hero-1click-charter"

@dataclass
class ChartConfig:
    # --- Basic ---
    mode: str = "real"  # "real" or "dummy"

    # --- Difficulty / Feel (TUNED FOR EXPERT) ---
    max_nps: float = 12.0       # Was 3.8 (Medium) -> 12.0 (Expert Shredding)
    min_gap_ms: int = 60        # Was 140ms -> 60ms (Allows fast runs/trills)
    seed: int = 42

    # --- Gameplay Customization ---
    allow_orange: bool = True       # Essential for Expert
    chord_prob: float = 0.22        # Was 0.12 -> 0.22 (More chords)
    sustain_len: float = 0.4        # Was 0.5 -> 0.4 (Slightly less hold, more tap)
    movement_bias: float = 0.6      # Was 0.5 -> 0.6 (More movement up/down neck)
    grid_snap: str = "1/16"         # Was 1/8 -> 1/16 (Finer resolution)
    force_taps: bool = False

    # --- Sustain Fine-Tuning ---
    sustain_threshold: float = 0.8
    sustain_buffer: float = 0.25

    # --- Structural ---
    rhythmic_glue: bool = True
    add_sections: bool = True
    add_star_power: bool = True
