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

LANE_PITCHES = DIFFICULTY_PITCHES["Expert"]

# --- SUPPORT INFO ---
SUPPORT_EMAIL = "oneclickcharter-support@outlook.com"
VENMO_HANDLE = "oneclickcharter"
VENMO_URL = "https://venmo.com/u/oneclickcharter"
REPO_URL = "https://github.com/zullo6975/clone-hero-1click-charter"

@dataclass
class ChartConfig:
    # --- Basic ---
    mode: str = "real"

    # --- EXPERT BASELINE ---
    max_nps: float = 12.0
    min_gap_ms: int = 60
    seed: int = 42

    # --- REDUCTION TUNING ---
    hard_min_gap_ms: int = 120
    medium_min_gap_ms: int = 220
    easy_min_gap_ms: int = 450

    # --- Gameplay Customization ---
    # CLEANUP: Locked these values to "Always On / High Quality"
    allow_orange: bool = True       # Always allow 5th lane logic to run
    rhythmic_glue: bool = True      # Always enforce patterns
    grid_snap: str = "1/16"         # Always use high-res grid

    chord_prob: float = 0.22
    sustain_len: float = 0.4
    movement_bias: float = 0.6
    force_taps: bool = False

    # --- Sustain Fine-Tuning ---
    sustain_threshold: float = 0.8
    sustain_buffer: float = 0.25

    # --- Structural ---
    add_sections: bool = True
    add_star_power: bool = True
