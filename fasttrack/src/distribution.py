"""Create channel-specific FastTrack distribution records."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_channels() -> dict:
    return json.loads(
        (ROOT / "config" / "channels.json").read_text(encoding="utf-8")
    )["channels"]


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" .,:;-") + "…"


def _post_with_link(text: str, link: str, limit: int) -> str:
    available = limit - len(link) - 2
    return f"{_shorten(text, available)}\n\n{link}"


def _common(record: dict, channel: str, config: dict) -> dict:
    return {
        "asset_id": record["asset_id"],
        "master_id": record["master_id"],
        "locale": record["locale"],
        "series": record["series"],
        "channel": channel,
        "priority": config["priority"],
        "publishing_mode": config["publishing_mode"],
        "content_types": config["content_types"],
        "play_store_url": record["play_links"][channel],
        "compliance": record["compliance"],
    }


def _channel_record(record: dict, channel: str, config: dict) -> dict:
    item = _common(record, channel, config)
    link = item["play_store_url"]
    caption_with_link = f"{record['caption']}\n\n{link}"

    if channel == "youtube":
        item.update(
            title=_shorten(record["hook"], 100),
            description=caption_with_link,
            video_brief=record["script"],
        )
    elif channel == "instagram":
        item.update(
            caption=caption_with_link,
            reel_hook=record["hook"],
            carousel_slides=[record["hook"], record["script"], record["cta"]],
            alt_text=_shorten(record["script"], 300),
        )
    elif channel == "tiktok":
        item.update(
            caption=_shorten(record["caption"], 2200),
            video_brief=record["script"],
            profile_link_note="Use the channel-coded Play URL in the profile or campaign landing link.",
        )
    elif channel == "facebook":
        item.update(caption=caption_with_link, reel_hook=record["hook"])
    elif channel == "pinterest":
        item.update(
            title=_shorten(record["hook"], 100),
            description=_shorten(f"{record['script']} {record['cta']}", 500),
            alt_text=_shorten(record["script"], 300),
        )
    elif channel == "threads":
        item.update(post_text=_post_with_link(record["hook"], link, 500))
    elif channel == "x":
        item.update(post_text=_post_with_link(record["hook"], link, 280))
    elif channel == "reddit":
        item.update(
            title=_shorten(record["hook"], 160),
            helpful_post_outline=[
                "Answer the community question before mentioning the app.",
                record["script"],
                record["safety_note"],
                "Disclose the relationship to FastTrack and add the link only when relevant.",
            ],
            human_review_required=True,
        )
    elif channel == "creator":
        item.update(
            creator_hook=record["hook"],
            talking_points=[record["script"], record["cta"], record["safety_note"]],
            disclosure_required=True,
            prohibited_claim="Do not claim personal weight loss or a medical outcome.",
        )
    elif channel == "seo":
        item.update(
            title=_shorten(record["hook"], 60),
            meta_description=_shorten(record["script"], 160),
            article_outline=[
                record["hook"],
                record["script"],
                record["safety_note"],
                record["cta"],
            ],
        )
    else:
        raise ValueError(f"Unsupported distribution channel: {channel}")
    return item


def build_distribution(records: list[dict]) -> dict[str, list[dict]]:
    """Return one channel-specific record set for every configured channel."""
    channels = _load_channels()
    return {
        channel: [_channel_record(record, channel, config) for record in records]
        for channel, config in channels.items()
    }


def write_distribution_exports(
    exports: dict[str, list[dict]], output_dir: Path
) -> list[Path]:
    """Write platform JSON files and a compact operator summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    summary = ["# FastTrack Distribution Summary", ""]
    for channel, records in exports.items():
        path = output_dir / f"{channel}.json"
        path.write_text(
            json.dumps(
                {"version": 1, "channel": channel, "records": records},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        paths.append(path)
        mode = records[0]["publishing_mode"] if records else "n/a"
        priority = records[0]["priority"] if records else "n/a"
        summary.append(
            f"- **{channel}**: {len(records)} assets · priority {priority} · `{mode}`"
        )
    summary.extend(
        [
            "",
            "Reddit and creator outreach always require a human. TikTok remains draft-only. ",
            "No channel is treated as successful solely because an export workflow is green.",
            "",
        ]
    )
    summary_path = output_dir / "distribution-summary.md"
    summary_path.write_text("\n".join(summary), encoding="utf-8")
    paths.append(summary_path)
    return paths

