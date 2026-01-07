# TODO

## Ship-it checklist (personal release)

- [ ] Test generated song in Clone Hero
  - [ ] Notes load correctly
  - [ ] Sections appear in-game
  - [ ] Star Power is collectible and usable
  - [ ] Timing feels reasonable
- [ ] Lock default tuning values
- [ ] Build + install via pipx
- [ ] Tag local git release (optional)

---

## Next iteration ideas

### Difficulty & feel

- [ ] Difficulty presets
  - Easy
  - Medium Casual
  - Medium Intense
  - Hard
- [ ] Presets map to:
  - max_nps
  - min_gap_ms
  - chord probability
  - sustain behavior
- [ ] Optional “No Orange” toggle
- [ ] Optional “More Chords” toggle

### GUI improvements

- [ ] Preset dropdown with explanations
- [ ] Tooltips for advanced settings
- [ ] Save/load last-used settings
- [ ] Compact advanced panel layout

### Validation tooling (no Clone Hero required)

- [ ] Validator summary:
  - section list
  - star power phrase count + timings
  - peak NPS warnings
- [ ] Export validation report (txt / json)
- [ ] Compare two runs side-by-side
