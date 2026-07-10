"""Growth-axis reading for the growth x inflation regime compass.

The growth axis is the Chicago Fed National Activity Index three-month moving
average (CFNAIMA3), read for both a LEVEL (activity above or below its trend)
and a DIRECTION (accelerating or decelerating), each dead-banded. It is the
complement to the inflation axis in `inflation_axis.py`; together they place the
regime in the growth x inflation quadrant (built in a later stage).

Why CFNAI and not a labour gauge: the CFNAI is a weighted average of 85 monthly
national-activity indicators, roughly two dozen of which are employment series,
so it already embeds labour. Adding a separate labour axis would double-count.
The monthly CFNAI is noisy; the published three-month average (CFNAIMA3) is the
standard smoothed read and is what the Chicago Fed attaches its interpretive
thresholds to.

Units (verified, see VERIFICATION.md): CFNAI is a STANDARDISED index in
standard-deviation units, where zero equals the historical trend rate of growth;
positive is above-trend, negative below-trend. It is NOT a percentage.

Construction
------------
Level      = the latest published CFNAIMA3 value.
Momentum   = the change in CFNAIMA3 over a 3-month and a 6-month window
             (level now minus level N months ago). Because CFNAIMA3 is itself a
             3-month average, the 3-month change compares two non-overlapping
             windows.
Direction  = confirmed sign of the 3-month momentum with a dead-band and
             anti-flip hysteresis (a change to rising/falling requires two
             consecutive beyond-band months; two in-band months revert to
             steady). This keeps the axis from flipping on a single noisy print
             or a revision.

Dead-bands are pre-committed from the Chicago Fed's own published CFNAI-MA3
thresholds, NOT tuned to make the current reading look clean:
  inner +/-0.20  -> the "around trend" band (the Fed's +0.20 "significant
                    likelihood of an expansion" magnitude).
  outer +/-0.70  -> the Fed's published MA3 lines (-0.70 recession-onset after
                    an expansion; +0.70 rising-inflation-pressure deep in an
                    expansion). Used here only to label growth LEVEL as
                    well-below / well-above trend. This dashboard does not make
                    recession or inflation-timing calls -- that is the bear-risk
                    market-regime-dashboard. The outer lines are reference
                    markers, not triggers.

Vintage note (guard 1): CFNAI is heavily revised. This module reads the CURRENT
vintage -- the best available estimate of the present -- and flags it
subject-to-revision. It is descriptive, not a point-in-time backtest; the
vintage-safe (ALFRED) classification belongs to the forward-return study.

Dates via the standard library only (no manual month arithmetic).

Usage:  python scripts/growth_axis.py            # print + write data/growth_axis.json
        python scripts/growth_axis.py --quiet     # write JSON only
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

# Pre-committed bands (standard-deviation units), sourced from the Chicago Fed's
# published CFNAI-MA3 thresholds. See the module docstring and VERIFICATION.md.
LEVEL_INNER = 0.20
LEVEL_OUTER = 0.70
DIR_BAND = 0.10        # 3-month-momentum dead-band (std-dev units)
DIR_WINDOW = 3         # months for the primary momentum read
DIR_CONFIRM = 2        # consecutive beyond-band months required to change direction

AXIS_ID = "CFNAIMA3"
CONTEXT_ID = "CFNAI"
FRED_URL = "https://fred.stlouisfed.org/series/{sid}"
CHICAGO_FED_URL = "https://www.chicagofed.org/research/data/cfnai/current-data"


def _valid_pairs(dates: list[str], values: list[float | None]) -> tuple[list[str], list[float]]:
    pairs = [(d, v) for d, v in zip(dates, values) if v is not None]
    return [d for d, _ in pairs], [v for _, v in pairs]


def _trim_history(dates: list[str], values: list[float], months: int = 120) -> list[list]:
    """Last ``months`` observations as ``[date, rounded_value]`` pairs (2 dp)."""
    pairs = list(zip(dates, values))[-months:]
    return [[d, round(v, 2)] for d, v in pairs]


def momentum(values: list[float], window: int) -> float | None:
    """Change in the series over ``window`` steps: latest minus ``window`` ago."""
    if len(values) <= window:
        return None
    return values[-1] - values[-1 - window]


def level_bucket(x: float | None) -> str:
    if x is None:
        return "n/a"
    if x <= -LEVEL_OUTER:
        return "well below trend"
    if x < -LEVEL_INNER:
        return "below trend"
    if x <= LEVEL_INNER:
        return "around trend"
    if x < LEVEL_OUTER:
        return "above trend"
    return "well above trend"


def confirmed_direction(values: list[float], band: float = DIR_BAND,
                        window: int = DIR_WINDOW, confirm: int = DIR_CONFIRM) -> str:
    """Anti-flip direction label for the latest month.

    Walks the series applying the ``window``-month momentum each step. A change
    to "rising"/"falling" requires ``confirm`` consecutive months whose momentum
    is beyond ``band`` in the same sign; ``confirm`` consecutive in-band months
    revert to "steady". Between those, the prior confirmed label holds, so a
    single noisy print or revision does not flip the axis.
    """
    if len(values) <= window:
        return "n/a"
    label = "steady"
    up = down = flat = 0
    for t in range(window, len(values)):
        m = values[t] - values[t - window]
        if m > band:
            up += 1
            down = flat = 0
        elif m < -band:
            down += 1
            up = flat = 0
        else:
            flat += 1
            up = down = 0
        if up >= confirm:
            label = "rising"
        elif down >= confirm:
            label = "falling"
        elif flat >= confirm:
            label = "steady"
    return label


def build() -> dict:
    errors: list[str] = []
    axis_dates, axis_values = [], []
    ctx_dates, ctx_values = [], []
    try:
        axis_dates, axis_values = _valid_pairs(*fetch_series(AXIS_ID))
    except FredFetchError as error:
        errors.append(f"{AXIS_ID}: {type(error).__name__}: {error}")
    try:
        ctx_dates, ctx_values = _valid_pairs(*fetch_series(CONTEXT_ID))
    except FredFetchError as error:
        errors.append(f"{CONTEXT_ID}: {type(error).__name__}: {error}")

    axis = None
    reference_month = None
    if axis_values:
        level = axis_values[-1]
        reference_month = axis_dates[-1]
        mom3 = momentum(axis_values, DIR_WINDOW)
        mom6 = momentum(axis_values, 6)
        direction = confirmed_direction(axis_values)
        bucket = level_bucket(level)
        axis = {
            "series": AXIS_ID,
            "level": level,
            "level_bucket": bucket,
            "momentum_3m": mom3,
            "momentum_6m": mom6,
            "direction": direction,
            "read": (f"Activity {bucket} (CFNAI-MA3 {level:+.2f}), {direction} — "
                     f"6m momentum {mom6:+.2f}, 3m {mom3:+.2f}."
                     if mom3 is not None and mom6 is not None
                     else f"Activity {bucket} (CFNAI-MA3 {level:+.2f})."),
        }

    # Trend history: the MA3 (the axis) and the monthly CFNAI (faint context, the
    # noise the MA3 removes). Current-vintage / as-revised; descriptive, not the
    # point-in-time classifier input.
    history_series = []
    if axis_values:
        history_series.append({
            "key": "cfnai_ma3", "name": "CFNAI-MA3", "role": "axis",
            "source_id": AXIS_ID, "source_url": FRED_URL.format(sid=AXIS_ID),
            "points": _trim_history(axis_dates, axis_values),
        })
    if ctx_values:
        history_series.append({
            "key": "cfnai", "name": "CFNAI (monthly)", "role": "context",
            "source_id": CONTEXT_ID, "source_url": FRED_URL.format(sid=CONTEXT_ID),
            "points": _trim_history(ctx_dates, ctx_values),
        })
    history = {
        "months": max((len(s["points"]) for s in history_series), default=0),
        "start": min((s["points"][0][0] for s in history_series), default=None),
        "note": ("Current-vintage (as-revised) CFNAI; descriptive trend context, "
                 "not the point-in-time classifier input."),
        "series": history_series,
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reference_month": reference_month,
        "axis": axis,
        "bands": {"level_inner": LEVEL_INNER, "level_outer": LEVEL_OUTER,
                  "direction": DIR_BAND, "direction_window_months": DIR_WINDOW,
                  "direction_confirm_months": DIR_CONFIRM},
        "reference_lines": {
            "recession_onset": -LEVEL_OUTER,
            "expansion_signal": LEVEL_INNER,
            "inflation_pressure": LEVEL_OUTER,
            "note": ("Chicago Fed CFNAI-MA3 interpretive lines, shown as reference "
                     "only. This dashboard does not time recessions or inflation — "
                     "that is the bear-risk market-regime-dashboard."),
        },
        "history": history,
        "source": {
            "source_id": AXIS_ID,
            "source_url": FRED_URL.format(sid=AXIS_ID),
            "secondary_source_url": CHICAGO_FED_URL,
            "as_of": reference_month,
            "units": "standardised index; zero = trend growth, standard-deviation units",
            "notes": ("Current vintage (as-revised), subject to revision. Bands are "
                      "pre-committed from the Chicago Fed's published MA3 thresholds, "
                      "not tuned. See VERIFICATION.md."),
        },
        "errors": errors or None,
    }


def _fmt(x) -> str:
    return "  n/a" if x is None else f"{x:+6.2f}"


def print_table(result: dict) -> None:
    print("=" * 72)
    print(f"GROWTH AXIS  ·  reference month {result['reference_month']}")
    print("=" * 72)
    axis = result.get("axis")
    if not axis:
        print("Axis unavailable:", result.get("errors"))
        return
    print(f"{'CFNAI-MA3 level':22s} {_fmt(axis['level'])}   ({axis['level_bucket']})")
    print(f"{'3-month momentum':22s} {_fmt(axis['momentum_3m'])}")
    print(f"{'6-month momentum':22s} {_fmt(axis['momentum_6m'])}")
    print(f"{'Direction (confirmed)':22s}   {axis['direction']}")
    b = result["bands"]
    print(f"\nBands: level dead-band +/-{b['level_inner']}, outer +/-{b['level_outer']}; "
          f"direction +/-{b['direction']} over {b['direction_window_months']}m, "
          f"confirm {b['direction_confirm_months']}m.")
    print(f"\nREAD: {axis['read']}")
    if result.get("errors"):
        print("\nErrors:", result["errors"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Growth-axis reading (growth x inflation compass).")
    parser.add_argument("--quiet", action="store_true", help="write JSON only, no table")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    result = build()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "growth_axis.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if not args.quiet:
        print_table(result)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
