# v2.2.0 Pre-Release Testing Checklist

End-to-end verification for every change group shipped in this release.
Test on **Windows**, **macOS**, and **Linux** where indicated.

---

## 0. Environment Setup

- [ ] Clean clone of the repo (or `git stash` local changes)
- [ ] `pip install -e .` succeeds with no errors
- [ ] `python -m charter --help` prints usage (no import errors)
- [ ] Verify reported version: `python -c "from charter import __version__; print(__version__)"` → `2.2.0`

---

## 1. Dead Code Removal (Group 1)

- [ ] `python -m charter --no-orange` → unrecognized argument error (flag removed)
- [ ] `python -m charter --grid-snap` → unrecognized argument error (flag removed)
- [ ] `python -m charter --no-rhythmic-glue` → unrecognized argument error (flag removed)
- [ ] Grep the codebase: `allow_orange`, `rhythmic_glue`, `grid_snap` appear **only** in git history, not in active code
- [ ] `pydub` is not in `pip show 1clickcharter` dependencies

---

## 2. Version Consolidation (Group 2)

- [ ] `charter/__init__.py` shows `__version__ = "2.2.0"`
- [ ] `pip show 1clickcharter` reports version `2.2.0`
- [ ] Open GUI → footer/about shows `2.2.0`
- [ ] `scripts/archiver.py` → run it and confirm the output zip filename contains `2.2.0`

---

## 3. Determinism (Group 3)

- [ ] Generate a chart with `--seed 42` (or set seed in GUI) for any audio file → save the MIDI
- [ ] Generate the **exact same chart** again with the same seed → diff the two MIDIs → **byte-identical**
- [ ] Change seed to `43` → output differs (sanity check)

---

## 4. Cross-Platform GUI (Group 4)

### Windows

- [ ] Launch GUI → fonts render cleanly, no `11pt` cramping
- [ ] Toggle between light and dark system themes → separators remain visible (not washed-out `#d0d0d0`)
- [ ] Click the output folder link → Explorer opens the correct directory

### macOS

- [ ] Launch GUI → fonts render at macOS-appropriate size (not oversized)
- [ ] Click the output folder link → Finder opens the correct directory
- [ ] Window does not exceed screen bounds on a 13" display

### Linux

- [ ] Launch GUI → fonts render cleanly under Wayland and X11
- [ ] Click the output folder link → default file manager opens
- [ ] `snap_to_content()` respects 85% of screen height

### All Platforms

- [ ] Drag audio file → label shows filename in bold
- [ ] Clear audio → label resets to italic "Drag Audio Files Here"
- [ ] Queue 3 files → finish all → label resets correctly at the end
- [ ] Batch run → finish → label resets correctly after summary dialog

---

## 5. CI / Build Pipeline (Group 5)

- [ ] Push a test tag (`v2.2.0-rc1`) → GitHub Actions triggers `release.yml`
- [ ] **Quality gate** job runs lint + tests and passes
- [ ] **Windows** build produces `.exe` inside a `.zip`
- [ ] **macOS** build completes (FFmpeg installed via `brew`, not evermeet.cx)
- [ ] **Linux** build produces AppImage
- [ ] All 3 builds upload SHA-256 `.sha256` checksum files alongside artifacts
- [ ] Manually verify one checksum: `sha256sum -c <artifact>.sha256`

---

## 6. Code Quality / DRY (Group 6)

These are internal refactors — no user-visible behavior changes. Verify nothing regressed:

- [ ] Single-song generation works end-to-end (MIDI + song.ini + optional .chart)
- [ ] Batch of 3+ songs works end-to-end with summary dialog
- [ ] `validator.py` standalone: `python -m charter.validator <song_dir>` runs without `NameError`
- [ ] `stats.py` standalone: chart stats JSON is written correctly after generation

---

## 7. Performance Optimizations (Group 7)

- [ ] Generate a chart for a **long song** (5+ minutes) — confirm it completes without timeout or freeze
- [ ] Compare generation time vs v2.1.4 on the same file (expect modest speedup on long tracks)
- [ ] Density visualizer data looks correct (no flat-zero or wildly different curves vs v2.1.4)
- [ ] Chart stats JSON: `max_nps_1s` and window `notes` counts are reasonable and match manual spot-checks

---

## 8. Smoke Tests — Full Workflow

- [ ] **Single song (MP3):** Drag → auto-metadata fills → Generate → open in Clone Hero → playable
- [ ] **Single song (OGG):** Same as above with `.ogg` input
- [ ] **Single song (WAV):** Same as above with `.wav` input
- [ ] **Single song (FLAC):** Same as above with `.flac` input
- [ ] **Batch (folder drag):** Drag folder of 5+ songs → Run Queue → all succeed → summary dialog correct
- [ ] **Batch with bad file:** Include a corrupt/empty file → queue continues → summary shows 1 failure
- [ ] **.chart export:** Enable `.chart` export in Advanced → generate → `.chart` file exists and opens in Moonscraper
- [ ] **Preset save/load:** Save a preset → close app → reopen → load preset → settings restored
- [ ] **Auto-update check:** (if applicable) app checks GitHub releases on startup without crashing

---

## 9. Final Sign-Off

- [ ] All checkboxes above are checked
- [ ] CHANGELOG.md accurately describes every change
- [ ] README.md roadmap is current
- [ ] Tag `v2.2.0` and push → release build succeeds → artifacts downloadable
