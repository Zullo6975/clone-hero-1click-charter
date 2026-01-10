from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import random
import json
import math

import pretty_midi # type: ignore
import librosa # type: ignore
import numpy as np # type: ignore
import mido # type: ignore

from charter.config import ChartConfig, LANE_PITCHES, TRACK_NAME, SP_PITCH
from charter.audio import detect_onsets, estimate_pitches
from charter.sections import generate_sections, compute_section_stats, Section
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

def _pitch_diff_semitones(p1: float | None, p2: float | None) -> float:
    if p1 is None or p2 is None or p1 <= 0 or p2 <= 0: return 0.0
    return 12 * math.log2(p2 / p1)

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
        base_w = 0.05 if lane == 4 else 1.0
        dist = abs(lane - prev_lane)
        if dist == 0: w = 2.0 * (1.0 - cfg.movement_bias)
        elif dist == 1: w = 2.0
        elif dist == 2: w = 1.3 + (cfg.movement_bias * 0.5)
        else: w = 0.3 + (cfg.movement_bias * 0.8)
        weights.append(max(0.01, w * base_w))

    semitone_diff = _pitch_diff_semitones(prev_pitch, curr_pitch)

    if abs(semitone_diff) > 0.5:
        for i, lane in enumerate(options):
            if semitone_diff > 0: # Up
                if lane > prev_lane: weights[i] *= 4.0
                elif lane < prev_lane: weights[i] *= 0.1
            elif semitone_diff < 0: # Down
                if lane < prev_lane: weights[i] *= 4.0
                elif lane > prev_lane: weights[i] *= 0.1
    else:
        for i, lane in enumerate(options):
            if abs(lane - prev_lane) >= 2:
                weights[i] *= 1.25

    total = sum(weights)
    weights = [w / total for w in weights]
    return rng.choices(options, weights=weights, k=1)[0]

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

def _rename_sections_based_on_density(sections: list, note_times: list[float], total_duration: float) -> list:
    if not note_times:
        return sections

    avg_nps = len(note_times) / total_duration if total_duration > 0 else 0.0
    solo_threshold = max(avg_nps * 1.15, 2.0)

    new_sections = []
    for i, s in enumerate(sections):
        start = s.start
        end = sections[i+1].start if i+1 < len(sections) else total_duration
        duration = end - start

        notes_in_section = sum(1 for t in note_times if start <= t < end)
        section_nps = notes_in_section / duration if duration > 0.5 else 0.0

        if (section_nps > solo_threshold
            and s.name not in ["Intro", "Outro"]
            and duration > 5.0):
            new_sections.append(asdict(s) | {"name": "Guitar Solo"})
        else:
            new_sections.append(asdict(s))

    return new_sections

def _compute_rolling_density(times: list[float], duration: float) -> list[dict]:
    """Calculates Notes Per Second (NPS) in 1-second windows, stepped every 0.5s."""
    points = []
    step = 0.5
    window = 1.0
    t = 0.0
    times_sorted = sorted(times)

    while t <= duration:
        # Count notes in [t, t + window]
        count = sum(1 for x in times_sorted if t <= x < t + window)
        points.append({"t": round(t, 2), "nps": count})
        t += step
    return points

def _fix_midi_sections(midi_path: Path):
    """
    Post-process the MIDI file to move [section ...] events to Track 0.
    Clone Hero REQUIRES section names to be Text events on the global tempo track.
    """
    try:
        mid = mido.MidiFile(str(midi_path))

        # Track 0 is usually the conductor track (tempo, time sig, global events)
        conductor_track = mid.tracks[0]

        # We will collect all section events found in ANY track
        sections_to_move = []

        for track in mid.tracks:
            # Rebuild track without the section events
            new_track_data = []
            current_time = 0

            for msg in track:
                current_time += msg.time # Track absolute time

                # Identify section markers (Lyrics or Text starting with [section)
                if msg.type in ('lyrics', 'text') and isinstance(msg.text, str) and msg.text.startswith('[section '):
                    # Store absolute time and text to move later
                    sections_to_move.append((current_time, msg.text))
                else:
                    new_track_data.append(msg)

            # Replace track content (stripping sections from original location)
            track[:] = new_track_data

        # Now add them to the conductor track
        if sections_to_move:
            # 1. Convert conductor track to absolute time
            abs_conductor = []
            curr = 0
            for msg in conductor_track:
                curr += msg.time
                abs_conductor.append((curr, msg))

            # 2. Add new section events
            for t, text in sections_to_move:
                # Create a proper Text event (meta type 0x01)
                new_msg = mido.MetaMessage('text', text=text)
                abs_conductor.append((t, new_msg))

            # 3. Sort by absolute time
            abs_conductor.sort(key=lambda x: x[0])

            # 4. Convert back to delta time
            new_conductor = []
            last_time = 0
            for t, msg in abs_conductor:
                delta = t - last_time
                # Mido messages are mutable, but safer to copy if modifying time
                msg = msg.copy(time=int(delta))
                new_conductor.append(msg)
                last_time = t

            mid.tracks[0][:] = new_conductor

        mid.save(str(midi_path))

    except Exception as e:
        print(f"Warning: Failed to fix section events: {e}")

