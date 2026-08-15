# FastTrack Content Factory

This isolated system creates safe, reviewable, bilingual launch content for the live FastTrack Android app.

Google Play: <https://play.google.com/store/apps/details?id=com.dehbkoclugu.fasttrack>

## What version one does

- validates 14 Turkish/English launch concepts;
- blocks unsafe or insufficiently qualified health claims;
- builds channel-specific Google Play attribution links;
- exports JSON, CSV, Markdown review, and Higgsfield UGC briefs;
- renders FastTrack-branded 1080x1920 storyboard cards;
- keeps publishing manual and dry-run by default.

It does not use the legacy WAR SHORTS schedules, prompts, accounts, or credentials.

## First Turkish video batch

The first MP4 batch uses `FT-006`, `FT-011`, and `FT-013`. Source screens are
captured from the real FastTrack Flutter widget tree in Turkish dark mode and
stored under `fasttrack/assets/screens/tr/`. They must be checked against the
current production Android app before publishing.

Install the local render dependencies:

```bash
python -m pip install "Pillow>=10.0.0" "edge-tts>=7,<8"
```

Build the three selected records and render the clean 1080×1920 masters:

```bash
python -m fasttrack.src.planner --locales tr \
  --content-id FT-006 --content-id FT-011 --content-id FT-013 \
  --output fasttrack/output
python -m fasttrack.src.video_renderer \
  --pack fasttrack/output/content-pack.json \
  --output fasttrack/output/videos
python -m fasttrack.src.video_validation fasttrack/output/videos/*.mp4
```

The output contains MP4 masters, thumbnails, a structured build report, the
content pack, captions, and channel-coded Play links. Videos contain no social
platform watermark. Publishing stays manual and requires visual, copy, link,
health-claim, and privacy review.

## Local usage

From the repository root:

```bash
python -m unittest discover -s fasttrack/tests -v
python -m fasttrack.src.planner --output fasttrack/output
python -m fasttrack.src.storyboards \
  --pack fasttrack/output/content-pack.json \
  --output fasttrack/output/storyboards
python -m fasttrack.src.report \
  --calendar fasttrack/output/content-calendar.csv \
  --output fasttrack/output/weekly-report.md
```

Generate a smaller review batch:

```bash
python -m fasttrack.src.planner --count 2 --locales tr,en --output fasttrack/output
```

Generate selected concepts:

```bash
python -m fasttrack.src.planner \
  --content-id FT-001 \
  --content-id FT-013 \
  --output fasttrack/output
```

## Review package

The output contains:

- `content-pack.json`: normalized copy and channel links;
- `content-calendar.csv`: production ledger seed;
- `review.md`: item-by-item human approval checklist;
- `higgsfield-briefs.md`: three safe creator-style briefs;
- `storyboards/*.png`: branded vertical review frames;
- `platforms/youtube.json`: Shorts titles, descriptions, and briefs;
- `platforms/instagram.json`: Reels, carousel slides, captions, and alt text;
- `platforms/tiktok.json`: vertical-video drafts and profile-link instructions;
- `platforms/facebook.json`: Reels/feed-video copy;
- `platforms/pinterest.json`: Pin titles, descriptions, and alt text;
- `platforms/threads.json` and `platforms/x.json`: length-limited text posts;
- `platforms/reddit.json`: human-only helpful-post outlines with disclosure;
- `platforms/creator.json`: creator/UGC talking points and prohibited claims;
- `platforms/seo.json`: article titles, metadata, and outlines;
- `platforms/distribution-summary.md`: priority and publishing mode matrix;
- `weekly-report.md`: production baseline.

## Publishing safety

The publishing workflow requires both explicit approval and dry-run mode. Live publishing intentionally fails until all of the following are complete:

1. Dedicated FastTrack social accounts exist.
2. Fresh FastTrack-only credentials are configured.
3. Each platform adapter is reviewed against current platform rules.
4. A generated artifact has passed human copy and visual review.
5. The health/wellness disclosures are correct for the destination.

Do not reuse the suspended legacy YouTube identity or any WAR SHORTS token.

YouTube is not the system's center. Every localized content item produces exports for ten acquisition channels. TikTok is draft-only, Reddit is human-only, and creator outreach requires disclosure; Instagram, Facebook, Pinterest, Threads, X, SEO, and YouTube can gain reviewed adapters independently.

## Language rollout

Launch content is produced in Turkish and English. Winning concepts can then be translated and reviewed for Spanish, Portuguese, German, and French. The configuration already reserves those locales, but unchecked machine translations must not be published.

## Metrics

Use the stable master ID (`FT-001`) and localized asset ID (`FT-001-tr`) in every asset and export. Acquisition starts with Google Play Install Referrer links, Play Console reports, platform exports, and RevenueCat reporting. Adding a new in-app analytics SDK is outside this system and would require a separate privacy/Data Safety review.
