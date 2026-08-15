"""Build deterministic Google Play campaign links for FastTrack content."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ID_PATTERN = re.compile(r"^FT-\d{3}$")


def _load_json(name: str) -> dict:
    with (ROOT / "config" / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def build_play_url(channel: str, locale: str, content_id: str) -> str:
    """Return a Play Store URL with an encoded Install Referrer payload."""
    brand = _load_json("brand.json")
    channel_config = _load_json("channels.json")
    channels = channel_config["channels"]

    if channel not in channels:
        raise ValueError(f"Unknown channel: {channel}")
    supported_locales = brand["launch_locales"] + brand["expansion_locales"]
    if locale not in supported_locales:
        raise ValueError(f"Unsupported locale: {locale}")
    if not CONTENT_ID_PATTERN.fullmatch(content_id):
        raise ValueError(f"Malformed content ID: {content_id}")

    referrer = urlencode(
        {
            "utm_source": channel,
            "utm_medium": channels[channel]["medium"],
            "utm_campaign": f"{channel_config['campaign']}_{locale}",
            "utm_content": content_id.lower(),
        }
    )
    return f"{brand['play_store_url']}&{urlencode({'referrer': referrer})}"

