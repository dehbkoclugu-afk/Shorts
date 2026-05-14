"""
adhd_script_gen.py — ADHD focus music videoları için Gemini ile metadata üretir.

Üretilen alanlar:
  - title: YouTube başlığı (≤60 karakter, ilk 35'te 40Hz+ADHD+keyword)
  - hook_line: Ekranda büyük metin (≤12 kelime)
  - hook_subtext: Hook altı metin (≤8 kelime)
  - description: SEO açıklaması + medical disclaimer
  - tags: ADHD, 40Hz, Brown Noise garantili
  - thumbnail_text: 2-4 kelime ALL CAPS
  - cta_line: Video sonu CTA
"""

import os
import json
import random
import re
import time
import requests

from freq_script_gen import generate_localizations  # Lokalizasyon tekrar yazılmaz

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"]

MEDICAL_DISCLAIMER = (
    "⚠️ This content is for relaxation and focus support purposes only. "
    "It is not medical advice or a substitute for professional ADHD treatment."
)


def _call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY ortam değişkeni eksik.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.85, "maxOutputTokens": max_tokens},
    }
    last_err = None
    for model in GEMINI_MODELS:
        url = GEMINI_API_BASE.format(model=model) + f"?key={api_key}"
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(2 ** attempt)
    raise RuntimeError(f"Tüm Gemini modelleri başarısız: {last_err}")


def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"JSON bulunamadı:\n{text[:400]}")


ADHD_PROMPT_TEMPLATE = """You are a viral YouTube Shorts creator for science-backed ADHD focus music. Your brand is "honest neuroscience" — no pseudoscience, only peer-reviewed claims. Study channels like Brain.fm and Mind Amend, then create better content.

Frequency: {beat_hz}Hz gamma binaural beat (carrier {carrier_hz}Hz)
Topic: {name}
Benefit: {benefit}
Noise Type: {noise_type} noise
Science Reference: {science_ref}
Mood: {mood}

HOOK INSPIRATION:
{hooks_str}

━━━ TITLE RULES (CRITICAL) ━━━
- ≤60 chars total
- First 35 chars MUST contain: "40Hz" + "ADHD" + one core keyword
- Format options:
  * "40Hz Gamma | ADHD [Benefit] | Brown Noise | #Shorts"
  * "40Hz ADHD [Keyword] | Brown Noise | Science-Backed"
  * "ADHD {beat_hz}Hz Focus | [Outcome] | Brown Noise"
- NEVER use: "DNA repair", "miracle", "cures", "treats ADHD"
- ALWAYS scientific but accessible: "Science-Backed", "Nigg 2024", "MIT Research", "Gamma Waves"
- End with "| #Shorts" or "#ADHDFocus" to signal Shorts format

━━━ HOOK LINE ━━━
≤12 words. Creates instant PHYSICAL response in an ADHD brain. Options:
- "Your ADHD brain on 40Hz gamma — feel the shift starting now."
- "40Hz is activating your prefrontal cortex right now."
- "Scientists found this exact frequency helps ADHD focus. Let it work."
- "ADHD attention deficit ends here. 40Hz gamma — 55 seconds."
Avoid generic: "this frequency will help you", "feel relaxed"

━━━ HOOK SUBTEXT ━━━
≤8 words. Urgency/credibility:
- "Nigg 2024 meta-analysis: g=0.249 effect size."
- "MIT Picower Lab validated. Headphones required."
- "Peer-reviewed. Not placebo. Try it."

━━━ THUMBNAIL TEXT ━━━
2-4 ALL CAPS words. Dark techy style:
ADHD GAMMA | 40HZ FOCUS | BRAIN RESET | DEEP WORK | BROWN NOISE | HYPERFOCUS

━━━ CTA LINE ━━━
- "Follow — science-backed ADHD focus music daily."
- "Subscribe. Your ADHD brain deserves this."
- "Follow for frequencies that neuroscience actually supports."

━━━ DESCRIPTION ━━━
80-110 words. Structure:
1. What 40Hz gamma does to the ADHD brain (physiological, specific)
2. Cite the science: mention {science_ref}
3. "🎧 Use headphones — binaural beats require stereo."
4. Best use cases for ADHD (2-3 specific)
5. Medical disclaimer (VERBATIM): "{disclaimer}"
6. Follow CTA
End with hashtags: #ADHDFocus #40HzGamma #BrownNoise #GammaWaves #BinauralBeats #ADHD #DeepWork #Shorts

━━━ TAGS ━━━
12-15 tags. MUST include ALL of:
- "ADHD", "ADHD Focus", "40Hz", "40Hz Gamma", "Brown Noise"
- "{beat_hz}Hz Binaural", "Gamma Waves", "Binaural Beats"
- Science keywords: "Nigg 2024" or "MIT Research" or "Gamma Entrainment"
- Use-case: "Deep Work", "Coding Focus", "Study Music", "Pomodoro" (pick relevant)
- "ADHD Brain", "Neuroscience", "Focus Music"

Output ONLY valid JSON:
{{
  "title": "...",
  "hook_line": "...",
  "hook_subtext": "...",
  "thumbnail_text": "...",
  "cta_line": "...",
  "description": "...",
  "tags": ["...", "..."]
}}
"""


