"""Normalize approved FastTrack topics into reviewable campaign records."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from fasttrack.src.campaign_links import build_play_url
from fasttrack.src.compliance import check_text


ROOT = Path(__file__).resolve().parents[1]


class UnsafeContentError(ValueError):
    """Raised when any localized item fails the deterministic safety gate."""


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_pack(
    topics: list[dict],
    *,
    locales: list[str] | None = None,
    count: int | None = None,
    content_ids: set[str] | None = None,
) -> list[dict]:
    """Build deterministic localized records and abort on unsafe copy."""
    brand = _load_json(ROOT / "config" / "brand.json")
    channel_config = _load_json(ROOT / "config" / "channels.json")
    caption_templates = _load_json(ROOT / "templates" / "captions.json")[
        "templates"
    ]
    selected_locales = locales or brand["launch_locales"]
    supported = set(brand["launch_locales"] + brand["expansion_locales"])
    unknown = set(selected_locales) - supported
    if unknown:
        raise ValueError(f"Unsupported locales: {', '.join(sorted(unknown))}")

    ordered_topics = sorted(topics, key=lambda item: item["id"])
    if content_ids:
        ordered_topics = [item for item in ordered_topics if item["id"] in content_ids]
    if count is not None:
        if count < 1:
            raise ValueError("count must be at least 1")
        ordered_topics = ordered_topics[:count]

    records: list[dict] = []
    seen_ids: set[str] = set()
    for topic in ordered_topics:
        master_id = topic["id"]
        if master_id in seen_ids:
            raise ValueError(f"Duplicate content ID: {master_id}")
        seen_ids.add(master_id)

        for locale in selected_locales:
            if locale not in topic["locales"]:
                raise ValueError(f"{master_id} is missing locale: {locale}")
            copy = topic["locales"][locale]
            safety_text = "\n".join(
                copy.get(field, "")
                for field in ("hook", "script", "cta", "safety_note")
            )
            findings = check_text(safety_text)
            if findings:
                rules = ", ".join(sorted({item.rule_id for item in findings}))
                raise UnsafeContentError(f"{master_id}-{locale} failed: {rules}")

            caption = caption_templates[locale].format(**copy)
            play_links = {
                channel: build_play_url(channel, locale, master_id)
                for channel in channel_config["channels"]
            }
            records.append(
                {
                    "asset_id": f"{master_id}-{locale}",
                    "master_id": master_id,
                    "locale": locale,
                    "series": topic["series"],
                    "format": topic["format"],
                    "hook": copy["hook"],
                    "script": copy["script"],
                    "cta": copy["cta"],
                    "safety_note": copy["safety_note"],
                    "caption": caption,
                    "compliance": "passed",
                    "play_links": play_links,
                }
            )

    return records


def write_pack(records: list[dict], output_dir: Path) -> None:
    """Write JSON, CSV, and Markdown artifacts for human review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "record_count": len(records), "records": records}
    (output_dir / "content-pack.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (output_dir / "content-calendar.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "asset_id",
                "master_id",
                "locale",
                "series",
                "format",
                "hook",
                "compliance",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow({field: record[field] for field in writer.fieldnames})

    review_lines = [
        "# FastTrack Content Review",
        "",
        f"Localized assets: **{len(records)}**",
        "",
        "Check the copy, product accuracy, disclosure, and destination link before approval.",
        "",
    ]
    for record in records:
        review_lines.extend(
            [
                f"## {record['asset_id']} — {record['series']}",
                "",
                f"**Hook:** {record['hook']}",
                "",
                record["script"],
                "",
                f"**CTA:** {record['cta']}",
                "",
                f"**Safety:** {record['safety_note']}",
                "",
                f"**YouTube Play link:** {record['play_links']['youtube']}",
                "",
                "- [ ] Copy approved",
                "- [ ] Product visuals approved",
                "- [ ] Link checked",
                "",
            ]
        )
    (output_dir / "review.md").write_text(
        "\n".join(review_lines).rstrip() + "\n", encoding="utf-8"
    )

    ugc = _load_json(ROOT / "templates" / "ugc.json")
    ugc_lines = [
        "# FastTrack Higgsfield UGC Briefs",
        "",
        f"**TR disclosure:** {ugc['disclosure']['tr']}",
        "",
        f"**EN disclosure:** {ugc['disclosure']['en']}",
        "",
    ]
    for brief in ugc["briefs"]:
        ugc_lines.extend(
            [
                f"## {brief['id']} — {brief['persona']}",
                "",
                f"Duration: {brief['duration_seconds']} seconds",
                "",
                brief["visual"],
                "",
                *[f"- {beat}" for beat in brief["structure"]],
                "",
            ]
        )
    (output_dir / "higgsfield-briefs.md").write_text(
        "\n".join(ugc_lines).rstrip() + "\n", encoding="utf-8"
    )
