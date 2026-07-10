# VERIFICATION.md — series-ID two-source checks

House rule: every data-provider series ID is verified against two independent
sources before first use, with units and any interpretive thresholds confirmed
from the originating source rather than from memory. This file is the record.

Convention: "Primary" is usually the FRED series page (resolves the ID, gives
units and coverage); "Secondary" is the originating statistical agency or
Reserve Bank page (confirms the construction, units convention, and any
published thresholds).

---

## Growth axis

### CFNAIMA3 — Chicago Fed National Activity Index, three-month moving average
- **Verified:** 2026-07-10.
- **Primary — FRED** (`https://fred.stlouisfed.org/series/CFNAIMA3`): title
  "Chicago Fed National Activity Index: Three Month Moving Average (CFNAIMA3)";
  units "Index"; coverage May 1967 to May 2026; not seasonally adjusted; notes
  "a zero value ... trend rate of growth; negative values indicate below-average
  growth". Resolves via the keyless `fredgraph.csv` endpoint (709 monthly
  observations, latest 2026-05-01).
- **Secondary — Chicago Fed** (`https://www.chicagofed.org/research/data/cfnai/current-data`),
  quoted verbatim: "A zero value for the CFNAI has been associated with the
  national economy expanding at its historical trend (average) rate of growth;
  negative values with below-average growth (in standard deviation units); and
  positive values with above-average growth."
- **Units convention:** standardised index, **zero = trend growth, measured in
  standard-deviation units** (NOT a percentage). Confirmed by both sources.
- **Published interpretive thresholds (Chicago Fed, verbatim), for CFNAI-MA3:**
  - Below **−0.70** following an expansion: increasing likelihood a recession has begun.
  - Above **−0.70** following a contraction: increasing likelihood an expansion; above **+0.20**, significant likelihood of an expansion.
  - Above **+0.70** more than two years into an expansion: increasing likelihood of rising inflation.
  - Caution recorded: the **−0.35** band belongs to the CFNAI **Diffusion Index**, a different series — it must NOT be applied to MA3.
- **Use in this repo:** the growth-axis dead-bands are set from these published
  lines (inner ±0.20, outer ±0.70), used as growth-*level* language only. This
  dashboard does not make recession/inflation-timing calls (that is the
  bear-risk `market-regime-dashboard`); the Fed's outer lines are shown as
  reference markers, not as triggers.
- **Transport:** FRED and Chicago Fed both return HTTP 403 to the default
  WebFetch agent (CDN fingerprinting, as documented in `scripts/sources/fred.py`);
  both were fetched with curl under its own agent, which passes.

### CFNAI — Chicago Fed National Activity Index, monthly (context only)
- **Verified:** 2026-07-10 alongside CFNAIMA3. Same source pages; the monthly
  index the MA3 smooths. Shown on the growth trend chart as faint context (the
  "noise" the MA3 removes), never as the axis. 711 monthly observations, latest
  2026-05-01.

---

## Pending (verify before first use)

Inflation axis IDs (`MEDCPIM159SFRBCLE`, `TRMMEANCPIM159SFRBCLE`,
`CORESTICKM159SFRBATL`, `PCETRIM12M159SFRBDAL`, `CPIAUCSL`, `PCEPILFE`) and the
expectations IDs (`T5YIE`, `T5YIFR`, `EXPINF1YR`) were confirmed to resolve with
expected units on 2026-07-09 but are not yet formally cross-verified at the
originating Reserve Bank pages — carry forward to a dedicated pass. Stage-clock
IDs (r\* Laubach-Williams, curve, funds, spreads) verify when that phase is built.
