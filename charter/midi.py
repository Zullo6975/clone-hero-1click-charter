from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import random
import json
import math

import pretty_midi  # type: ignore
import librosa  # type: ignore
import numpy as np  # type: ignore
import mido  # type: ignore

from charter.config import ChartConfig, LANE_PITCHES, TRACK_NAME, SP_PITCH
from charter.audio import detect_onsets, estimate_pitches
# FIX: 'generate_sections' replaced with 'find_sections'
from charter.sections import find_sections, compute_section_stats, Section
from charter.star_power import generate_star_power_phrases
from charter.reduction import reduce_to_hard, reduce_to_medium, reduce_to_easy

# -------------------------------------------------------------------------
# 1. ANALYSIS HELPERS
# -------------------------------------------------------------------------


def _filter_onsets(candidates: list, duration: float, cfg: ChartConfig) -> list:
    """Selects onsets based on density settings."""
    window = 4.0
    # FIXED: Lowered floor from 0.05 (50ms) to 0.02 (20ms) to allow bursts up to 50 NPS
    min_gap = max(0.02, cfg.min_gap_ms / 1000.0)

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
            if count >= quota:
                break
            if any(abs(c.t - s.t) < min_gap for s in selected):
                continue
            selected.append(c)
            count += 1

    selected.sort(key=lambda x: x.t)
    return selected


def _pitch_diff_semitones(p1: float | None, p2: float | None) -> float:
    if p1 is None or p2 is None or p1 <= 0 or p2 <= 0:
        return 0.0
    return 12 * math.log2(p2 / p1)


def _quantize_to_measure(time: float, beat_times: list[float]) -> tuple[int, float]:
    """Returns (measure_index, offset_from_measure_start)"""
    if not beat_times:
        return 0, 0.0

    idx = (np.abs(np.array(beat_times) - time)).argmin()
    measure_idx = idx // 4
    measure_start_beat_idx = measure_idx * 4

    if measure_start_beat_idx >= len(beat_times):
        return measure_idx, 0.0

    measure_start_time = beat_times[measure_start_beat_idx]
    beat_dur = beat_times[1] - beat_times[0] if len(beat_times) > 1 else 0.5
    offset_beats = (time - measure_start_time) / beat_dur
    quantized_offset = round(offset_beats * 4) / 4

    return measure_idx, quantized_offset


def _compute_rolling_density(times: list[float], duration: float) -> list[dict]:
    points = []
    step = 0.5
    window = 1.0
    t = 0.0
    times_sorted = sorted(times)

    while t <= duration:
        count = sum(1 for x in times_sorted if t <= x < t + window)
        points.append({"t": round(t, 2), "nps": count})
        t += step
    return points

# -------------------------------------------------------------------------
# 2. NOTE GENERATION LOGIC
# -------------------------------------------------------------------------


def _assign_lane(
    prev_lane: int,
    curr_pitch: float | None,
    prev_pitch: float | None,
    rng: random.Random,
    cfg: ChartConfig
) -> int:
    options = [0, 1, 2, 3]
    if cfg.allow_orange:
        options.append(4)

    weights = []
    for lane in options:
        # FIXED: Increased Orange weight from 0.05 to 0.20 for more Expert feel
        base_w = 0.20 if lane == 4 else 1.0

        dist = abs(lane - prev_lane)
        if dist == 0:
            w = 2.0 * (1.0 - cfg.movement_bias)
        elif dist == 1:
            w = 2.0
        elif dist == 2:
            w = 1.3 + (cfg.movement_bias * 0.5)
        else:
            w = 0.3 + (cfg.movement_bias * 0.8)
        weights.append(max(0.01, w * base_w))

    semitone_diff = _pitch_diff_semitones(prev_pitch, curr_pitch)

    if abs(semitone_diff) > 0.5:
        for i, lane in enumerate(options):
            if semitone_diff > 0:  # Up
                if lane > prev_lane:
                    weights[i] *= 4.0
                elif lane < prev_lane:
                    weights[i] *= 0.1
            elif semitone_diff < 0:  # Down
                if lane < prev_lane:
                    weights[i] *= 4.0
                elif lane > prev_lane:
                    weights[i] *= 0.1
    else:
        for i, lane in enumerate(options):
            if abs(lane - prev_lane) >= 2:
                weights[i] *= 1.25

    total = sum(weights)
    weights = [w / total for w in weights]
    return rng.choices(options, weights=weights, k=1)[0]


