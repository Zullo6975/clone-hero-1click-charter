# TODO

## Current Focus

- Refining Medium difficulty feel
- Locking in sustain and chord heuristics
- Reducing randomness while preserving variety

---

## Milestone 0 — Project scaffolding (COMPLETE)

- [X] Add `.gitignore` (ignore venv, outputs, audio, midi)
- [X] Add `LICENSE` (MIT)
- [X] Add `CONTRIBUTING.md`
- [X] Add `pyproject.toml` with `1clickcharter` script entry
- [X] Create package structure:
  - [X] `charter/cli.py`
  - [X] `charter/audio.py`
  - [X] `charter/midi.py`
  - [X] `charter/ini.py`
  - [X] `charter/metadata.py`
- [X] Add basic smoke test

---

## Milestone 1 — CLI + audio load

Goal: run CLI on a file and produce a valid Clone Hero folder.

- [X] CLI accepts audio input and output folder
- [X] Load audio and detect duration
- [X] Fail fast on missing/unsupported files
- [X] Copy audio as `song.mp3`

---

## Milestone 2 — Beat grid + onset candidates

Goal: produce musically-aligned candidate note events.

- [X] Beat tracking and BPM estimation
- [X] Onset detection
- [X] Merge close onsets (anti-jitter)
- [X] Quantize to 1/8 note grid

---

## Milestone 3 — Note generation (Medium, governed)

Goal: generate a playable Medium chart.

Hard constraints (always enforced):

- No sustained fast streams
- No chaotic hand travel
- No sudden difficulty spikes

- [X] Lane assignment (G/R/Y/B, selective Orange)
- [X] Smart sustains (gap + beat aware)
- [X] Selective double notes
- [X] Full-song coverage

---

## Milestone 4 — Difficulty governor (TUNING)

Goal: enforce the difficulty envelope consistently.

Metrics:

- [ ] Rolling note density
- [ ] Rolling chord density
- [ ] Movement cost window

Actions:

- [ ] Thin notes if density too high
- [ ] Convert chords to singles when needed
- [ ] Insert sustains as breathing room

Acceptance:

- [ ] Max NPS never exceeds target
- [ ] Orange remains rare and justified
- [ ] Charts feel consistent across songs

---

## Milestone 5 — Export polish

- [X] Write `song.ini`
- [X] Write `notes.mid`
- [X] Copy audio
- [X] Output loads immediately in Clone Hero
- [ ] Auto preview start time
- [ ] Difficulty rating estimate

---

## Milestone 6 — Quality loop

- [ ] Chart summary after generation
- [ ] `--seed` exposed in CLI
- [ ] `--preset`:
  - [ ] `medium_casual`
  - [ ] `medium_dense`
  - [ ] `medium_chill`

---

## Later (Optional)

- [ ] Section detection (verse / chorus)
- [ ] Multiple difficulties derived from Medium
- [ ] Optional stem separation (AI)
- [ ] Web / batch pipeline (AWS)
