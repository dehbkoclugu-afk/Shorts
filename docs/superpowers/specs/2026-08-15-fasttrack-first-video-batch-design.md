# FastTrack First Video Batch Design

**Date:** 2026-08-15  
**Status:** Approved  
**Repository:** `dehbkoclugu-afk/Shorts`  
**Branch:** `agent/fasttrack-growth`

## 1. Outcome

Extend the existing FastTrack content factory so it produces the first three publishable Turkish vertical MP4 videos, not only storyboard cards.

The batch must remain reusable across TikTok, Instagram Reels, YouTube Shorts, Facebook Reels, and Pinterest without platform watermarks.

## 2. Selected concepts

| Content ID | Theme | Primary hook |
| --- | --- | --- |
| FT-006 | Product feature demo | Bir oruç zamanlayıcısı sadece geri sayım olmamalı. |
| FT-011 | Beginner 12:12 setup | İlk 12:12 planını 10 saniyede kur. |
| FT-013 | Private, account-free tracking | Oruç takibi için hesap açmak istemiyor musun? |

All videos are Turkish for the initial Türkiye launch. English and additional locales remain outside this first batch.

## 3. Creative direction

- Duration: 15–20 seconds.
- Canvas: 1080×1920, 9:16.
- Visual style: dark navy surfaces, FastTrack coral accents, white high-contrast captions.
- Footage style: faceless hand-and-phone presentation plus genuine FastTrack screen captures.
- Tone: calm, direct, encouraging, and product-led.
- No body transformation imagery, fake testimonial, quantified weight-loss outcome, or medical promise.
- The master MP4 must contain no platform watermark.

Each video follows this timing model:

1. 0–2 seconds: problem-led hook.
2. 2–12 seconds: genuine FastTrack screen demonstration.
3. 12–16 seconds: one concise benefit.
4. 16–20 seconds: FastTrack logo and Google Play call to action.

## 4. Video briefs

### FT-006 — Product demo

Sequence: fasting timer → hydration → meal tracking → weekly progress.

Benefit: the complete fasting routine is visible without switching between separate apps.

CTA: “FastTrack’i Google Play’den indir.”

### FT-011 — First 12:12 plan

Sequence: choose 12:12 → set the start time → start the timer.

Benefit: a beginner can create a repeatable, gentle starting routine quickly.

CTA: “İlk planını FastTrack’te başlat.”

### FT-013 — Privacy

Sequence: open the app → begin without account creation → show the applicable local-data/privacy message.

Benefit: simple tracking without mandatory account creation.

CTA: “Özel ve sade takip için FastTrack’i dene.”

Privacy copy must match the current production app and published privacy policy. The renderer must not invent or broaden a privacy claim.

## 5. Production architecture

The first version uses the repository’s existing Python, MoviePy, Edge TTS, subtitle timing, validation, and GitHub Actions patterns. No external UGC provider is required.

Data flow:

1. Read the approved FastTrack content record.
2. Resolve the required genuine app screen captures.
3. Generate Turkish narration and timed captions.
4. Compose a clean 1080×1920 master MP4.
5. Run deterministic health-claim and disclosure checks.
6. Validate duration, resolution, audio stream, video stream, and file integrity.
7. Export the MP4, thumbnail, captions, and channel metadata as a GitHub Actions artifact.
8. Keep publishing manual and human-approved.

## 6. Failure handling

- Missing required screen captures are blocking; the renderer must not silently substitute unrelated or fabricated UI.
- A failed concept must report its content ID and reason.
- One failed video must not suppress successful outputs from the other concepts.
- Compliance failure blocks that asset from the publish package.
- Rendering or validation failures must produce a failing workflow status rather than a misleading green result.
- Temporary narration or render files must not be committed.

## 7. Distribution

The same clean master MP4 is reused across channels. Copy and tracking links remain platform-specific.

Initial schedule:

| Day | Asset |
| --- | --- |
| 1 | FT-006 product demo |
| 2 | FT-011 beginner setup |
| 3 | FT-013 privacy advantage |

TikTok remains manual/draft publishing. Reddit remains human-only and is not a destination for this three-video automated package. Other channels receive their existing channel-coded Play Store link and localized caption export.

## 8. Measurement

Primary signals:

- three-second retention;
- completion rate;
- saves and shares;
- Play Store clicks;
- installs;
- attributable Premium purchases.

The purpose of the batch is to identify which message produces qualified store traffic, not to optimize for vanity views. After three days, the strongest concept receives two new hook variants.

## 9. Plugin and provider decision

Do not install or depend on HeyGen, Higgsfield, or another UGC provider for this batch. The faceless hand-and-phone direction avoids synthetic testimonial risk and keeps production repeatable.

A UGC provider may be introduced only after an organic concept wins. Any AI-assisted creator demonstration must be disclosed as dramatized or AI-assisted and must not be presented as a genuine user result.

## 10. Testing

Required automated coverage:

- correct concept selection for FT-006, FT-011, and FT-013;
- missing-screen failure;
- duration and 1080×1920 validation;
- audio/video stream presence;
- caption safe-area bounds;
- prohibited-claim blocking;
- output isolation when one concept fails;
- deterministic artifact naming with content ID and locale.

Required human review:

- every shown screen matches the production Android app;
- captions remain readable and inside safe zones;
- narration pronunciation is acceptable;
- CTA and Play Store link are correct;
- no misleading health, weight-loss, privacy, or testimonial claim is present.

## 11. Definition of done

- Three Turkish 1080×1920 MP4s render successfully.
- Each video is 15–20 seconds and contains genuine FastTrack UI.
- Each asset has narration, timed captions, thumbnail, metadata, and channel-coded Play Store links.
- All automated checks pass.
- The workflow uploads a reviewable artifact.
- Publishing remains manual until the user approves each final video and platform credentials are configured.
