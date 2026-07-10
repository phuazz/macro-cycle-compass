# SPEC — macro-cycle-compass (draft for sign-off)

Status: **draft, pending ZH sign-off.** No production code beyond the inflation-axis
prototype until this is approved. Personal context. Layers on `C:\dev\CLAUDE.md`.

A growth × inflation regime **positioning compass**: a four-quadrant regime read plus
a six-stage short-term-debt-cycle clock, driving an asset-class favour/avoid read. It
answers "what regime are we in and what should I own" — the complement to the bear-risk
timing dashboard at `C:\dev\market-regime-dashboard` (which answers "should I reduce
risk"). Separate product and repo; they share plumbing, not a signal.

---

## The three ways this could be silently wrong — and the guard for each

Stated first, per house rule, because these shape every build decision.

1. **Macro-data vintage / look-ahead.** CFNAI, the inflation levels, and unemployment
   are all *revised*. Classifying today's regime on today's revised series, or
   backtesting on revised prints, overstates the framework by using data that did not
   exist at the decision point. **Guard:** every revised input is read from an ALFRED
   real-time vintage; the classifier runs on data-as-it-was; historical labels are
   frozen point-in-time; the UI shows as-first-estimated versus as-revised. The stage's
   market/policy drivers (curve, funds, spreads) are unrevised and exempt.

2. **Small-sample overfit in the asset prescriptions.** There are only a handful of each
   regime in ~55 years, fewer after structural breaks. Tuned favour/avoid rules would
   fit noise. **Guard:** prescriptions ship as *received doctrine* (Investment Clock on
   the quadrant, credit-cycle map on the stage), visibly flagged uncalibrated with blank
   base rates, never as trade triggers. The forward-return study either calibrates them
   or honestly concludes there is no standalone edge — "no edge found" is a successful,
   pre-committed outcome.

3. **Regime-boundary instability.** Thresholds tuned so today looks clean, or a label
   that flips on a single noisy monthly print. **Guard:** axes read by direction with a
   pre-committed dead-band; the six-stage clock is data-driven with hysteresis (a
   confirmed move required to change stage); the labour confirmation gate holds a fresh
   transition "tentative" until ratified; stage↔quadrant divergence is surfaced, never
   silently reconciled.

Plus: every FRED/BLS/Fed series ID is verified against two independent sources before
first use.

---

## Architecture — three timescales

- **Coincident → the quadrant** (where we are). CFNAI-MA3 (growth) × underlying-inflation
  momentum (inflation), read by direction, dead-banded.
- **Leading → the stage** (where we are heading). Six-stage clock driven by the
  policy/credit cycle only.
- **Confirming → the labour gate** (has the turn ratified). Sahm-style rise / payroll
  momentum, feeding a conviction qualifier on the headline.

**Headline output:** the regime label (quadrant + stage) with a conviction qualifier
(*confirmed / tentative / diverging*). The asset read sits beneath as the flagged
prescription; the reconciliation verdict is the confidence badge.

## Quadrant (coincident)

- **Growth axis:** Chicago Fed National Activity Index 3-month average (`CFNAIMA3`),
  read by direction. Deliberately *not* labour (CFNAI already contains ~24 employment
  series — folding labour in double-counts).
- **Inflation axis:** underlying momentum from the prototype — median CPI (anchor),
  16% trimmed-mean CPI, Atlanta sticky-price core CPI, Dallas trimmed-mean PCE; headline
  CPI and core PCE context only. Read by direction (accelerating/decelerating), dead-banded.
- **Supply/demand overlay** (Shapiro, SF Fed): qualifies the inflation read and modulates
  the prescription — demand-driven versus supply-driven inflation carry opposite asset
  implications (metals vs energy). Does not change the axis.
- Four quadrants = Δgrowth × Δinflation. Framing choices (target-equivalents ~2.4% CPI /
  2.0% PCE, dead-band widths) are flagged, not fitted.

## Stage (leading / forward)

- Six stages: Early Cycle → Mid → Late → Tightening → Recession → **Reflation/Easing**
  (renamed from the reference's "Late Recession" — the pivot to risk-on is the most
  asset-relevant stage).
- **Drivers, policy/credit only** (kept independent of the quadrant so the reconciliation
  is meaningful): Fed funds trajectory versus a **time-varying r\*** (Laubach-Williams),
  the yield curve (10y–3m level + slope trend), and credit-spread trend. All unrevised
  market/policy data → vintage-safe.
- Data-driven, not a mechanical hand: the 1→6 order is the *expected* path, not a rail;
  sit/skip/reverse allowed; a confirmed (smoothed / hysteresis) move required to change
  stage.
- Each stage maps to an **expected quadrant**; when the coincident quadrant differs, the
  divergence is flagged — the engine of both the reconciliation table and the conviction
  qualifier. A sub-sample stationarity check on the driver→stage mapping is required
  (structural breaks: Volcker, ZLB, 2020–21 fiscal).

## Reconciliation, asset read, overlays

- **Reconciliation table** (the differentiator): per asset, quadrant-doctrine says vs
  stage-doctrine says vs verdict, flagging divergences.
- **Asset universe (v1, ~10 broad classes):** DM equities, EM equities, duration (USTs),
  credit/HY, industrial metals, energy, gold, USD, real assets/REITs, cash. Metals vs
  energy is the asset-level mirror of the supply/demand overlay. Sectors, factors, size,
  curve segments deferred to v1.1.
- **Dual prescriptions, both flagged received-doctrine:** Merrill Investment Clock on the
  quadrant; a credit-cycle map on the stage. Calibrated only by the forward-return study.
- **Overlays:** supply/demand (built into the read), expectations (built — `T5YIE` /
  `T5YIFR` / `EXPINF1YR`), inflation nowcast (deferred — public but not FRED; needs a
  Cleveland-page fetcher).

## Integrity, emit, study

- **Point-in-time vintages** are a first-class requirement (guard 1).
- **regime-library:** emit the *classification* (quadrant + stage + conviction +
  supply/demand read) as an observation-layer indicator, schema-conformant,
  `historical_base_rates: null`, `qualitative_note` carrying the conviction/divergence
  caveat, flagged experimental. Do not emit prescriptions. Do not consume for v1.
- **Forward-return study = the gate.** Condition the ~10 classes' forward returns
  (1/3/6/12m, conditional-vs-base, per-episode) on regime **entry** (transition), three
  separate conditionings (quadrant / stage / reconciliation state) plus the supply/demand
  cut, on ALFRED vintages. Reuses `market-regime-dashboard`'s Phase 5 machinery and
  `saa-trend-overlay-lab`'s return layer. Filed via `research-review`; ledger updated.
  Sobering prior: the Phase 5 and Lens 2 studies found regime *level* carries no
  standalone forward-return edge — expect the same and report it honestly.

## Success criteria

- **Shell v1:** classifier reproduces a pre-specified panel of historical regimes on
  real-time vintages (2021 reflation, 2022 tightening/stagflationary, 2008–09
  deflationary contraction, 2017/2019 mid-cycle); label passes an anti-flip stability
  bar; reconciliation flags known divergences; regime label + conviction + flagged asset
  read render with uncertainty loud; house rules met; deployed public, in the hub, emits
  the flagged regime-library indicator.
- **Study v1.1:** runs on ALFRED vintages and gives an honest answer — usable tilts
  (base rates populated) *or* documented no-edge (prescriptions stay doctrine-flagged,
  compass documented as descriptive). Both are success.

## Explicitly out of scope

Not a trading system / order generator / position sizer. Not a recession-timing tool
(that is the bear-risk dashboard). No single-name selection. No macro forecasting beyond
the deferred nowcast. No discretionary overrides (rules-based; overrides named + logged).
Monthly macro cadence (daily market data for stage drivers). v1 emits to regime-library
but does not consume. Educational / IC-grade, not financial advice.

## Decisions still open (pre-build)

- Exact CFNAI series (`CFNAIMA3` vs building MA3 from `CFNAI`) — verify + decide.
- Dead-band widths and the anti-flip hysteresis parameters — set as pre-committed, not tuned.
- Whether the anchor stays median CPI (timely) or shifts toward trimmed-mean PCE (Fed-target).