def generate_expert_notes(
    times: list[float],
    pitches: list[float],
    beat_times: list[float],
    cfg: ChartConfig
) -> tuple[list[pretty_midi.Note], list[float]]:
    """
    Generates the baseline 'Expert' chart notes in memory.
    Returns (list_of_notes, list_of_chord_start_times)
    """
    rng = random.Random(cfg.seed)
    generated_notes = []
    chord_starts = []

    # Rhythmic Glue Prep
    measure_notes = {}
    pattern_memory = {}

    if cfg.rhythmic_glue and len(beat_times) > 4:
        for i, t in enumerate(times):
            m_idx, m_offset = _quantize_to_measure(t, beat_times)
            measure_notes.setdefault(m_idx, []).append((m_offset, i))

    prev_lane = 2
    prev_pitch = None

    for i, t in enumerate(times):
        curr_pitch = pitches[i]
        lane = _assign_lane(prev_lane, curr_pitch, prev_pitch, rng, cfg)
        prev_lane = lane
        prev_pitch = curr_pitch

        is_sustain = False
        is_chord = False
        found_memory = False

        # Rhythmic Glue Logic
        if cfg.rhythmic_glue and len(beat_times) > 4:
            m_idx, m_offset = _quantize_to_measure(t, beat_times)
            sig = ""
            if m_idx in measure_notes:
                offsets = sorted([x[0] for x in measure_notes[m_idx]])
                sig = ",".join([f"{x:.2f}" for x in offsets])

            if sig and sig in pattern_memory:
                saved_decisions = pattern_memory[sig]
                for saved_offset, decision in saved_decisions.items():
                    if abs(saved_offset - m_offset) < 0.05:
                        is_sustain, is_chord = decision
                        found_memory = True
                        break

        if not found_memory:
            next_t = times[i+1] if i+1 < len(times) else t + 2.0
            gap = next_t - t

            if gap > cfg.sustain_threshold and rng.random() < cfg.sustain_len:
                is_sustain = True
            if rng.random() < cfg.chord_prob:
                is_chord = True

            if cfg.rhythmic_glue and len(beat_times) > 4:
                m_idx, m_offset = _quantize_to_measure(t, beat_times)
                if m_idx in measure_notes:
                    offsets = sorted([x[0] for x in measure_notes[m_idx]])
                    sig = ",".join([f"{x:.2f}" for x in offsets])
                    if sig not in pattern_memory:
                        pattern_memory[sig] = {}
                    pattern_memory[sig][m_offset] = (is_sustain, is_chord)

        dur = 0.1
        if is_sustain:
            next_t = times[i+1] if i+1 < len(times) else t + 2.0
            gap = next_t - t
            dur = gap - cfg.sustain_buffer
            dur = min(dur, 2.5)
            dur = max(dur, 0.2)

        lanes = [lane]
        if is_chord:
            opts = [l for l in [lane-1, lane+1] if 0 <= l <= 4]
            if not cfg.allow_orange:
                opts = [l for l in opts if l != 4]
            if opts:
                l2 = rng.choice(opts)
                lanes.append(l2)
                chord_starts.append(t)

        for l in lanes:
            # Use current LANE_PITCHES (will be Expert)
            midi_pitch = LANE_PITCHES[l]
            generated_notes.append(pretty_midi.Note(
                velocity=100, pitch=midi_pitch, start=t, end=t+dur
            ))

    return generated_notes, chord_starts

# -------------------------------------------------------------------------
# 3. SECTION & FILE IO
# -------------------------------------------------------------------------


