"""Deterministic health-claim checks for FastTrack marketing copy."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    matched: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _load_rules() -> dict:
    with (ROOT / "config" / "claims.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _first_match(patterns: list[str], text: str) -> re.Match | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.UNICODE)
        if match:
            return match
    return None


def check_text(text: str) -> list[Finding]:
    """Return blocking findings for unsafe or insufficiently qualified copy."""
    rules = _load_rules()
    findings: list[Finding] = []

    for rule in rules["blocking_rules"]:
        match = _first_match(rule["patterns"], text)
        if match:
            findings.append(
                Finding(
                    rule_id=rule["id"],
                    severity="error",
                    matched=match.group(0),
                    message=f"Blocked marketing claim: {rule['id']}",
                )
            )

    lowered = text.casefold()
    for rule in rules["disclaimer_rules"]:
        trigger = _first_match(rule["patterns"], text)
        has_disclaimer = any(
            required.casefold() in lowered for required in rule["required_any"]
        )
        if trigger and not has_disclaimer:
            findings.append(
                Finding(
                    rule_id=rule["id"],
                    severity="error",
                    matched=trigger.group(0),
                    message=(
                        "Metabolic-stage copy requires general-estimate or "
                        "person-to-person-variation language."
                    ),
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    args = parser.parse_args()

    text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    findings = check_text(text)
    print(json.dumps([item.to_dict() for item in findings], ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

