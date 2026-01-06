# CH 1-Click Charter

CH 1-Click Charter is a Python-based tool that generates **playable Clone Hero lead guitar charts** from audio files with a single command.

This project is **fun-first**, targeting **Medium difficulty** charts that feel good to play and **never exceed the intensity of GH3 Medium (e.g. Cult of Personality)**.

Accuracy is intentionally secondary to **playability, consistency, and musical flow**.

---

## Goals

- One-click generation of **Medium lead guitar** charts
- Charts that are fun, readable, and predictable
- Musical flow over mechanical precision
- Mixed single notes, doubles, and sustains (within safe limits)
- Output that works immediately in Clone Hero

---

## Non-Goals

This project intentionally does **not** aim to:

- Generate Expert or competitive charts
- Perfectly transcribe real guitar parts
- Emulate a specific game’s charting style
- Replace human charting for leaderboard play
- Expose dozens of tuning knobs

---

## Hard Constraints (Always Enforced)

- ❌ No sustained fast streams
- ❌ No chaotic hand travel
- ❌ No sudden speed or difficulty spikes

### Difficulty Envelope

- Medium difficulty only
- Burst speed capped
- Chords allowed but governed
- Sustains added only when musically justified

If constraints are violated, the chart **simplifies automatically**.

---

## How It Works (High Level)

1. Analyze audio for tempo, beats, and onsets
2. Generate candidate note events
3. Quantize events to a musical grid
4. Apply musical rules (lanes, sustains, doubles)
5. Enforce strict difficulty governors
6. Export a Clone Hero–ready folder (`notes.mid`, `song.ini`, audio)

---

## Current Status

🚧 **Active prototype**

What works today:

- Local Python CLI
- Medium-difficulty lead guitar
- Groove-locked timing
- Smart singles, doubles, and sustains
- Deterministic output via seed

Planned later:

- Multiple difficulty derivation
- Section-aware phrasing
- Optional cloud / batch pipeline

---

## Requirements

- Python 3.10+
- Clone Hero (for testing output)

Key dependencies:

- `librosa`
- `numpy`
- `soundfile`
- `pretty_midi`
- `requests`

---

## Philosophy

> If a chart ever feels annoying, unreadable, or unfair — it failed.

CH 1-Click Charter prioritizes **fun over fidelity**, using clear rules and safety rails instead of chasing perfect transcription.

---

## License

MIT License
