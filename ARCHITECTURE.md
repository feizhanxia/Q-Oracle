# Q-Oracle Architecture (Draft)

This document captures the agreed initial architecture and algorithm choices.

## Goals
- Quantum RNG as entropy source
- High-island style casting: first determine the base hexagram, then a single moving line
- CLI ASCII output for validation, and a Streamlit UI for a minimal web view

## Directory layout
- core/
  - qrng.py: unified QRNG interface (LFDR / ANU / fallback)
  - hexagrams.py: 64-hexagram table (6-bit patterns, names, index)
  - casting.py: casting logic (base hexagram, moving line, derived hexagram)
- ui/
  - cli.py: ASCII rendering for quick verification
  - app.py: Streamlit UI
- config/
  - settings.py: configuration loader and defaults
- tests/ (optional, later)

## Casting rules (agreed)
1) Base hexagram:
   - Use 6 random bits.
   - Each line is yin/yang with equal probability.
2) Moving line position:
   - Uniformly choose 1–6.
3) Change rule:
   - The moving line always flips (yin <-> yang).

## Data flow
QRNG -> random bytes -> 6-bit base hexagram -> moving line -> changed hexagram -> UI render

## Configuration
- `.env` stores QRNG API keys (e.g., ANU key).
- Streamlit secrets live in `.streamlit/secrets.toml`.

## Notes
- The base hexagram is generated first, without any "old yin/old yang" concept.
- The single moving line is chosen separately to enforce a one-line change.
