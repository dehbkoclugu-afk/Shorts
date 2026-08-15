"""CLI for generating an offline FastTrack content review pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fasttrack.src.content_pack import build_pack, write_pack


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topics", type=Path, default=ROOT / "content" / "topics.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument("--locales", default="tr,en")
    parser.add_argument("--count", type=int)
    parser.add_argument("--content-id", action="append", dest="content_ids")
    args = parser.parse_args()

    topic_payload = json.loads(args.topics.read_text(encoding="utf-8"))
    locales = [item.strip() for item in args.locales.split(",") if item.strip()]
    records = build_pack(
        topic_payload["topics"],
        locales=locales,
        count=args.count,
        content_ids=set(args.content_ids) if args.content_ids else None,
    )
    write_pack(records, args.output)
    print(f"Generated {len(records)} localized assets in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

