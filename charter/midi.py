from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import random
import json
import math

import pretty_midi # type: ignore
import librosa # type: ignore
import numpy as np # type: ignore

from charter.config import ChartConfig, LANE_PITCHES, TRACK_NAME, SP_PITCH
from charter.audio import detect_onsets, estimate_pitches
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
    """
    Identifies 'Guitar Solo' sections by finding areas with high note density (NPS).
    Uses raw audio onsets (note_times) to find the 'true' busy-ness of the song.
    """
    if not note_times:
        return sections

    # 1. Calculate Song Average NPS
    avg_nps = len(note_times) / total_duration if total_duration > 0 else 0.0
    
    # Tuned Thresholds (v1.1.4): Aggressive Sensitivity
    # 1.15x average density (was 1.4x)
    # Minimum floor 2.0 NPS (was 3.0)
    solo_threshold = max(avg_nps * 1.15, 2.0) 

    print(f"DEBUG: Audio Avg NPS: {avg_nps:.2f} | Solo Threshold: {solo_threshold:.2f}")

    new_sections = []
    
    for i, s in enumerate(sections):
        start = s.start
        end = sections[i+1].start if i+1 < len(sections) else total_duration
        duration = end - start
        
        # Count raw audio events in this section
        notes_in_section = sum(1 for t in note_times if start <= t < end)
        section_nps = notes_in_section / duration if duration > 0.5 else 0.0
        
        print(f"DEBUG: Section '{s.name}' ({start:.1f}s): {section_nps:.2f} NPS")
        
        # If this section spikes above threshold, rename it
        if (section_nps > solo_threshold 
            and s.name not in ["Intro", "Outro"] 
            and duration > 5.0):
            print(f"DEBUG: -> Renaming '{s.name}' to 'Guitar Solo' (Spike Detected!)")
            new_sections.append(asdict(s) | {"name": "Guitar Solo"})
        else:
            new_sections.append(asdict(s))
            
    return new_sections

def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    cfg: ChartConfig,
    stats_out_path: Path | None = None,
) -> float:
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

    # 3. Note Generation
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(tempo))
    guitar = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    prev_lane = 2
    prev_pitch = None
    chord_starts = []

    for i, t in enumerate(times):
        curr_pitch = pitches[i]
        lane = _assign_lane(prev_lane, curr_pitch, prev_pitch, rng, cfg)
        prev_lane = lane
        prev_pitch = curr_pitch

        # Texture Decisions (Glue)
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
    if cfg.add_sections:
        raw_sections = generate_sections(str(audio_path), duration - shift_seconds)
        
        shifted_sections = []
        for s in raw_sections:
            shifted_start = s.start + shift_seconds
            shifted_sections.append(asdict(s) | {"start": shifted_start})
            
        # RAW ONSETS FOR DENSITY CHECK
        raw_onset_times = [o.t + shift_seconds for o in onsets]
        
        from charter.sections import Section
        obj_sections = [Section(s["name"], s["start"]) for s in shifted_sections]
        
        final_sections = _rename_sections_based_on_density(
            obj_sections, 
            raw_onset_times, 
            duration
        )

        evt = pretty_midi.Instrument(0, name="EVENTS")
        for s in final_sections:
            pm.lyrics.append(pretty_midi.Lyric(f"[section {s['name']}]", float(s['start'])))
        pm.instruments.append(evt)

    if cfg.add_star_power:
        phrases = generate_star_power_phrases(note_times=times, duration_sec=duration)
        for p in phrases:
            guitar.notes.append(pretty_midi.Note(100, SP_PITCH, p.start, p.end))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))

    if stats_out_path:
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