def _rename_sections_based_on_density(
    sections: list,
    note_times: list[float],
    note_pitches: list[float],
    total_duration: float
) -> list:
    """
    Intelligently renames sections to 'Guitar Solo' if they meet:
    1. High Density (NPS) relative to song average.
    2. High Pitch Variance (Standard Deviation) - Solos move around, strumming doesn't.
    """
    if not note_times:
        return sections

    # Filter out 0.0 pitches (failed detection) for statistics
    valid_pitches = [p for p in note_pitches if p > 0]
    if not valid_pitches:
        return sections

    avg_nps = len(note_times) / total_duration if total_duration > 0 else 0.0

    # 1. Density Threshold: Only consider sections much faster than average
    solo_nps_threshold = max(avg_nps * 1.3, 3.0)

    new_sections = []

    # Pre-zip times and pitches for easier slicing
    notes_zipped = list(zip(note_times, note_pitches))

    for i, s in enumerate(sections):
        start = float(s.start)
        end = float(sections[i+1].start) if i + \
            1 < len(sections) else total_duration
        duration = end - start

        # Gather notes in this section
        sec_notes = [p for t, p in notes_zipped if start <= t < end and p > 0]
        count = len(sec_notes)

        section_nps = count / duration if duration > 0.5 else 0.0

        # 2. Pitch Variance: Calculate Standard Deviation
        # Solos move up/down the neck. Breakdowns/Strumming stay on 1-2 notes (low std dev).
        pitch_std = np.std(sec_notes) if count > 1 else 0.0

        is_solo = False
        is_bridge = (s.name == "Bridge")

        # Criteria:
        # - Must be fast (High NPS) OR be a Bridge with Moderate NPS
        # - Must move around (High Std Dev)

        # Standard Detection
        if (section_nps > solo_nps_threshold
            and pitch_std > 3.5
            and duration > 10.0
                and s.name not in ["Intro", "Outro"]):
            is_solo = True

        # Bridge Rescue: Bridges are often melodic solos
        # Lower thresholds if it's already identified structurally as a Bridge
        if is_bridge:
            # Just slightly above average is fine for a bridge solo
            relaxed_nps = max(avg_nps * 1.15, 2.5)
            # Allow more melodic playing (lower variance)
            if section_nps > relaxed_nps and pitch_std > 2.5 and duration > 8.0:
                is_solo = True

        if is_solo:
            new_sections.append(asdict(s) | {"name": "Guitar Solo"})
        else:
            new_sections.append(asdict(s))

    return new_sections


def _inject_sections_mido(midi_path: Path, sections: list, pm: pretty_midi.PrettyMIDI):
    """
    Directly injects section Text events into a dedicated 'EVENTS' track.
    Format: [section Name] (Text Event)
    """
    try:
        mid = mido.MidiFile(str(midi_path))

        # Create a fresh track for Events
        events_track = mido.MidiTrack()

        # Name it "EVENTS" (Crucial for Clone Hero)
        events_track.append(mido.MetaMessage(
            'track_name', name='EVENTS', time=0))

        abs_events = []
        for s in sections:
            name = s['name'] if isinstance(s, dict) else s.name
            start_sec = float(s['start'] if isinstance(s, dict) else s.start)

            # Convert seconds -> ticks
            start_ticks = pm.time_to_tick(start_sec)

            # Create Text event WITH brackets: [section Name]
            text_msg = mido.MetaMessage(
                'text', text=f"[section {name}]", time=0)
            abs_events.append((int(start_ticks), text_msg))

        abs_events.sort(key=lambda x: x[0])

        last_ticks = 0
        for t, msg in abs_events:
            delta = t - last_ticks
            msg = msg.copy(time=int(delta))
            events_track.append(msg)
            last_ticks = t

        # Insert the EVENTS track after the Tempo track (Index 1)
        mid.tracks.insert(1, events_track)

        mid.save(str(midi_path))

    except Exception as e:
        print(f"Warning: Failed to inject sections: {e}")

# -------------------------------------------------------------------------
# 4. MAIN PIPELINE
# -------------------------------------------------------------------------


