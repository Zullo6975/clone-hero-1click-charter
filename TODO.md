# Project Roadmap

## 🟢 Phase 1: Polish & Stability (Current)

- [x] **Safe Inputs:** Prevent mouse-wheel scrolling from accidentally changing values on dropdowns/spinners.
- [x] **Action Bar:** Move Generate/Cancel buttons to a fixed footer.
- [x] **Separate Logs:** Move logs to a pop-up window to clean up the main UI.
- [x] **Smart Delay:** Add lead-in time via `song.ini` delay instead of destructive audio editing.
- [x] **Required Fields:** Visual cues (Red `*`) for Title/Artist/Audio/Output.

---

## 🟡 Phase 2: Batch Processing (Next)

The goal: "Chart an entire discography while I make coffee."

- [ ] **Queue UI:** Replace the single "Input Audio" box with a `QListWidget` that accepts multiple files.
- [ ] **Batch Logic:** Refactor `qt_app.py` to iterate through the list.
- [ ] **Error Handling:** If Song A fails, log it and proceed to Song B (don't crash the app).
- [ ] **Auto-Naming:** Smarter regex to extract "Artist - Title" from filenames since the user can't type metadata for 50 songs.

---

## 🔴 Phase 3: Multi-Difficulty Support (Long Term)

The goal: "One click, four difficulties."

- [ ] **Refactor `midi.py`:** Separation of concerns.
  - `Analysis` (Beats/Onsets) happens ONCE.
  - `PatternGeneration` happens 4 times (Easy, Med, Hard, Expert) with different `ChartConfig` objects.
- [ ] **Reduction Algorithm:** - Implement a "Parent -> Child" reduction logic.
  - Expert notes are the "source of truth".
  - Hard = Expert minus 20% density + simpler chords.
  - Medium = Hard minus 30% + no Orange.
  - Easy = Medium minus 40% + playing only on the beat.
- [ ] **UI Update:**
  - Add "Target Difficulties" checkboxes (e.g., [x] Easy [x] Medium [x] Hard [x] Expert).
  - Allow distinct settings per difficulty tier (eventually).
