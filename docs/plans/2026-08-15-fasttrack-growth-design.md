# FastTrack Growth System Design

**Date:** 2026-08-15  
**Status:** Approved  
**Owner:** FastTrack  
**Source repository:** `dehbkoclugu-afk/Shorts`  
**Implementation branch:** `agent/fasttrack-growth`

## 1. Outcome

Build a human-approved content factory that turns one FastTrack content idea into reusable, localized assets for YouTube Shorts, Instagram Reels, TikTok, Facebook Reels, Pinterest, short-form text, and Google Play acquisition campaigns.

The first 90-day north-star metric is qualified Google Play installs. Premium conversion is the secondary metric.

## 2. Positioning

FastTrack is positioned as the calm, private, sustainable alternative to aggressive fasting and weight-loss products.

Primary promise:

> Oruçta mükemmellik değil, sürdürülebilir bir ritim.

English equivalent:

> Build a sustainable fasting rhythm, not a perfect streak.

The content must demonstrate the product's real strengths:

- fasting timer and flexible plans;
- hydration, weight, meal, and progress tracking;
- estimated metabolic stages with appropriate uncertainty;
- recovery-oriented gamification rather than shame;
- crisis/support mode and completion summaries;
- local-first data storage and no required account;
- Premium plans without misleading outcome promises.

## 3. Audience and language rollout

Initial audience:

- adults beginning with 12:12 or 16:8;
- people repeatedly restarting a fasting routine;
- privacy-conscious wellness users;
- users who prefer calm motivation over punitive streak mechanics.

Language rollout:

1. Produce every launch concept in Turkish and English.
2. Measure creative performance by stable content ID.
3. Localize winners to Spanish, Portuguese, German, and French.
4. Preserve meaning and safety rules; do not machine-publish unchecked health copy.

## 4. Chosen approach

Use an isolated `fasttrack/` system inside the Shorts repository during development. Do not connect it to the legacy schedules or credentials. Once stable, it may be moved to a dedicated private repository.

Reuse only proven technical components:

- Edge TTS and subtitle timing;
- MoviePy vertical rendering patterns;
- Pexels footage selection patterns;
- batch queues and artifacts;
- video validation;
- localization structure;
- YouTube upload patterns with new FastTrack OAuth;
- notification patterns.

Do not reuse:

- war, news, Bible, Arabic, or frequency topic prompts;
- legacy account tokens;
- automatic replies;
- sentiment and competitor workflows;
- automatic title or thumbnail mutation;
- direct unattended TikTok publishing;
- legacy RSS and trend dependencies.

## 5. Content model

One master concept produces:

- Turkish and English short-video scripts;
- platform captions;
- a faceless vertical-video brief;
- a screen-demo brief;
- a UGC/Higgsfield brief;
- carousel copy;
- Pinterest copy;
- short text-post variants;
- a channel-coded Google Play URL.

Recurring series:

1. Today, which fasting hour are you in?
2. Beginner mistakes and gentle starts.
3. Recovery after a broken plan.
4. FastTrack in 20 seconds.
5. Myth versus evidence.
6. Calm visual motivation.
7. Seven-day rhythm challenge.

Weekly editorial rhythm:

| Day | Theme |
| --- | --- |
| Monday | Beginner education |
| Tuesday | Estimated fasting journey |
| Wednesday | Product demonstration |
| Thursday | UGC problem/solution |
| Friday | Myth and safety |
| Saturday | Challenge/community |
| Sunday | Recovery and weekly reset |

## 6. Safety and compliance

Every generated item passes deterministic checks before rendering or publishing.

Disallowed:

- diagnosing, treating, curing, or preventing disease;
- guaranteed weight loss or quantified personal results;
- exact universal autophagy or ketosis timing;
- fake testimonials or before/after transformations;
- encouragement aimed at minors;
- advice to ignore medication, pregnancy, eating-disorder history, or professional care;
- shame, punishment, or fear-based retention language.

Required when relevant:

- describe metabolic timings as general estimates;
- describe FastTrack as a wellness/educational tracker, not a medical device;
- encourage professional advice for individual health decisions;
- distinguish actor/AI creator demonstrations from genuine user testimonials.