def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    cfg: ChartConfig,
    stats_out_path: Path | None = None,
    override_sections: list[dict] | None = None,
    dry_run: bool = False,
) -> tuple[float, list[dict], list[dict] | dict]:
    """
    Main Orchestrator.
    1. Analyzes Audio
    2. Generates 'Expert' Notes
    3. Cascades Reduction (Exp -> Hard -> Med -> Easy)
    4. Writes Unified MIDI
    """

    # --- STEP 1: ANALYZE ---
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    onsets = detect_onsets(audio_path)
    notes = _filter_onsets(onsets, duration, cfg)

    raw_times = [n.t for n in notes]
    pitches = estimate_pitches(audio_path, raw_times)
    pitch_map = {t: p for t, p in zip(raw_times, pitches)}

    times = [n.t for n in notes]
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)

    # Grid Snapping
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

        combined = []
        for t, original_t in zip(snapped, times):
            combined.append((t, pitch_map.get(original_t)))
        combined.sort(key=lambda x: x[0])

        final_times = []
        final_pitches = []
        seen_times = set()
        for t, p in combined:
            if t not in seen_times:
                final_times.append(t)
                final_pitches.append(p)
                seen_times.add(t)
        times = final_times
        pitches = final_pitches

    # Shift for start delay
    shift_seconds = 0.0
    if times and times[0] < 3.0:
        shift_seconds = 3.0 - times[0]

    # Keep track of original duration before shifting
    original_duration = duration

    times = [t + shift_seconds for t in times]
    duration += shift_seconds
    shifted_beat_times = [b + shift_seconds for b in beat_times]

    # --- STEP 2: GENERATE EXPERT NOTES ---
    # NOTE: We now generate notes even in dry_run mode to calculate density stats for all diffs
    expert_notes, chord_starts = generate_expert_notes(
        times, pitches, shifted_beat_times, cfg
    )

    hard_notes = []
    medium_notes = []
    easy_notes = []

    if expert_notes:
        hard_notes = reduce_to_hard(
            expert_notes, min_gap_ms=cfg.hard_min_gap_ms)
        medium_notes = reduce_to_medium(
            hard_notes, min_gap_ms=cfg.medium_min_gap_ms)
        easy_notes = reduce_to_easy(
            medium_notes, min_gap_ms=cfg.easy_min_gap_ms)

    # --- STEP 3: SECTIONS ---
    final_sections = []
    if override_sections:
        final_sections = override_sections
    elif cfg.add_sections:
        # FIX: Calculate density profile from unshifted times to match original audio analysis
        # unshifted_times = raw_times from onsets (approximately)
        # But we must be careful: 'times' has been snapped and filtered.
        # Recover unshifted times from current 'times':
        unshifted_note_times = [t - shift_seconds for t in times]

        # Calculate density profile for find_sections
        d_profile = _compute_rolling_density(
            unshifted_note_times, original_duration)
        nps_values = [p['nps'] for p in d_profile]

        # Call the new find_sections
        raw_sections = find_sections(nps_values, original_duration)

        shifted_sections = []
        for s in raw_sections:
            shifted_start = s.start + shift_seconds
            shifted_sections.append(asdict(s) | {"start": shifted_start})

        obj_sections = [Section(s["name"], s["start"])
                        for s in shifted_sections]

        # Use actual charted notes (times & pitches) for better solo detection
        final_sections = _rename_sections_based_on_density(
            obj_sections,
            times,    # Charted note times (already shifted)
            pitches,  # Charted note pitches
            duration  # Total duration (shifted)
        )

    # --- STEP 4: WRITE MIDI (UNIFIED) ---
    if not dry_run:
        pm = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))
        guitar = pretty_midi.Instrument(program=0, name=TRACK_NAME)

        guitar.notes.extend(expert_notes)
        guitar.notes.extend(hard_notes)
        guitar.notes.extend(medium_notes)
        guitar.notes.extend(easy_notes)

        # Add Star Power
        if cfg.add_star_power:
            phrases = generate_star_power_phrases(
                note_times=times, duration_sec=duration)
            for p in phrases:
                guitar.notes.append(pretty_midi.Note(
                    100, SP_PITCH, p.start, p.end))

        # Add Solo Markers (Note 103)
        if final_sections:
            for i, sec in enumerate(final_sections):
                s_name = sec["name"] if isinstance(sec, dict) else sec.name
                if s_name == "Guitar Solo":
                    s_start = float(sec["start"] if isinstance(
                        sec, dict) else sec.start)
                    # Determine end time based on next section
                    if i + 1 < len(final_sections):
                        next_s = final_sections[i+1]
                        s_end = float(next_s["start"] if isinstance(
                            next_s, dict) else next_s.start)
                    else:
                        s_end = duration

                    # 103 is the standard Solo Marker pitch in Clone Hero
                    guitar.notes.append(
                        pretty_midi.Note(100, 103, s_start, s_end))

        pm.instruments.append(guitar)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pm.write(str(out_path))

        # Inject Sections
        if final_sections:
            _inject_sections_mido(out_path, final_sections, pm)

    # --- STEP 5: STATS ---
    # Calculate density for ALL difficulties for the Review Graph
    expert_times = times
    hard_times = [n.start for n in hard_notes]
    med_times = [n.start for n in medium_notes]
    easy_times = [n.start for n in easy_notes]

    density_data = {
        "Expert": _compute_rolling_density(expert_times, duration),
        "Hard": _compute_rolling_density(hard_times, duration),
        "Medium": _compute_rolling_density(med_times, duration),
        "Easy": _compute_rolling_density(easy_times, duration)
    }

    if stats_out_path and final_sections:
        sec_objs = []
        for s in final_sections:
            if isinstance(s, dict):
                sec_objs.append(Section(s["name"], s["start"]))
            else:
                sec_objs.append(s)

        stats = compute_section_stats(
            note_starts=times, chord_starts=chord_starts,
            sections=sec_objs, duration_sec=duration
        )
        data = {"stats": [asdict(s) for s in stats]}
        stats_out_path.write_text(json.dumps(data, indent=2))

    return shift_seconds, final_sections, density_data


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
