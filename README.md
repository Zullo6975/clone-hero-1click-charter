# CH 1-Click Charter

1-Click Charter is a Python-based tool that generates **playable Clone Hero lead guitar charts** from audio files with a single command.

This project is **fun-first**, targeting **Medium difficulty** charts that feel good to play and **never exceed the intensity of GH3 Medium (e.g. Cult of Personality)**. Accuracy is secondary to playability, consistency, and musical flow.

---

## Goals

- One-click generation of **Medium lead guitar** charts
- Charts that are fun, readable, and predictable
- No sudden difficulty spikes or Expert-style patterns
- Mixed single notes and double notes (within safe limits)
- Output that works immediately in Clone Hero

---

## Non-Goals

This project intentionally does **not** aim to:

- Generate Expert or Orange-lane charts
- Perfectly transcribe real guitar parts
- Match a specific game style (GH or Rock Band)
- Replace human charting for competitive play

---

## Hard Constraints (Always Enforced)

- ❌ No Orange lane
- ❌ No sustained fast streams
- ❌ No chaotic hand travel
- ❌ No sudden speed or difficulty spikes

### Difficulty Envelope

- Medium-only
- Max burst speed capped
- Chord usage allowed but governed
- Wide chords allowed, chaotic movement is not

If constraints are violated, the chart **simplifies automatically**.

---

## How It Works (High Level)

1. Analyze audio for tempo, beats, and onsets  
2. Generate candidate note events  
3. Apply musical and difficulty rules  
4. Enforce strict difficulty governors  
5. Export a Clone Hero–ready chart (`notes.mid`, `song.ini`)

---

## Current Status

🚧 Early development / prototype stage

Initial focus:

- Local Python CLI
- Single difficulty (Medium)
- Lead guitar only

Cloud deployment, UI, and advanced AI features may come later.

---

## Requirements

- Python 3.10+
- Clone Hero (for testing output)

Planned dependencies include:

- `librosa`
- `numpy`
- `soundfile`
- `pretty_midi` or `mido`

---

## Philosophy

> If a chart ever feels annoying, unreadable, or unfair — it failed.

OneClickCharter prioritizes **fun over fidelity**, using clear rules and safety rails instead of chasing perfect transcription.

---

## License

MIT License
