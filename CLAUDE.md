# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

PyLCARS is a PyQt5 widget library that renders Star Trek LCARS-style UIs. It provides styled widgets, SVG-based rendering with caching, a color/condition system, and audio playback.

## Commands

```bash
# Install with dev deps
pip install -e ".[dev]"

# Run a demo
python -m pylcars.demos.simple_window

# Tests
pytest tests/ -v
pytest tests/ -m "not gui"          # skip GUI tests
pytest tests/ --cov=pylcars         # with coverage

# Lint / type / format
flake8 pylcars tests/
mypy pylcars/ --ignore-missing-imports
black pylcars/                      # line length 100
```

## Architecture

### Layers

```
Demo Apps / User Apps
    ↓
Widget Layer  (Bracket, Block, Textline, Deco, Slider, Menue, LayoutGrid, …)
    ↓
Core Layer    (Lcars, Sound, Colors, Orientation, config)
    ↓
PyQt5 / PyAudio / xxhash
```

### Key classes

**`Lcars` (`lcars.py`)** — Main window. Inherits from both `Sound` and `QMainWindow` (multiple inheritance). Entry point for every app.

**`Sound` (`sound.py`)** — Manages async WAV playback via PyAudio callbacks. Lazy-initialised; call `set_play_sound(True)` first. Streams cleaned up in `__del__`.

**`Widgets` (`widgets/widgets.py`)** — Mixin that every widget class also inherits from. Owns all SVG logic:
- `adapt_svg(color)` → substitutes colour hex into an SVG template
- `build_svg()` → hashes SVG+size with xxhash, writes PNG to `background/XX/YYY/ZZZ.png` cache
- `paint_back()` → sets the cached PNG as the widget stylesheet background
- `tickle()` / `tockle()` — 300 ms flash / toggle-colour animations

All concrete widgets (e.g. `Bracket`, `Block`, `Menue`) mix in `Widgets` alongside a PyQt5 base class (`QPushButton`, `QFrame`, `QLabel`).

### Enumerations

- **`Colors`** — hex strings for the LCARS palette (orange, flieder, blaugrau, leuchtblau, …)
- **`Conditions`** — maps status names to colours (alert→red, active→blaugrau, …)
- **`Orientation`** — left=0, right=1, top=2, bottom=3
- **`Enumeration`** — immutable set-based base used by all of the above

All constants live in `config.py` (window size, animation durations, font name, audio chunk size).

### Widget creation pattern

```python
widget = SomeWidget(
    lcars=parent_widget,
    rect=QtCore.QRect(x, y, w, h),
    text="Label",
    color=Colors.orange,
)
```

`rect` is always an absolute `QRect` within the parent; widgets call `setGeometry(rect)` directly.

### SVG caching

Cache lives in `background/` relative to the working directory, keyed by a hierarchical xxhash of (SVG content + rendered size). A cache hit skips rasterisation entirely.

### Font

Primary font is "LCARS" (must be installed separately — see `FONTS.md`). Falls back to Courier with a printed warning. Detection uses `QFontDatabase` (not `QFont.exactMatch`) for macOS compatibility.
