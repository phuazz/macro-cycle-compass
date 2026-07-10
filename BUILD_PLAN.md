# BUILD PLAN — macro-cycle-compass (draft for sign-off)

Multi-turn, one coherent phase per session (2–4 commits each), per the vault session
discipline. No production code beyond the inflation-axis prototype until ZH approves
SPEC.md and this plan. Each phase ends with tests green and a short what-changed note.

Legend: ✅ done · ▶ next · ⏳ later.

---

## Phase 0 — Scaffold ✅ (mostly done)
`README.md`, `SPEC.md`, `CLAUDE.md`, this plan; `scripts/sources/fred.py` vendored;
`scripts/inflation_axis.py` prototype + `data/inflation_axis.json`. Remaining: `tests/`
dir with the boundary-date + classifier unit-test harness; `.claude/launch.json` for the
preview server; `requirements.txt` (stdlib + python-dateutil, mirror the sibling).

## Phase 1 — Fetchers and vintage layer ▶
Copy `prices.py`, `bls.py`, `net_probe.py` from the sibling. Add an **ALFRED
vintage** fetch method (real-time point-in-time). Add the **SF Fed Shapiro** supply/demand
fetcher. `net_probe` each new transport before use. **Verify every series ID against two
sources** (`CFNAIMA3`, `MEDCPIM159SFRBCLE`, `T5YIE`, `T5YIFR`, `EXPINF1YR`, r\*
Laubach-Williams, curve/funds/spreads) and record in a `VERIFICATION.md`.

## Phase 2 — Inflation axis (lift the prototype)
Conform `inflation_axis.py` output to the per-point data schema (`source_url`,
`secondary_source_url`, `as_of`, `notes`). Fold in the **supply/demand overlay** (Shapiro)
and confirm the expectations overlay. Re-open the flagged framing calls (CPI target-
equivalent, anchoring band, momentum method) as pre-committed parameters.

## Phase 3 — Growth axis
CFNAI-MA3, read by direction, on ALFRED vintages. Dead-band + anti-flip. Emit with full
provenance.

## Phase 4 — Quadrant + confirmation + conviction
Combine the two axes into the four quadrants (Δgrowth × Δinflation, dead-banded). Build the
**labour confirmation gate** (Sahm-style rise / payroll momentum, real-time) and the
**conviction qualifier** (confirmed / tentative / diverging). Face-validity tests against
the historical regime panel in SPEC.md.

## Phase 5 — Stage clock
Six stages (Early → … → Reflation/Easing). Policy/credit drivers only (funds vs
time-varying r\*, curve level+slope trend, credit-spread trend). Hysteresis; data-driven
(sit/skip/reverse). Stage→expected-quadrant map + divergence flag. Sub-sample stationarity
check on the driver→stage mapping.

## Phase 6 — Reconciliation + asset read
Reconciliation table (per asset: quadrant-doctrine vs stage-doctrine vs verdict). Asset
read over the ~10 broad classes, **dual doctrine** (Investment Clock on the quadrant,
credit-cycle map on the stage), all **flagged uncalibrated, base rates blank**.

## Phase 7 — UI + pipeline + emit
`template.html` per `C:\dev\design.md` tokens (regime label + conviction hero →
reconciliation → asset read → axes/overlays). `scripts/pipeline.py` → `docs/`. Point-in-
time labels frozen; as-first-vs-revised shown. Emit the flagged `regime-library`
observation indicator. GitHub Actions refresh (daily/monthly split, mirror the sibling).

## Phase 8 — Forward-return study (the gate) ⏳
Read `STUDIES_LEDGER.md` first. Condition the ~10 classes' forward returns on regime
*entry* (quadrant / stage / reconciliation, + supply/demand cut) on **ALFRED vintages**,
reusing the Phase 5 machinery + `saa-trend-overlay-lab` return layer. Honest verdict —
edge or no-edge — populates or leaves blank the regime-library base rates. File via
`research-review`; ledger row added.

## Phase 9 — Deploy + verify ⏳
Public on GitHub Pages, add to the hub. Run the success-criteria checks (historical panel,
anti-flip bar, reconciliation divergences, house-rule audit). ZH sign-off.

---

**Standing follow-up in the sibling repo** (`market-regime-dashboard`): the one-line
regime-aware hint on the combined-read panel, reading this compass's `data/` output — not
duplicating logic. Build after this compass's classification is emitting.
