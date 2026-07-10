"""Build docs/index.html by injecting data/ JSON into template.html.

template.html is the single source of truth for the UI and must stay under
200 KB (project CLAUDE.md); this script fails loudly if it grows past that.
docs/ is generated output — never edit it by hand. The whole data/ tree is
also copied to docs/data/ so the built page can fetch anything not inlined at
runtime, matching the fetch-fallback paths used during development.

This mirrors market-regime-dashboard/scripts/build.py verbatim in mechanism
(same DATA_INJECT marker and escaping); the payload differs because this
compass currently emits only the inflation axis. As further groups are built
(growth axis, quadrant, asset read) they are added to PAYLOAD below.

No date arithmetic here — generated_at is a UTC timestamp only.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template.html"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
MARKER = "null; /*DATA_INJECT*/"
TEMPLATE_LIMIT_BYTES = 200_000

# Each entry: payload_key -> (filename, required). Optional groups that do not
# exist yet are simply skipped, so the pipeline runs cleanly through the build.
DATA_GROUPS = {
    "inflation_axis": ("inflation_axis.json", True),
    # "growth_axis":  ("growth_axis.json", False),   # added in a later stage
    # "quadrant":     ("quadrant.json", False),
    # "asset_read":   ("asset_read.json", False),
}


def load_json(name: str) -> dict:
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def build_payload() -> dict:
    payload: dict = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for key, (filename, required) in DATA_GROUPS.items():
        path = DATA_DIR / filename
        if path.exists():
            payload[key] = load_json(filename)
        elif required:
            raise SystemExit(f"Required data file missing: {path}")
        else:
            payload[key] = None
    return payload


def main() -> int:
    template_size = TEMPLATE.stat().st_size
    if template_size >= TEMPLATE_LIMIT_BYTES:
        raise SystemExit(
            f"template.html is {template_size:,} bytes, at or above the "
            f"{TEMPLATE_LIMIT_BYTES:,}-byte limit. Reduce it before building."
        )

    html = TEMPLATE.read_text(encoding="utf-8")
    if html.count(MARKER) != 1:
        raise SystemExit(
            f"Expected exactly one injection marker '{MARKER}' in template.html, "
            f"found {html.count(MARKER)}."
        )

    payload = build_payload()
    # "</" is escaped so no JSON string can terminate the surrounding <script>
    # element early; "<\/" is an identical string once parsed as JSON.
    injected = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace(MARKER, injected + ";")

    DOCS_DIR.mkdir(exist_ok=True)
    output = DOCS_DIR / "index.html"
    output.write_text(html, encoding="utf-8")
    shutil.copytree(DATA_DIR, DOCS_DIR / "data", dirs_exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"template.html: {template_size:,} bytes (limit {TEMPLATE_LIMIT_BYTES:,})")
    print(f"docs/index.html: {output.stat().st_size:,} bytes")
    print("docs/data/: refreshed from data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
