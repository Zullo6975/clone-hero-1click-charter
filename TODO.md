# TODO

## Milestone 0 — Project scaffolding
- [ ] Add `.gitignore` (ignore venv, outputs, audio, midi)
- [ ] Add `LICENSE` (MIT)
- [ ] Add `CONTRIBUTING.md`
- [ ] Add `pyproject.toml` with `oneclickcharter` script entry
- [ ] Create package structure:
  - [ ] `charter/cli.py`
  - [ ] `charter/audio.py`
  - [ ] `charter/beat.py`
  - [ ] `charter/events.py`
  - [ ] `charter/rules.py`
  - [ ] `charter/governor.py`
  - [ ] `charter/midi.py`
  - [ ] `charter/ini.py`
- [ ] Add `tests/test_smoke.py`

## Milestone 1 — CLI + audio load (no chart yet)
Goal: run CLI on a file and print basic analysis.

- [ ] CLI accepts:
  - [ ] `--audio /path/to/file`
  - [ ] `--title`, `--artist` (optional)
  - [ ] `--out output_dir`
- [ ] Load audio and log:
  - [ ] duration
  - [ ] sample rate
  - [ ] RMS / loudness summary
- [ ] Fail fast with clear errors for unsupported files

## Milestone 2 — Beat grid + onset candidates
Goal: produce time-aligned candidate note events.

- [ ] Implement beat tracking:
  - [ ] estimate BPM
  - [ ] beat timestamps
- [ ] Implement onset detection:
  - [ ] raw onset timestamps
  - [ ] merge close onsets (anti-jitter)
- [ ] Quantize candidates to grid:
  - [ ] default 1/8 grid
  - [ ] optional brief 1/16 windows (but conservative)

## Milestone 3 — Note generation (Medium, no Orange)
Goal: generate a playable “draft” chart.

Hard constraints (always):
- No Orange lane
- No 3-note chords
- No sustained fast streams
- No chaotic hand travel
- No sudden difficulty spikes

- [ ] Lane assignment (G/R/Y/B only)
- [ ] Chord generation:
  - [ ] allow 2-note chords (adjacent + spaced)
  - [ ] avoid G+B
- [ ] Sustains:
  - [ ] add when energy decays slowly
  - [ ] avoid micro-sustains

## Milestone 4 — Difficulty governor (the secret sauce)
Goal: enforce your difficulty envelope every time.

Metrics to compute:
- [ ] note density (rolling 1s window)
- [ ] chord density (rolling 4s window)
- [ ] consecutive chord streak length
- [ ] movement cost (rolling 2s window)

Enforcement actions:
- [ ] thin notes if density too high
- [ ] convert some chords -> single notes when chord/density too high
- [ ] reduce big jumps / zig-zags (rewrite lanes)
- [ ] insert sustains as “breathing room”

Acceptance test:
- [ ] worst 1s window never exceeds target density cap
- [ ] orange never appears
- [ ] charts remain playable and consistent across runs

## Milestone 5 — Export Clone Hero folder
Goal: output loads immediately in Clone Hero.

- [ ] Write `song.ini` (title, artist, delay/offset placeholder)
- [ ] Write `notes.mid` (Clone Hero-compatible track)
- [ ] Copy audio into output folder
- [ ] Print final output path + quick summary stats

## Milestone 6 — Quality loop
Goal: iterate fast on feel.

- [ ] Add “chart summary” printed after generation:
  - [ ] BPM estimate
  - [ ] total notes
  - [ ] chords count
  - [ ] max notes/sec (worst window)
  - [ ] max movement cost window
- [ ] Add `--seed` for repeatable randomness
- [ ] Add `--preset`:
  - [ ] `medium_casual` (default)
  - [ ] `medium_chill`
  - [ ] `medium_dense`

## Later (optional)
- [ ] Stem separation (AI) as an optional step
- [ ] Section detection (verse/chorus) for motif reuse
- [ ] Multiple difficulties (Easy/Hard from Medium base)
- [ ] Web/AWS pipeline (S3 + job queue + container/Lambda)
