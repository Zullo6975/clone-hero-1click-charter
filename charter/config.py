from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ChartConfig:
    # --- Basic ---
    mode: str = "real"  # "real" or "dummy"

    # --- Difficulty / Feel ---
    max_nps: float = 3.8
    min_gap_ms: int = 140
    seed: int = 42

    # --- New Custom Settings ---
    allow_orange: bool = True       # "No Orange" toggle
    chord_prob: float = 0.12        # 0.0 to 0.5 (Chord Density)
    sustain_len: float = 0.5        # 0.0 (Staccato) to 1.0 (Flowing)
    movement_bias: float = 0.5      # 0.0 (Static) to 1.0 (Active)
    grid_snap: str = "1/8"          # "1/4", "1/8", "1/16"
    force_taps: bool = False        # If True, avoids HOPO logic (force strum)

    # --- Structural ---
    add_sections: bool = True
    add_star_power: bool = True

# Constants moved from other files
TRACK_NAME = "PART GUITAR"
SP_PITCH = 116
LANE_PITCHES = {
    0: 60,  # Green
    1: 61,  # Red
    2: 62,  # Yellow
    3: 63,  # Blue
    4: 64,  # Orange
}
