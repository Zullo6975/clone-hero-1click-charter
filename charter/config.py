from __future__ import annotations
from dataclasses import dataclass

# Constants used across the app
TRACK_NAME = "PART GUITAR"
SP_PITCH = 116

# CLONE HERO PITCH MAP
# Easy:   60-64
# Medium: 72-76
# Hard:   84-88
# Expert: 96-100
LANE_PITCHES = {
    0: 72,  # Green (Medium)
    1: 73,  # Red
    2: 74,  # Yellow
    3: 75,  # Blue
    4: 76,  # Orange
}

# --- SUPPORT INFO (v2.0) ---
SUPPORT_EMAIL = "oneclickcharter-support@outlook.com"
VENMO_HANDLE = "oneclickcharter"
VENMO_URL = "https://venmo.com/u/oneclickcharter"
REPO_URL = "https://github.com/zullo6975/clone-hero-1click-charter"

@dataclass
class ChartConfig:
    # --- Basic ---
    mode: str = "real"  # "real" or "dummy"

    # --- Difficulty / Feel ---
    max_nps: float = 3.8
    min_gap_ms: int = 140
    seed: int = 42

    # --- Gameplay Customization ---
    allow_orange: bool = True       # If False, limits to G/R/Y/B
    chord_prob: float = 0.12        # 0.0 (None) to 0.5 (Heavy)
    sustain_len: float = 0.5        # Probability (0.0 to 1.0)
    movement_bias: float = 0.5      # 0.0 (Static) to 1.0 (Active)
    grid_snap: str = "1/8"          # "1/4", "1/8", "1/16"
    force_taps: bool = False        # If True, avoids HOPO logic (force strum)

    # --- Sustain Fine-Tuning ---
    sustain_threshold: float = 0.8  # Min gap (seconds) required to trigger a sustain
    sustain_buffer: float = 0.25    # Gap (seconds) left at the end of a sustain

    # --- Structural ---
    rhythmic_glue: bool = True      # New v1.2: Enforce consistent patterns for repeated rhythms
    add_sections: bool = True
    add_star_power: bool = True