def generate_adhd_script(topic: dict) -> dict:
    """
    ADHD topic için Gemini metadata üretir.

    Args:
        topic: adhd_topic_pool.json'dan bir kayıt

    Returns:
        Üretilen metadata dict
    """
    hooks_str = "\n".join(f"- {h}" for h in topic.get("hooks", []))

    prompt = ADHD_PROMPT_TEMPLATE.format(
        beat_hz=topic.get("beat_hz", 40),
        carrier_hz=topic.get("carrier_hz", 200),
        name=topic["name"],
        benefit=topic["benefit"],
        noise_type=topic.get("noise_type", "brown"),
        science_ref=topic.get("science_ref", "Nigg 2024"),
        mood=topic["mood"],
        hooks_str=hooks_str,
        disclaimer=MEDICAL_DISCLAIMER,
    )

    print(f"[adhd_script_gen] {topic['name']} için Gemini çağrılıyor...")
    raw = _call_gemini(prompt)
    script = _extract_json(raw)

    # Eksik alanlar için default'lar
    script.setdefault("title", topic["title_name"])
    script.setdefault("hook_line", random.choice(topic["hooks"]))
    script.setdefault("hook_subtext", "Headphones required for binaural effect.")
    script.setdefault("thumbnail_text", "ADHD GAMMA")
    script.setdefault("cta_line", "Follow — science-backed ADHD focus music daily.")
    script.setdefault("tags", topic["tags"])
    script.setdefault("description", topic["description"])

    # Medical disclaimer description'da yoksa ekle
    if MEDICAL_DISCLAIMER not in script.get("description", ""):
        script["description"] = script["description"].rstrip() + "\n\n" + MEDICAL_DISCLAIMER

    # Topic meta
    script["beat_hz"] = topic.get("beat_hz", 40)
    script["carrier_hz"] = topic.get("carrier_hz", 200)
    script["noise_type"] = topic.get("noise_type", "brown")
    script["topic_name"] = topic["name"]
    script["short_benefit"] = topic["short_benefit"]
    script["mood"] = topic["mood"]
    script["science_ref"] = topic.get("science_ref", "Nigg 2024")
    script["pexels_keywords"] = topic.get("pexels_keywords", [])

    print(f"[adhd_script_gen] Başlık: {script['title']}")
    print(f"[adhd_script_gen] Hook: {script['hook_line']}")
    return script


def save_adhd_script(script: dict, path: str = "output/adhd_script.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    print(f"[adhd_script_gen] Script kaydedildi: {path}")
