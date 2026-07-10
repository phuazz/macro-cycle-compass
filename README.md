# macro-cycle-compass

Growth × inflation regime compass (Personal project). A quadrant / cycle read of
the macro regime, built entirely from sourced public data, following the same
architecture as `market-regime-dashboard` (whose fetchers this repo reuses).

Status: **early prototype.** Only the **inflation axis** is built so far. The
growth axis and the dashboard UI are not started. Integration into a dashboard
is a deliberate next step, not done here.

## Inflation axis (built)

`scripts/inflation_axis.py` reduces the family of underlying-inflation measures
to a single axis reading — a level (distance from target) and a direction
(accelerating vs decelerating). A regime axis must not flip on an energy spike,
so it is built from outlier-robust / persistence gauges, with headline CPI and
core PCE shown for context only.

| Measure | Role | FRED level (12m) | FRED momentum (1m ann.) |
|---|---|---|---|
| Median CPI (Cleveland) | **anchor** | `MEDCPIM159SFRBCLE` | `MEDCPIM158SFRBCLE` |
| 16% Trimmed-mean CPI (Cleveland) | underlying | `TRMMEANCPIM159SFRBCLE` | `TRMMEANCPIM158SFRBCLE` |
| Sticky-price core CPI (Atlanta) | underlying | `CORESTICKM159SFRBATL` | `CORESTICKM158SFRBATL` |
| Trimmed-mean PCE (Dallas) | underlying | `PCETRIM12M159SFRBDAL` | `PCETRIM1M158SFRBDAL` |
| Headline CPI | context | `CPIAUCSL` (index) | — |
| Core PCE | context | `PCEPILFE` (index) | — |

**Construction.** Level = published 12-month change (index YoY for the context
series). Momentum = 3m / 6m annualised — the trailing mean of the published
1-month-annualised prints for the underlying gauges, geometric annualisation for
the context index series. Direction = 6m annualised minus 12m YoY, with a 0.3pp
dead-band. Target framing: CPI measures run ~0.3–0.4pp above PCE, so the 2% PCE
objective is treated as ~2.4% on CPI gauges, 2.0% on the PCE gauge (a flagged
framing choice, not a fitted parameter).

### Expectations overlay (forward)

A second, forward-looking layer: market-implied and model expected inflation.
Distinct from the realised axis — it senses turns earlier, and whether long-run
expectations are anchored is itself regime-defining. All public FRED (the
Bloomberg 1y inflation swap seen in vendor tools is licensed; public breakevens
plus the Cleveland model expectation stand in for it).

| Measure | FRED | Cadence |
|---|---|---|
| 5-year breakeven (market) | `T5YIE` | daily |
| 5y5y forward (market, anchoring gauge) | `T5YIFR` | daily |
| 1-year expected (Cleveland model) | `EXPINF1YR` | monthly |

Anchoring is read off the 5y5y forward (a band around ~2%, since TIPS breakevens
carry a modest premium). The overlay also reports each series' 3-month change and
the gap between market expectations and the realised anchor.

**A nowcast overlay is deferred, not dropped.** The Cleveland Fed inflation
nowcast (a daily model estimate of the current month's CPI/PCE, which would close
the axis's ~6-week lag) is public but **not a stable FRED series** — it needs a
dedicated Cleveland-page fetcher and its own verification before wiring, so it is
flagged rather than bolted on as a fragile scrape. **Truflation was rejected:**
proprietary, no clean public feed, not redistributable on a public dashboard, and
not two-source verifiable (see the market-regime-dashboard session, 2026-07-09).

**Latest reading (realised data May 2026, expectations to Jul 2026, run
2026-07-09):** underlying inflation ~2.9% YoY and broadly stable (median 2.9,
trimmed 2.9, sticky-core 3.1, trimmed-PCE 2.4); headline CPI +4.3% with 6m
annualised +5.6% and core PCE +3.4% — both hot and accelerating
(**headline-over-underlying gap +1.4pp**). Expectations are **anchored** (5y5y
forward 2.2%, flat; 5y breakeven 2.3%, easing) even as the Cleveland 1y model
firms to 3.0%. Regime note: *above target realised (~2.9%), expectations anchored
— the market prices inflation to fade below the current underlying pace.* An
elevated-but-anchored inflation state, not a de-anchoring one.

## Run

```
python scripts/inflation_axis.py          # print the table, write data/inflation_axis.json
python scripts/inflation_axis.py --quiet   # JSON only
```

No API key (keyless FRED `fredgraph.csv`, curl-first transport). Output carries a
`source_id`, `source_url`, and `as_of` per measure.

## Open items / next steps

1. **Growth axis** — the other half of the quadrant (candidates: real activity /
   WEI, employment momentum, ISM new orders, real income). Then place the regime
   in the growth × inflation quadrant (reflation / goldilocks / stagflation /
   deflation).
2. **Nowcast overlay** — build a Cleveland-page fetcher for the daily CPI/PCE
   nowcast (public but not on FRED) to close the realised axis's ~6-week lag;
   currently emitted in the output as `nowcast.status = "deferred"`.
3. **Dashboard panel** — an HTML panel per `C:\dev\design.md` once both axes
   exist; this is the "integrate into a regime dashboard" step.
3. **Formal series verification** — every FRED ID against a second independent
   source (house rule); IDs here were confirmed to resolve with expected units on
   2026-07-09 but not yet cross-verified at the originating Reserve Bank pages.
4. **Backtest** — do these regime states map to asset-class forward returns? Use
   entry-point discipline and walk-forward, per the vault backtesting rules.
5. **CPI vs PCE weighting** — decide whether the anchor stays median CPI
   (timely) or shifts toward trimmed-mean PCE (Fed-target relevant).

## Provenance

`scripts/sources/fred.py` is vendored verbatim from `market-regime-dashboard`
(the curl-first keyless FRED fetcher). Data integrity, dating, and dashboard
rules follow `C:\dev\CLAUDE.md`.
