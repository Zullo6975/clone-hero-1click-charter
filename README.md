# CH 1-Click Charter

CH 1-Click Charter is a Python-based tool that generates **playable Clone Hero lead guitar charts** from audio files with a single command or via a lightweight GUI.

This project is **fun-first**, targeting **Medium difficulty** charts that feel good to play and **never exceed the intensity of GH3 Medium** (e.g. _Cult of Personality_). Accuracy is secondary to playability, consistency, and musical flow.

## What it creates

Given an audio file, the tool generates a song output directory containing:

- `notes.mid` — Clone Hero–compatible MIDI
- `stats.json` — tuning/analysis output (tooling-only)
- `album.png` — optional album art (GUI only)

---

## Philosophy

> If a chart ever feels annoying, unreadable, or unfair — it failed.

This project prioritizes:

- Comfort over precision
- Flow over transcription accuracy
- Consistency over surprise

---

## Goals

- One-click generation of **Medium lead guitar** charts
- Predictable, readable patterns
- Mixed single notes, doubles, and sustains (within strict limits)
- Output that works immediately in Clone Hero
- Deterministic results (same input → same chart)

---

## Non-Goals

This project intentionally does **not** aim to:

- Generate Expert or Orange-heavy charts
- Perfectly transcribe real guitar parts
- Match a specific game engine (GH vs Rock Band)
- Replace human charting for competitive play

---

## Hard Constraints (Always Enforced)

- ❌ No chaotic hand travel
- ❌ No sudden difficulty spikes
- ❌ No sustained fast streams
- ❌ No unreadable patterns

Medium difficulty is a **hard ceiling**.

If constraints are violated, the chart **simplifies automatically**.

---

## How It Works (High Level)

1. Analyze audio for tempo, beats, and onsets
2. Select musically relevant note times
3. Quantize to a conservative beat grid
4. Assign lanes with movement bias
5. Apply difficulty governors
6. Export a Clone Hero–ready folder:
   - `song.mp3`
   - `song.ini`
   - `notes.mid`
   - `album.png` (optional)

---

## Requirements

- Python 3.10+
- Clone Hero (for testing output)

---

## Install

```bash
make install
```

---

## GUI (Recommended)

```bash
make gui
```

## CLI

```bash
make run AUDIO="samples/test.mp3" OUT="output/TestSong" TITLE="Test Song"
```

## Personal App

```bash
make build
make pipx-install
1clickcharter --help
1clickcharter-gui
```

The GUI supports:

- Audio selection
- Metadata entry
- Album art preview
- Difficulty tuning
- One-click chart generation

Always launch the GUI via `make gui` to ensure the correct Python environment.

---

## CLI Usage

### Dummy Chart

```bash
make run MODE=dummy
```

### Real Chart

```bash
make run MODE=real
```

---

## Current Status

✅ Playable Medium charts
✅ Full-song coverage
✅ Smart taps, sustains, and doubles
✅ GUI + CLI parity

This is a **stable v0.1 baseline**.

---

## License

MIT License
