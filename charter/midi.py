from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import random
import json

import pretty_midi # type: ignore
import librosa # type: ignore
import numpy as np # type: ignore

from charter.config import ChartConfig, LANE_PITCHES, TRACK_NAME, SP_PITCH
from charter.audio import detect_onsets
from charter.sections import generate_sections, compute_section_stats
from charter.star_power import generate_star_power_phrases

def _filter_onsets(candidates: list, duration: float, cfg: ChartConfig) -> list:
    """Selects onsets based on density settings."""
    window = 4.0
    min_gap = max(0.05, cfg.min_gap_ms / 1000.0)

    selected = []
    buckets = {}
    for c in candidates:
        idx = int(c.t // window)
        buckets.setdefault(idx, []).append(c)

    for w in sorted(buckets.keys()):
        items = sorted(buckets[w], key=lambda x: x.strength, reverse=True)
        quota = int(cfg.max_nps * window)

        count = 0
        for c in items:
            if count >= quota: break
            if any(abs(c.t - s.t) < min_gap for s in selected):
                continue
            selected.append(c)
            count += 1

    selected.sort(key=lambda x: x.t)
    return selected

def _assign_lane(prev_lane: int, rng: random.Random, cfg: ChartConfig) -> int:
    options = [0, 1, 2, 3]
    if cfg.allow_orange:
        options.append(4)

    weights = []
    for lane in options:
        # Orange is rare spice
        base_w = 0.05 if lane == 4 else 1.0
        dist = abs(lane - prev_lane)
        if dist == 0:
            w = 2.0 * (1.0 - cfg.movement_bias)
        elif dist == 1:
            w = 2.0
        elif dist == 2:
            w = 1.0 + (cfg.movement_bias * 0.5)
        else:
            w = 0.2 + (cfg.movement_bias * 0.8)
        weights.append(max(0.01, w * base_w))

    return rng.choices(options, weights=weights, k=1)[0]

def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    cfg: ChartConfig,
    stats_out_path: Path | None = None,
) -> float:
    """
    Generates the MIDI chart.
    Returns: shift_seconds (float) - amount the chart was shifted to create a lead-in.
    """
    rng = random.Random(cfg.seed)

    # 1. Analyze
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    onsets = detect_onsets(audio_path)

    # 2. Filter & Quantize
    notes = _filter_onsets(onsets, duration, cfg)
    times = [n.t for n in notes]

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)

    if len(beat_times) > 1:
        grid = []
        divs = {"1/4": 1, "1/8": 2, "1/16": 4}.get(cfg.grid_snap, 2)
        for i in range(len(beat_times)-1):
            s, e = beat_times[i], beat_times[i+1]
            span = e - s
            for d in range(divs):
                grid.append(s + (span * (d/divs)))
        grid = np.array(grid)

        snapped = []
        for t in times:
            idx = (np.abs(grid - t)).argmin()
            snapped.append(grid[idx])
        times = sorted(list(set(snapped)))

    # --- LEAD-IN LOGIC ---
    # If the song starts too fast (< 3.0s), shift everything to give 3s runway.
    shift_seconds = 0.0
    if times and times[0] < 3.0:
        shift_seconds = 3.0 - times[0]

    # Apply shift
    times = [t + shift_seconds for t in times]
    # We must also effectively "extend" the duration for section logic
    duration += shift_seconds

    # 3. Write Notes
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))
    guitar = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    prev_lane = 2
    chord_starts = []

    for i, t in enumerate(times):
        lane = _assign_lane(prev_lane, rng, cfg)
        prev_lane = lane

        # Sustain Logic
        next_t = times[i+1] if i+1 < len(times) else t + 2.0
        gap = next_t - t
        is_sustain = False
        if gap > 0.4 and rng.random() < cfg.sustain_len:
            is_sustain = True

        dur = min(gap - 0.05, 0.15)
        if is_sustain: dur = gap - 0.1

        # Chord Logic
        lanes = [lane]
        if rng.random() < cfg.chord_prob:
            opts = [l for l in [lane-1, lane+1] if 0 <= l <= 4]
            if not cfg.allow_orange: opts = [l for l in opts if l != 4]
            if opts:
                l2 = rng.choice(opts)
                lanes.append(l2)
                chord_starts.append(t)

        for l in lanes:
            guitar.notes.append(pretty_midi.Note(
                velocity=100, pitch=LANE_PITCHES[l], start=t, end=t+dur
            ))

    pm.instruments.append(guitar)

    # 4. Events
    final_sections = []
    if cfg.add_sections:
        # Generate raw sections (based on original audio time)
        # Then shift them to match the new grid
        raw_sections = generate_sections(str(audio_path), duration - shift_seconds)

        evt = pretty_midi.Instrument(0, name="EVENTS")
        for s in raw_sections:
            shifted_start = s.start + shift_seconds
            final_sections.append(asdict(s) | {"start": shifted_start}) # Store for stats
            pm.lyrics.append(pretty_midi.Lyric(f"[section {s.name}]", float(shifted_start)))
        pm.instruments.append(evt)

    if cfg.add_star_power:
        phrases = generate_star_power_phrases(note_times=times, duration_sec=duration)
        for p in phrases:
            guitar.notes.append(pretty_midi.Note(100, SP_PITCH, p.start, p.end))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))

    # 5. Stats
    if stats_out_path:
        # Re-wrap final_sections for stats consumption
        # (This is a bit hacky, but stats is internal only)
        from charter.sections import Section
        sec_objs = [Section(s["name"], s["start"]) for s in final_sections]

        stats = compute_section_stats(
            note_starts=times, chord_starts=chord_starts,
            sections=sec_objs, duration_sec=duration
        )
        data = { "stats": [asdict(s) for s in stats] }
        stats_out_path.write_text(json.dumps(data, indent=2))

    return shift_seconds

def write_dummy_notes_mid(out_path: Path, bpm: float, bars: int, density: float) -> float:
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(0, name=TRACK_NAME)
    total_beats = bars * 4
    for b in range(total_beats):
        t = b * (60.0 / bpm)
        pitch = LANE_PITCHES[b % 3]
        inst.notes.append(pretty_midi.Note(100, pitch, t, t + 0.2))
    pm.instruments.append(inst)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))
    return 0.0
