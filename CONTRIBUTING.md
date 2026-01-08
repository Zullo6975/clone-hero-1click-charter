# Contributing

This project prioritizes **playability over accuracy**.

Before proposing changes, understand the core philosophy:

- Medium difficulty is our primary focus (for now).
- Charts must remain readable and predictable.
- If a rule conflict occurs, the chart simplifies.
- Musical feel beats technical precision.

---

## UI/UX Standards

We strive for a professional, "app-like" feel, not a developer tool.

1. **Safe Inputs:** All `QComboBox` and `QSpinBox` widgets must subclass `Safe*` variants to disable mouse-wheel scrolling. Users hate accidental changes.
2. **Action Bar:** Primary actions (Generate, Cancel) live in the **Footer**, not the main scroll area. They must always be visible.
3. **Cursors:** Interactive elements (buttons, checkboxes, dropdowns) must use `Qt.PointingHandCursor` to signal clickability.
4. **Feedback:** Do not use the console for user feedback. Use `QMessageBox` pop-ups for success/failure and the Status Bar for transient updates ("Validating...").

---

## Development Principles

- **Explicit over Implicit:** Prefer clear rules (`if gap < 200ms`) over magic numbers.
- **Determinism:** The same audio file + same seed must **always** produce the exact same chart.
- **Fail Gracefully:** If audio analysis fails, the app should catch the error and show a human-readable pop-up, not a Python traceback.
