"""Inflation-axis prototype for the growth x inflation regime compass.

Fetches the family of underlying-inflation measures from FRED (public, keyless)
and reduces them to a single inflation-axis reading: an underlying level (how
far from target) and a direction (accelerating vs decelerating). Built to be
lifted into macro-cycle-compass as the inflation axis of the growth x inflation
quadrant. The growth axis is out of scope here — this is one of the two axes.

Why these measures (dashboard discussion, 2026-07-09): headline CPI is noisy and
can be pushed around by a few outlier categories, so a regime axis must not flip
on an energy spike. The axis is therefore built from underlying / trend /
persistence gauges, with headline CPI and core PCE shown only for context:

  - Median CPI (Cleveland)          primary trend anchor (best forecast record)
  - 16% Trimmed-mean CPI (Cleveland)
  - Sticky-price core CPI (Atlanta) persistence / embedded expectations
  - Trimmed-mean PCE (Dallas)       Fed-target relevance (PCE, not CPI)
  - Headline CPI, Core PCE          context only

Construction
------------
Level      = the published 12-month change (FRED "...M159..." variants; index
             YoY for the two context series).
Momentum   = 3-month and 6-month annualised. For the underlying gauges this is
             the trailing mean of the published 1-month-annualised prints
             (FRED "...M158..." variants), which is how 3m/6m annualised
             inflation is conventionally shown; for the index context series it
             is geometric annualisation of the level.
Direction  = 6-month annualised minus 12-month YoY. Positive (beyond a 0.3pp
             band) = accelerating (reflationary), negative = decelerating
             (disinflationary), otherwise stable.

Target framing: CPI measures run structurally ~0.3-0.4pp above PCE, so the 2%
PCE objective is treated as ~2.4% on the CPI gauges and 2.0% on the PCE gauge.
This is a framing choice, flagged, not a fitted parameter.

FRED series IDs are from FRED and were confirmed to resolve with expected units
(2026-07-09). Verify against the originating Reserve Bank pages before any
production use (house rule: every series ID against two sources).

Dates via the standard library only (no manual month arithmetic).

Usage:  python scripts/inflation_axis.py           # print table + write data/inflation_axis.json
        python scripts/inflation_axis.py --quiet    # write JSON only
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
sys.path.insert(0, str(SCRIPTS_DIR))

from sources.fred import fetch_series, FredFetchError  # noqa: E402

# Target-equivalents of the 2% PCE objective (see module docstring).
CPI_TARGET = 2.4
PCE_TARGET = 2.0

# role: "anchor" (primary), "underlying" (in the composite), "context" (shown only).
RATE_MEASURES = [
    {"key": "median_cpi", "name": "Median CPI", "bank": "Cleveland Fed", "role": "anchor",
     "target": CPI_TARGET, "level_id": "MEDCPIM159SFRBCLE", "mom_id": "MEDCPIM158SFRBCLE",
     "source_url": "https://www.clevelandfed.org/indicators-and-data/median-cpi"},
    {"key": "trimmed_cpi", "name": "16% Trimmed-mean CPI", "bank": "Cleveland Fed", "role": "underlying",
     "target": CPI_TARGET, "level_id": "TRMMEANCPIM159SFRBCLE", "mom_id": "TRMMEANCPIM158SFRBCLE",
     "source_url": "https://www.clevelandfed.org/indicators-and-data/median-cpi"},
    {"key": "sticky_core_cpi", "name": "Sticky-price core CPI", "bank": "Atlanta Fed", "role": "underlying",
     "target": CPI_TARGET, "level_id": "CORESTICKM159SFRBATL", "mom_id": "CORESTICKM158SFRBATL",
     "source_url": "https://www.atlantafed.org/research-and-data/data/sticky-price-cpi"},
    {"key": "trimmed_pce", "name": "Trimmed-mean PCE", "bank": "Dallas Fed", "role": "underlying",
     "target": PCE_TARGET, "level_id": "PCETRIM12M159SFRBDAL", "mom_id": "PCETRIM1M158SFRBDAL",
     "source_url": "https://www.dallasfed.org/research/pce"},
]
INDEX_MEASURES = [
    {"key": "headline_cpi", "name": "Headline CPI", "bank": "BLS", "role": "context",
     "target": CPI_TARGET, "index_id": "CPIAUCSL",
     "source_url": "https://fred.stlouisfed.org/series/CPIAUCSL"},
    {"key": "core_pce", "name": "Core PCE", "bank": "BEA", "role": "context",
     "target": PCE_TARGET, "index_id": "PCEPILFE",
     "source_url": "https://fred.stlouisfed.org/series/PCEPILFE"},
]

# Forward overlay: market-implied and model expected inflation. Distinct from the
# realised axis — it senses turns the realised gauges confirm only later, and its
# anchoring (5y5y forward near target) is itself regime-defining. All public FRED;
# the Bloomberg 1y inflation swap seen in vendor tools is licensed, so the public
# breakevens plus the Cleveland model expectation stand in for it.
EXPECTATION_MEASURES = [
    {"key": "market_5y", "name": "5y breakeven (market)", "id": "T5YIE", "cadence": "daily",
     "source_url": "https://fred.stlouisfed.org/series/T5YIE"},
    {"key": "forward_5y5y", "name": "5y5y forward (market)", "id": "T5YIFR", "cadence": "daily",
     "role": "anchor", "source_url": "https://fred.stlouisfed.org/series/T5YIFR"},
    {"key": "model_1y", "name": "1y expected (Cleveland model)", "id": "EXPINF1YR", "cadence": "monthly",
     "source_url": "https://fred.stlouisfed.org/series/EXPINF1YR"},
]


def _valid_pairs(dates: list[str], values: list[float | None]) -> tuple[list[str], list[float]]:
    pairs = [(d, v) for d, v in zip(dates, values) if v is not None]
    return [d for d, _ in pairs], [v for _, v in pairs]


def _trailing_mean(values: list[float], n: int) -> float | None:
    if len(values) < n:
        return None
    window = values[-n:]
    return sum(window) / len(window)


def _trim_history(dates: list[str], values: list[float], months: int = 120) -> list[list]:
    """Last ``months`` observations as ``[date, rounded_value]`` pairs (2 dp), for
    the trend chart. Inputs are already None-filtered by ``_valid_pairs``."""
    pairs = list(zip(dates, values))[-months:]
    return [[d, round(v, 2)] for d, v in pairs]


def compute_rate_measure(m: dict) -> dict:
    ldates, lvalues = _valid_pairs(*fetch_series(m["level_id"]))
    _mdates, mvalues = _valid_pairs(*fetch_series(m["mom_id"]))
    # The published "...M159..." level series IS the 12-month percentage change,
    # so its own history is the YoY trend directly — no extra FRED call.
    return {
        "as_of": ldates[-1],
        "yoy": lvalues[-1],
        "mom_3m_ann": _trailing_mean(mvalues, 3),
        "mom_6m_ann": _trailing_mean(mvalues, 6),
        "history": _trim_history(ldates, lvalues),
    }


def compute_index_measure(m: dict) -> dict:
    dates, values = _valid_pairs(*fetch_series(m["index_id"]))
    yoy = (values[-1] / values[-13] - 1) * 100 if len(values) >= 13 else None
    mom_6m = ((values[-1] / values[-7]) ** (12 / 6) - 1) * 100 if len(values) >= 7 else None
    mom_3m = ((values[-1] / values[-4]) ** (12 / 3) - 1) * 100 if len(values) >= 4 else None
    # YoY trend from the index: (index[i] / index[i-12] - 1) for each month.
    yoy_dates = [dates[i] for i in range(12, len(values))]
    yoy_values = [(values[i] / values[i - 12] - 1) * 100 for i in range(12, len(values))]
    return {"as_of": dates[-1], "yoy": yoy, "mom_3m_ann": mom_3m, "mom_6m_ann": mom_6m,
            "history": _trim_history(yoy_dates, yoy_values)}


def direction(yoy: float | None, mom_6m: float | None, band: float = 0.3) -> str:
    if yoy is None or mom_6m is None:
        return "n/a"
    gap = mom_6m - yoy
    if gap > band:
        return "accelerating"
    if gap < -band:
        return "decelerating"
    return "stable"


def level_bucket(yoy: float | None, target: float) -> str:
    if yoy is None:
        return "n/a"
    if yoy >= target + 1.0:
        return "well above target"
    if yoy >= target + 0.3:
        return "above target"
    if yoy <= target - 0.5:
        return "below target"
    return "near target"


def compute_expectation(m: dict) -> dict:
    dates, values = _valid_pairs(*fetch_series(m["id"]))
    lookback = 63 if m["cadence"] == "daily" else 3  # ~3 months either way
    change_3m = (values[-1] - values[-1 - lookback]) if len(values) > lookback else None
    return {"level": values[-1], "change_3m": change_3m, "as_of": dates[-1]}


def anchoring(forward_5y5y: float | None) -> str:
    """Is the long-run market expectation sitting at target? 5y5y forward is the
    canonical anchoring gauge; a small band around ~2% (TIPS breakevens carry a
    modest premium) reads as anchored."""
    if forward_5y5y is None:
        return "n/a"
    if forward_5y5y > 2.6:
        return "drifting up"
    if forward_5y5y < 1.6:
        return "drifting down"
    return "anchored"


def build() -> dict:
    rows: list[dict] = []
    history_by_key: dict[str, list] = {}
    for m in RATE_MEASURES + INDEX_MEASURES:
        try:
            metrics = compute_rate_measure(m) if "level_id" in m else compute_index_measure(m)
        except (FredFetchError, ZeroDivisionError, IndexError) as error:
            rows.append({**{k: m[k] for k in ("key", "name", "bank", "role")},
                         "error": f"{type(error).__name__}: {error}",
                         "source_id": m.get("level_id") or m.get("index_id"),
                         "source_url": m["source_url"]})
            continue
        rows.append({
            "key": m["key"], "name": m["name"], "bank": m["bank"], "role": m["role"],
            "yoy": metrics["yoy"], "mom_3m_ann": metrics["mom_3m_ann"], "mom_6m_ann": metrics["mom_6m_ann"],
            "direction": direction(metrics["yoy"], metrics["mom_6m_ann"]),
            "level_bucket": level_bucket(metrics["yoy"], m["target"]),
            "as_of": metrics["as_of"], "source_id": m.get("level_id") or m.get("index_id"),
            "source_url": m["source_url"],
        })
        history_by_key[m["key"]] = metrics.get("history")

    by_key = {r["key"]: r for r in rows if "error" not in r}
    underlying = [r for r in rows if r.get("role") in ("anchor", "underlying") and "error" not in r]
    composite_yoy = _trailing_mean([r["yoy"] for r in underlying], len(underlying)) if underlying else None
    composite_mom = (_trailing_mean([r["mom_6m_ann"] for r in underlying if r["mom_6m_ann"] is not None],
                                    len([r for r in underlying if r["mom_6m_ann"] is not None]))
                     if underlying else None)

    anchor = by_key.get("median_cpi")
    headline = by_key.get("headline_cpi")
    headline_gap = (headline["yoy"] - anchor["yoy"]) if (headline and anchor) else None

    axis = None
    if anchor:
        axis = {
            "anchor": "median_cpi",
            "level_yoy": anchor["yoy"],
            "momentum_6m_ann": anchor["mom_6m_ann"],
            "momentum_3m_ann": anchor["mom_3m_ann"],
            "level_bucket": anchor["level_bucket"],
            "direction": anchor["direction"],
            "read": (f"Underlying inflation {anchor['yoy']:.1f}% YoY ({anchor['level_bucket']}), "
                     f"6m momentum {anchor['mom_6m_ann']:.1f}% ({anchor['direction']})."),
        }

    # Forward overlay — expectations.
    exp_rows: list[dict] = []
    for m in EXPECTATION_MEASURES:
        try:
            metrics = compute_expectation(m)
        except (FredFetchError, IndexError) as error:
            exp_rows.append({"key": m["key"], "name": m["name"],
                             "error": f"{type(error).__name__}: {error}",
                             "source_id": m["id"], "source_url": m["source_url"]})
            continue
        exp_rows.append({"key": m["key"], "name": m["name"], "role": m.get("role", "expectation"),
                         "level": metrics["level"], "change_3m": metrics["change_3m"],
                         "as_of": metrics["as_of"], "source_id": m["id"], "source_url": m["source_url"]})
    exp_by_key = {r["key"]: r for r in exp_rows if "error" not in r}
    forward = exp_by_key.get("forward_5y5y")
    market5 = exp_by_key.get("market_5y")
    anchored = anchoring(forward["level"]) if forward else "n/a"
    exp_gap = (market5["level"] - anchor["yoy"]) if (market5 and anchor) else None
    expectations = {
        "anchored": anchored,
        "gap_vs_realised_pp": exp_gap,
        "note": None,
        "measures": exp_rows,
    }
    if exp_gap is not None:
        if exp_gap < -0.3:
            expectations["note"] = "Market prices inflation to fade below the current underlying pace."
        elif exp_gap > 0.3:
            expectations["note"] = "Market prices inflation above the current underlying pace (upside)."
        else:
            expectations["note"] = "Market expectations in line with the current underlying pace."

    regime_note = None
    if axis and forward:
        regime_note = (f"{axis['level_bucket'].capitalize()} realised (~{axis['level_yoy']:.1f}%), "
                       f"expectations {anchored} (5y5y {forward['level']:.1f}%)"
                       + (f" — {expectations['note'].rstrip('.').lower()}" if expectations["note"] else "") + ".")

    reference_month = anchor["as_of"] if anchor else (underlying[0]["as_of"] if underlying else None)

    # Trend history for the time-series chart: the four underlying gauges plus
    # headline CPI as the volatile-context outlier. Current-vintage (as-revised)
    # 12-month change — descriptive context, not the point-in-time classifier
    # input (the vintage-safe classification lands with the growth axis).
    history_keys = ["median_cpi", "trimmed_cpi", "sticky_core_cpi", "trimmed_pce", "headline_cpi"]
    history_series = []
    for m in RATE_MEASURES + INDEX_MEASURES:
        if m["key"] not in history_keys:
            continue
        pts = history_by_key.get(m["key"])
        if not pts:
            continue
        history_series.append({
            "key": m["key"], "name": m["name"], "role": m["role"],
            "source_id": m.get("level_id") or m.get("index_id"),
            "source_url": m["source_url"], "points": pts,
        })
    history = {
        "months": max((len(s["points"]) for s in history_series), default=0),
        "start": min((s["points"][0][0] for s in history_series), default=None),
        "target_cpi": CPI_TARGET, "target_pce": PCE_TARGET,
        "note": ("Current-vintage (as-revised) 12-month change; descriptive trend "
                 "context, not the point-in-time classifier input."),
        "series": history_series,
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reference_month": reference_month,
        "axis": axis,
        "composite_underlying": {"yoy": composite_yoy, "momentum_6m_ann": composite_mom},
        "headline_gap_pp": headline_gap,
        "history": history,
        "expectations": expectations,
        "nowcast": {"status": "deferred",
                    "note": ("Cleveland Fed inflation nowcast is public but not a stable FRED series; "
                             "needs a dedicated Cleveland-page fetcher before wiring."),
                    "source_url": "https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting"},
        "regime_note": regime_note,
        "measures": rows,
    }


def _fmt(x) -> str:
    return "  n/a" if x is None else f"{x:+5.1f}"


def print_table(result: dict) -> None:
    print("=" * 78)
    print(f"INFLATION AXIS  ·  reference month {result['reference_month']}")
    print("=" * 78)
    print(f"{'Measure':24s} {'YoY':>6s} {'3m*':>6s} {'6m*':>6s}  {'direction':13s} {'vs target':18s}")
    print("-" * 78)
    for r in result["measures"]:
        if "error" in r:
            print(f"{r['name']:24s}  {'— unavailable: ' + r['error']}")
            continue
        tag = "  (context)" if r["role"] == "context" else ("  (anchor)" if r["role"] == "anchor" else "")
        print(f"{r['name']:24s} {_fmt(r['yoy'])} {_fmt(r['mom_3m_ann'])} {_fmt(r['mom_6m_ann'])}  "
              f"{r['direction']:13s} {r['level_bucket']:18s}{tag}")
    print("-" * 78)
    c = result["composite_underlying"]
    if c["yoy"] is not None:
        print(f"{'Composite underlying':24s} {_fmt(c['yoy'])} {'':>6s} {_fmt(c['momentum_6m_ann'])}")
    if result["headline_gap_pp"] is not None:
        print(f"\nHeadline-over-underlying gap: {result['headline_gap_pp']:+.1f} pp "
              f"(headline CPI minus median CPI)")
    if result["axis"]:
        print(f"\nAXIS READ: {result['axis']['read']}")

    exp = result.get("expectations")
    if exp:
        print("\n" + "-" * 78)
        print(f"{'EXPECTATIONS (forward overlay)':24s} {'level':>6s} {'3m chg':>7s}")
        for r in exp["measures"]:
            if "error" in r:
                print(f"{r['name']:24s}  — unavailable: {r['error']}")
                continue
            chg = "   n/a" if r["change_3m"] is None else f"{r['change_3m']:+6.2f}"
            print(f"{r['name']:24s} {_fmt(r['level'])} {chg:>7s}")
        print(f"\nExpectations are {exp['anchored']}"
              + (f"; {exp['note']}" if exp["note"] else ""))

    if result.get("regime_note"):
        print(f"\nREGIME NOTE: {result['regime_note']}")
    if result.get("nowcast", {}).get("status") == "deferred":
        print(f"\nNowcast overlay: deferred — {result['nowcast']['note']}")

    print("\n*3m / 6m are annualised (trailing mean of 1-month-annualised prints; "
          "geometric for context index series).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inflation-axis prototype (growth x inflation compass).")
    parser.add_argument("--quiet", action="store_true", help="write JSON only, no table")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    result = build()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "inflation_axis.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if not args.quiet:
        print_table(result)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
