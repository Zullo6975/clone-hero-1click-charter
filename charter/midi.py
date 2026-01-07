from __future__ import annotations

from pathlib import Path
import json
import random

import pretty_midi  # type: ignore
import librosa  # type: ignore
import numpy as np  # type: ignore

from charter.audio import detect_onsets, OnsetCandidate
from charter.sections import generate_sections, compute_section_stats
from charter.star_power import generate_star_power_phrases, SP_PITCH

# Keep this EXACTLY as your known-good baseline for now
TRACK_NAME = "PART GUITAR"

LANE_PITCH = {
    0: 60,  # Green
    1: 61,  # Red
    2: 62,  # Yellow
    3: 63,  # Blue
    4: 64,  # Orange (rare)
}


def _filter_onsets_windowed(
    candidates: list[OnsetCandidate],
    *,
    duration_sec: float,
    window_sec: float,
    min_gap_ms: int,
    max_nps: float,
    min_notes_per_window: int,
) -> list[OnsetCandidate]:
    if window_sec <= 0:
        window_sec = 4.0

    min_gap = max(0.03, min_gap_ms / 1000.0)
    quota = max(1, int(round(max_nps * window_sec)))
    min_notes_per_window = max(0, int(min_notes_per_window))

    buckets: dict[int, list[OnsetCandidate]] = {}
    for c in candidates:
        idx = int(c.t // window_sec)
        buckets.setdefault(idx, []).append(c)

    selected: list[OnsetCandidate] = []

    def too_close(t: float) -> bool:
        return any(abs(s.t - t) < min_gap for s in selected)

    num_windows = int(duration_sec // window_sec) + 1

    for w in range(num_windows):
        items = buckets.get(w, [])
        items_sorted = sorted(items, key=lambda x: x.strength, reverse=True)

        picked_this_window: list[OnsetCandidate] = []
        for c in items_sorted:
            if len(picked_this_window) >= quota:
                break
            if too_close(c.t):
                continue
            picked_this_window.append(c)
            selected.append(c)

        if len(picked_this_window) < min_notes_per_window:
            mid = (w * window_sec) + (window_sec * 0.5)
            if mid >= 1.0 and mid <= duration_sec - 0.5 and not too_close(mid):
                filler = OnsetCandidate(t=float(mid), strength=0.0)
                selected.append(filler)

    selected.sort(key=lambda c: c.t)
    return selected


def _assign_lanes(times: list[float], *, seed: int = 42) -> list[int]:
    rng = random.Random(seed)
    out: list[int] = []

    last_lane = 1
    repeat_run = 0

    for _ in times:
        candidates = [0, 1, 2, 3]
        weights = []

        for lane in candidates:
            move = abs(lane - last_lane)
            if move == 0:
                w = 2.6
            elif move == 1:
                w = 2.2
            elif move == 2:
                w = 1.0
            else:
                w = 0.55

            if lane == 3:
                w *= 0.65

            if lane == last_lane and repeat_run >= 2:
                w *= 0.2
            elif lane == last_lane and repeat_run == 1:
                w *= 0.55

            if len(out) >= 2 and out[-1] == out[-2] == lane:
                w *= 0.15

            weights.append(w)

        lane = rng.choices(candidates, weights=weights, k=1)[0]

        if lane == last_lane:
            repeat_run += 1
        else:
            repeat_run = 0

        out.append(lane)
        last_lane = lane

    return out


def _quantize_times_to_grid(
    audio_path: Path,
    times: list[float],
    *,
    subdivision: str = "1/8",
) -> list[float]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    _tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    if len(beat_times) < 2:
        return times

    mult = {"1/4": 1, "1/8": 2, "1/16": 4}.get(subdivision, 2)

    grid: list[float] = []
    for i in range(len(beat_times) - 1):
        a, b = beat_times[i], beat_times[i + 1]
        step = (b - a) / mult
        for k in range(mult):
            grid.append(float(a + k * step))
    grid.append(float(beat_times[-1]))

    grid_np = np.array(grid)
    return [float(grid_np[np.argmin(np.abs(grid_np - t))]) for t in times]


def _get_beat_times(audio_path: Path) -> list[float]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    _tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return [float(t) for t in beat_times]


def _is_strong_beat(t: float, beat_times: list[float], *, tol: float = 0.07) -> bool:
    if len(beat_times) < 2:
        return False

    idx = min(range(len(beat_times)), key=lambda i: abs(beat_times[i] - t))
    if abs(beat_times[idx] - t) > tol:
        return False

    return (idx % 4) == 0


def _choose_double(main_lane: int, *, rng: random.Random, allow_orange: bool, gap_to_next: float) -> list[int]:
    if allow_orange and main_lane == 3 and gap_to_next >= 0.30 and rng.random() < 0.18:
        return [3, 4]  # B + O

    adjacent = {
        0: [(0, 1), (0, 2)],
        1: [(0, 1), (1, 2), (1, 3)],
        2: [(1, 2), (2, 3), (0, 2)],
        3: [(2, 3), (1, 3)],
    }.get(main_lane, [(1, 2)])

    a, b = rng.choice(adjacent)
    return [a, b]


def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    min_gap_ms: int = 140,
    max_nps: float = 3.0,
    seed: int = 42,
    tap_duration: float = 0.10,
    bpm: float = 120.0,
    # NEW: CH-full features
    add_sections: bool = True,
    add_star_power: bool = True,
    stats_out_path: Path | None = None,
) -> None:
    """
    Real chart:
      audio -> onsets -> windowed filtering -> quantize -> lanes -> notes.mid

    Adds:
      - GH-ish star power phrases
      - MIDI section markers (EVENTS track)
      - stats.json export for tuning (our tool, not Clone Hero)
    """
    rng = random.Random(seed)

    candidates = detect_onsets(audio_path)
    duration_sec = float(librosa.get_duration(path=str(audio_path)))
    beat_times = _get_beat_times(audio_path)

    kept = _filter_onsets_windowed(
        candidates,
        duration_sec=duration_sec,
        window_sec=4.0,
        min_gap_ms=min_gap_ms,
        max_nps=max_nps,
        min_notes_per_window=1,
    )

    times = [c.t for c in kept]
    times = _quantize_times_to_grid(audio_path, times, subdivision="1/8")
    times = sorted(times)

    # de-dupe after quantization
    min_gap = max(0.03, min_gap_ms / 1000.0)
    deduped: list[float] = []
    for t in times:
        if not deduped or t - deduped[-1] >= min_gap:
            deduped.append(t)
    times = deduped

    lanes = _assign_lanes(times, seed=seed)

    # ---- knobs (kept as constants for now) ----
    allow_orange = True
    base_double_prob = 0.10
    sustain_min_gap = 0.45
    sustain_max_len = 1.20
    # ------------------------------------------

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)

    # 1) Guitar track
    inst = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    # We'll track chord starts separately for stats
    chord_starts: list[float] = []
    note_starts: list[float] = []

    for i, (t, lane) in enumerate(zip(times, lanes)):
        start = max(1.0, float(t))
        next_start = float(times[i + 1]) if i + 1 < len(times) else (start + 1.0)
        gap = max(0.0, next_start - start)

        strong = _is_strong_beat(start, beat_times)

        # sustain vs tap
        do_sustain = False
        if gap >= sustain_min_gap:
            p = 0.55 if strong else 0.25
            do_sustain = rng.random() < p

        if do_sustain:
            end = min(start + sustain_max_len, next_start - 0.03)
            end = max(end, start + 0.18)
        else:
            end = min(start + tap_duration, max(start + 0.05, next_start - 0.03))

        # single vs double
        double_prob = base_double_prob * (1.8 if strong else 1.0)
        if gap < 0.22:
            double_prob *= 0.25

        lanes_to_write = [int(lane)]
        if rng.random() < double_prob:
            lanes_to_write = _choose_double(int(lane), rng=rng, allow_orange=allow_orange, gap_to_next=gap)

        if len(lanes_to_write) >= 2:
            chord_starts.append(start)
        note_starts.append(start)

        for ln in lanes_to_write:
            inst.notes.append(
                pretty_midi.Note(
                    velocity=100,
                    pitch=LANE_PITCH[int(ln)],
                    start=start,
                    end=end,
                )
            )

    pm.instruments.append(inst)

    # 2) EVENTS track (sections)
    sections = []
    if add_sections:
        sections = generate_sections(duration_sec=duration_sec, approx_section_len_sec=25.0, start_at=1.0)
        events_inst = pretty_midi.Instrument(program=0, name="EVENTS")
        for s in sections:
            # pretty_midi supports lyrics/text via .lyrics
            # Clone Hero reads [section ...] style markers from text/lyrics events.
            pm.lyrics.append(pretty_midi.Lyric(text=f"[section {s.name}]", time=float(s.start)))
        pm.instruments.append(events_inst)

    # 3) Star Power phrases
    if add_star_power and note_starts:
        phrases = generate_star_power_phrases(
            note_times=note_starts,
            duration_sec=duration_sec,
            every_sec=22.0,
            phrase_len_sec=9.0,
            start_at=12.0,
        )
        for p in phrases:
            inst.notes.append(
                pretty_midi.Note(
                    velocity=100,
                    pitch=SP_PITCH,
                    start=float(p.start),
                    end=float(p.end),
                )
            )

    # 4) Stats export (our tool)
    if stats_out_path is not None:
        stats = compute_section_stats(
            note_starts=note_starts,
            chord_starts=chord_starts,
            sections=sections,
            duration_sec=duration_sec,
        )
        payload = {
            "duration_sec": duration_sec,
            "total_notes": len(note_starts),
            "total_chords": len(chord_starts),
            "sections": [
                {
                    "name": s.name,
                    "start": s.start,
                    "end": s.end,
                    "notes": s.notes,
                    "chords": s.chords,
                    "avg_nps": round(s.avg_nps, 3),
                    "max_nps_1s": round(s.max_nps_1s, 3),
                }
                for s in stats
            ],
        }
        stats_out_path.parent.mkdir(parents=True, exist_ok=True)
        stats_out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))