def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    cfg: ChartConfig,
    stats_out_path: Path | None = None,
    override_sections: list[dict] | None = None,
    dry_run: bool = False,
) -> tuple[float, list[dict], list[dict]]:
    rng = random.Random(cfg.seed)

    # 1. Analyze
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

    shift_seconds = 0.0
    if times and times[0] < 3.0:
        shift_seconds = 3.0 - times[0]
    times = [t + shift_seconds for t in times]
    duration += shift_seconds

    # --- RHYTHMIC GLUE ---
    shifted_beat_times = [b + shift_seconds for b in beat_times]
    measure_notes = {}
    pattern_memory = {}

    if cfg.rhythmic_glue and len(shifted_beat_times) > 4:
        for i, t in enumerate(times):
            m_idx, m_offset = _quantize_to_measure(t, shifted_beat_times)
            measure_notes.setdefault(m_idx, []).append((m_offset, i))

    # 3. Note Generation (Skip if dry_run)
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))
    guitar = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    prev_lane = 2
    prev_pitch = None
    chord_starts = []

    if not dry_run:
        for i, t in enumerate(times):
            curr_pitch = pitches[i]
            lane = _assign_lane(prev_lane, curr_pitch, prev_pitch, rng, cfg)
            prev_lane = lane
            prev_pitch = curr_pitch

            is_sustain = False
            is_chord = False
            found_memory = False

            if cfg.rhythmic_glue and len(shifted_beat_times) > 4:
                m_idx, m_offset = _quantize_to_measure(t, shifted_beat_times)
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

                if cfg.rhythmic_glue and len(shifted_beat_times) > 4:
                    m_idx, m_offset = _quantize_to_measure(t, shifted_beat_times)
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

    # 4. Events & Smart Sections
    final_sections = []

    if override_sections:
        final_sections = override_sections
        if not dry_run:
            for s in final_sections:
                pm.lyrics.append(pretty_midi.Lyric(f"[section {s['name']}]", float(s['start'])))

    elif cfg.add_sections:
        raw_sections = generate_sections(str(audio_path), duration - shift_seconds)

        shifted_sections = []
        for s in raw_sections:
            shifted_start = s.start + shift_seconds
            shifted_sections.append(asdict(s) | {"start": shifted_start})

        raw_onset_times = [o.t + shift_seconds for o in onsets]
        obj_sections = [Section(s["name"], s["start"]) for s in shifted_sections]

        final_sections = _rename_sections_based_on_density(
            obj_sections,
            raw_onset_times,
            duration
        )

        if not dry_run:
            for s in final_sections:
                pm.lyrics.append(pretty_midi.Lyric(f"[section {s['name']}]", float(s['start'])))

    if not dry_run and cfg.add_star_power:
        phrases = generate_star_power_phrases(note_times=times, duration_sec=duration)
        for p in phrases:
            guitar.notes.append(pretty_midi.Note(100, SP_PITCH, p.start, p.end))

    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pm.write(str(out_path))

        # --- FIX: Move section events to Track 0 for Clone Hero ---
        _fix_midi_sections(out_path)

    # --- Compute Density ---
    density_data = _compute_rolling_density(times, duration)

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
        data = { "stats": [asdict(s) for s in stats] }
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
