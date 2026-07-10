# CLAUDE.md — macro-cycle-compass

Operating constraints for this repository. Read in full before writing any code.
Personal context. Layers on top of `C:\dev\CLAUDE.md` (the vault master) and overrides
only where noted. See SPEC.md for the design.

## Purpose
A growth × inflation regime **positioning compass** (quadrant + six-stage clock → asset
favour/avoid). The "what should I own" complement to the bear-risk timing dashboard at
`C:\dev\market-regime-dashboard`. Separate product; shared plumbing only.

## Non-negotiable architecture
Standard dashboard architecture; do not deviate without asking.
- `template.html` — single source of truth for the UI, **under 200 KB**, with a `fetch`
  fallback so it renders standalone from `data/` during development.
- `data/*.json` — one logical group per file. **Every data point carries `source_url`,
  `secondary_source_url`, `as_of`, and `notes`.** Estimates/nowcasts are flagged in `notes`.
- `scripts/pipeline.py` — injects `data/` into `template.html` → writes `docs/index.html`.
- `docs/` — GitHub Pages output. Generated, never hand-edited.
- Style tokens: copy the `:root` block and font link **verbatim** from `C:\dev\design.md`.

## Hard file rules
- Never open a built output over 500 KB (`docs/index.html`). Check size first (`wc -c`).
  Files over 200 KB: `grep -n` + line-range views + `str_replace` patches only.
- Propose a multi-turn plan before writing code (see BUILD_PLAN.md). Do not build in one pass.

## Fetchers and transport
- **Copy, do not re-solve,** the hardened fetchers from
  `C:\dev\market-regime-dashboard\scripts\sources\` — `fred.py` (curl-first,
  CDN-fingerprint-aware), `prices.py`, `bls.py` — and `net_probe.py`. The inflation-axis
  prototype already vendors `fred.py`.
- **Probe with `net_probe` before changing any transport.** Do not spoof user agents or
  collapse the curl-first/urllib alternation.
- **New source modules** needed by this build, each under the same net_probe discipline
  and two-source verification: an **ALFRED vintage** fetch (real-time point-in-time
  series; `fred.py` currently hits the current-vintage `fredgraph.csv` only), an **SF Fed
  Shapiro** supply/demand-PCE fetcher (public page, not FRED), and — deferred — a
  **Cleveland-page nowcast** fetcher.

## Data integrity (strict — guards for the three failure modes in SPEC.md)
- **Vintage / look-ahead:** classify on ALFRED real-time vintages; freeze historical
  labels point-in-time; show as-first vs as-revised. Unrevised market/policy drivers
  (curve, funds, spreads) are exempt.
- **Verify every series ID against two independent sources before first use.** Do not
  assume a FRED/BLS code from memory.
- **Flag uncertain/estimated numbers** in the UI and in `notes` (nowcasts especially).
- **Rebuild every threshold, classification rule, and asset prescription independently
  from public data.** Borrow the reference HTML's taxonomy and layout only — never its
  printed numbers (its "core PCE 4.07%" looked wrong). Treat the BofA regime/factor
  reference (Navigo, licensed, private) the same: taxonomy only, and keep contexts
  separate — this repo is Personal and public.
- Asset prescriptions are **received doctrine, flagged uncalibrated** until the
  forward-return study calibrates them. "No edge found" is an acceptable study outcome.

## Dates
Always use a date library; never compute weekdays/offsets by hand. State month indexing
in a comment wherever month arithmetic appears (Python months are 1-indexed). At least
two edge-case tests: a month boundary and a year boundary.

## Style
- **No contractions anywhere** — UI copy, comments, commit messages, docstrings.
- British / Singapore English. White / light theme, maximally readable.

## Boundaries (out of scope — do not build)
Not a trading system / order generator / position sizer. Not a recession-timing tool
(that is the bear-risk dashboard — no creep). No single-name selection; broad classes
only for v1. No macro forecasting beyond the deferred nowcast. No discretionary
overrides — rules-based; any override named and logged. Educational / IC-grade, not
financial advice.

## Analytical discipline
Forward-return work uses **entry-point discipline** (condition on regime *entry*, not
presence) and **real-time vintages** (no look-ahead). File the study via the
`research-review` skill; read `C:\dev\STUDIES_LEDGER.md` first and add a row after.

## Local development
- Node.js installed. Quick dev: `npx serve .` then open `template.html` (fetch fallback).
- Full test: `python scripts/pipeline.py` then `npx serve docs`.
- Data refresh cadence via GitHub Actions (mirror the sibling's daily/monthly split).