def write_dummy_notes_mid(
    out_path: Path,
    bpm: float = 115.0,
    bars: int = 24,
    density: float = 0.58,
) -> None:
    density = max(0.05, min(1.0, float(density)))
    rng = random.Random(42)

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    spb = 60.0 / bpm
    total_beats = bars * 4

    t = 1.0
    last_lane = 1

    for _beat in range(total_beats):
        eighth_prob = 0.25 + 0.45 * density
        slots = 2 if rng.random() < eighth_prob else 1

        for _s in range(slots):
            place_prob = density * (0.70 if slots == 2 else 0.90)
            if rng.random() >= place_prob:
                t += spb / slots
                continue

            candidates = [0, 1, 2, 3]
            weights = []
            for lane in candidates:
                move = abs(lane - last_lane)
                if move == 0:
                    w = 3.0
                elif move == 1:
                    w = 2.2
                elif move == 2:
                    w = 1.0
                else:
                    w = 0.5
                if lane == 3:
                    w *= 0.6
                weights.append(w)

            lane = rng.choices(candidates, weights=weights, k=1)[0]
            last_lane = lane

            lanes = [lane]
            if density < 0.72 and rng.random() < (0.06 + 0.06 * density):
                chord_options = [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3)]
                cand = [c for c in chord_options if lane in c] or chord_options
                a, b = rng.choice(cand)
                lanes = [a, b]

            dur = 0.18 if slots == 2 else 0.22
            for ln in lanes:
                inst.notes.append(
                    pretty_midi.Note(
                        velocity=100,
                        pitch=LANE_PITCH[ln],
                        start=t,
                        end=t + dur,
                    )
                )

            t += spb / slots

    pm.instruments.append(inst)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))
