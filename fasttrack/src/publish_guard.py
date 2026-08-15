"""Fail-closed approval gate for future FastTrack publishing adapters."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CONTENT_ID_PATTERN = re.compile(r"^FT-\d{3}$")


def validate_publish_request(*, approved: bool, dry_run: bool, content_id: str) -> dict:
    if not approved:
        raise ValueError("Explicit human approval is required")
    if not CONTENT_ID_PATTERN.fullmatch(content_id):
        raise ValueError(f"Malformed content ID: {content_id}")
    if not dry_run:
        raise RuntimeError(
            "Live publishing is not configured; add fresh FastTrack channel credentials "
            "and a reviewed publisher adapter first"
        )
    return {
        "content_id": content_id,
        "approved": True,
        "dry_run": True,
        "status": "dry-run-approved",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = validate_publish_request(
        approved=args.approved,
        dry_run=args.dry_run,
        content_id=args.content_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Dry-run publish manifest written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