Compliance failure is blocking. The workflow must not silently convert a failed check into a successful publish job.

## 7. Automation architecture

```text
content/topics.json
        |
        v
Planner -> Script generator -> Compliance gate -> Localizer
        |                                      |
        +------------------+-------------------+
                           v
            Draft package + render manifests
                           |
                           v
             GitHub artifact / human approval
                           |
                           v
       Approved publishers + campaign ledger + report
```

Initial workflows:

- `fasttrack-plan.yml`: validate the topic bank and build a weekly draft package;
- `fasttrack-render.yml`: render approved/local dry-run assets and upload artifacts;
- `fasttrack-publish.yml`: manual-only publisher gate, initially dry-run by default;
- `fasttrack-report.yml`: summarize the content ledger and later ingest platform exports.

TikTok starts as draft/manual publishing. Higgsfield starts as a human-operated creative tool because no dependable public automation contract is assumed.

## 8. Repository layout

```text
fasttrack/
  README.md
  config/
    brand.json
    claims.json
    channels.json
  content/
    topics.json
  src/
    compliance.py
    campaign_links.py
    content_pack.py
    planner.py
  templates/
    captions.json
    ugc.json
  tests/
    test_campaign_links.py
    test_compliance.py
    test_content_pack.py
  output/                 # ignored
.github/workflows/
  fasttrack-plan.yml
  fasttrack-render.yml
  fasttrack-publish.yml
  fasttrack-report.yml
```

## 9. Attribution and measurement

Each master concept receives a stable ID such as `FT-001`. Localized outputs append the language, for example `FT-001-tr` and `FT-001-en`. All exports and links retain both the master ID and language.

Initial measurements avoid adding a new analytics SDK to the app:

- Google Play campaign/referrer links;
- Play Console acquisition and conversion reporting;
- YouTube/Meta/TikTok/Pinterest platform metrics;
- RevenueCat purchase reporting;
- a versioned content ledger in the growth system.

Core report fields:

- content ID, language, series, hook, channel, publish time;
- impressions/views, three-second retention, completion, saves, shares;
- store clicks, installs, store conversion;
- Premium purchase count and revenue when attributable.

## 10. Rollout

### Days 1–7

- build the isolated system and tests;
- create the first 14 Turkish/English concepts;
- generate captions, UGC briefs, and campaign URLs;
- produce dry-run artifacts;
- prepare three Higgsfield UGC packs.

### Days 8–30

- publish one master concept per day;
- test hooks and Play Store listing variants;
- contact micro-creators;
- start the seven-day rhythm challenge;
- keep all publishing human-approved.

### Days 31–60

- localize winning concepts into four additional languages;
- add native FastTrack sharing and shareable rhythm cards in a later app release;
- test small paid boosts only on proven organic creatives.

### Days 61–90

- scale the three strongest creative families;
- expand creator partnerships;
- retire weak channels and series;
- optimize Premium conversion without incentivized reviews or misleading claims.

## 11. Definition of done for version one

- The FastTrack system does not invoke legacy pipelines.
- Configuration and topic files validate offline.
- Unsafe claims block generation with a non-zero exit status.
- A weekly TR/EN content pack can be generated without API credentials.
- Every asset has a stable content ID and channel-specific Play link.
- GitHub Actions produce reviewable artifacts and default to dry-run.
- Tests cover safety checks, attribution links, and content-pack structure.
- Publishing remains manual until fresh FastTrack channel credentials are configured.

## 12. Channel distribution matrix

| Channel | Primary assets | Initial mode |
| --- | --- | --- |
| YouTube | Short, title, description | API after fresh credentials |
| Instagram | Reel, carousel, story | API after fresh credentials |
| TikTok | Vertical video | Draft-only and human publish |
| Facebook | Reel and feed video | API after fresh credentials |
| Pinterest | Static and video Pin | API after approved access |
| Threads | Text and image post | Scheduler after credentials |
| X | Short text and image post | Manual or scheduler |
| Reddit | Helpful post/comment outline | Human-only, disclosed |
| Creator / UGC | Brief and talking points | Human outreach |
| SEO | Article and FAQ outline | CMS after editorial review |

Each localized record must create a separate export for all ten channels. YouTube is one consumer of the content engine, not its central data model.
