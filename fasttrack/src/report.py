"""Create a baseline FastTrack content production report."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def _section(title: str, values: Counter) -> list[str]:
    lines = [f"## {title}", ""]
    lines.extend(f"- {key}: {count}" for key, count in sorted(values.items()))
    lines.append("")
    return lines


def build_report(rows: list[dict]) -> str:
    lines = [
        "# FastTrack Weekly Content Report",
        "",
        f"Localized assets: **{len(rows)}**",
        "",
    ]
    lines.extend(_section("Locales", Counter(row["locale"] for row in rows)))
    lines.extend(_section("Series", Counter(row["series"] for row in rows)))
    lines.extend(_section("Formats", Counter(row["format"] for row in rows)))
    lines.extend(
        [
            "## Measurement status",
            "",
            "- Production baseline generated.",
            "- Add platform export rows after publishing to calculate reach and conversion.",
            "- Do not infer performance from a successful workflow alone.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.calendar.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(rows), encoding="utf-8")
    print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

