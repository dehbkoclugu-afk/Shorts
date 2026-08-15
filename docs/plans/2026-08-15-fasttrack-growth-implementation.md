# FastTrack Growth System Implementation Plan

> Execute in the isolated `agent/fasttrack-growth` worktree. Keep all new workflows manual or dry-run by default. Do not reuse legacy credentials.

**Goal:** Ship a tested, offline-first FastTrack content-pack generator with deterministic health-claim checks, channel attribution links, branded storyboards, and safe GitHub Actions entry points.

**Architecture:** A standard-library Python package reads versioned JSON configuration and bilingual topics, validates the content, builds normalized campaign records, renders branded 9:16 storyboard cards with Pillow, and exports a reviewable content pack. GitHub Actions run the same commands and upload artifacts. Publishing stays a separate manual gate.

**Dependencies:** Python 3.11+, Pillow for storyboards; standard library for validation, links, packing, tests, and reporting.

---

## Task 1: Establish the FastTrack package and brand configuration

**Files:**

- Create: `fasttrack/__init__.py`
- Create: `fasttrack/src/__init__.py`
- Create: `fasttrack/config/brand.json`
- Create: `fasttrack/config/channels.json`
- Create: `fasttrack/config/claims.json`
- Modify: `.gitignore`

**Steps:**

1. Add the production Play package and URL.
2. Mirror the app palette from `fasting_app/lib/core/theme/app_colors.dart`.
3. Define TR/EN launch locales and the four later locales.
4. Define supported channels and campaign naming rules.
5. Define blocking phrases and contextual disclaimer triggers.
6. Ignore `fasttrack/output/` while retaining its README/placeholder if needed.
7. Validate every JSON file with `python -m json.tool`.

## Task 2: Build and test campaign attribution links

**Files:**

- Create: `fasttrack/tests/test_campaign_links.py`
- Create: `fasttrack/src/campaign_links.py`

**Steps:**

1. Write tests for encoded Google Play install-referrer parameters.
2. Test stable content ID, language, channel, medium, and campaign fields.
3. Test rejection of unknown channels and malformed content IDs.
4. Implement the smallest standard-library URL builder.
5. Run `python -m unittest fasttrack.tests.test_campaign_links -v`.

## Task 3: Build and test the deterministic compliance gate

**Files:**

- Create: `fasttrack/tests/test_compliance.py`
- Create: `fasttrack/src/compliance.py`

**Steps:**

1. Write tests that block guaranteed weight-loss, disease-treatment, fake-testimonial, minor-targeting, and exact universal metabolic timing claims.
2. Write tests that allow cautious estimates and ordinary product demonstrations.
3. Require a general-estimate disclaimer when metabolic stages are mentioned.
4. Return machine-readable findings with severity, rule ID, and matched text.
5. Make blocking findings produce a non-zero CLI exit.
6. Run `python -m unittest fasttrack.tests.test_compliance -v`.

## Task 4: Define the first 14 bilingual launch concepts

**Files:**

- Create: `fasttrack/content/topics.json`
- Create: `fasttrack/templates/ugc.json`
- Create: `fasttrack/templates/captions.json`

**Steps:**

1. Add stable master IDs `FT-001` through `FT-014`.
2. Include TR/EN hook, spoken copy, CTA, series, format, and safety note.
3. Add three Higgsfield briefs with actor disclosure and no personal-results claim.
4. Add channel caption templates.
5. Validate JSON and run all copy through the compliance CLI.

## Task 5: Build and test content-pack generation

**Files:**

- Create: `fasttrack/tests/test_content_pack.py`
- Create: `fasttrack/src/content_pack.py`
- Create: `fasttrack/src/planner.py`

**Steps:**

1. Write tests for normalized TR/EN records and deterministic ordering.
2. Verify each localized record carries master ID, locale, series, copy, CTA, compliance result, and channel links.
3. Verify an unsafe concept aborts the entire pack.
4. Generate `content-pack.json`, `content-calendar.csv`, and `review.md`.
5. Add CLI filters for count, locale, and content ID.
6. Run `python -m unittest fasttrack.tests.test_content_pack -v`.

## Task 6: Generate branded review storyboards

**Files:**

- Create: `fasttrack/tests/test_storyboards.py`
- Create: `fasttrack/src/storyboards.py`

**Steps:**

1. Test 1080x1920 output, deterministic file names, and one storyboard per localized item.
2. Use FastTrack primary `#E84C5E`, secondary `#FF8A96`, water accent `#4A9DFF`, and dark background `#0F0F1A`.
3. Render hook, three beats, CTA, content ID, language, and disclosure area.
4. Use system fonts with a deterministic fallback.
5. Generate PNG storyboards into the ignored output directory.

## Task 7: Add safe GitHub Actions workflows

**Files:**

- Create: `.github/workflows/fasttrack-plan.yml`
- Create: `.github/workflows/fasttrack-render.yml`
- Create: `.github/workflows/fasttrack-publish.yml`
- Create: `.github/workflows/fasttrack-report.yml`

**Steps:**

1. Keep planning and rendering manual initially; add an optional weekly schedule only after launch validation.
2. Grant `contents: read` unless a job genuinely needs more.
3. Upload content packs and storyboards as artifacts.
4. Make publishing require `workflow_dispatch`, an explicit `approved=true` input, and `dry_run=true` by default.
5. Do not reference legacy YouTube, TikTok, Meta, or Gemini secrets.
6. Make missing publisher configuration fail clearly rather than report false success.

## Task 8: Documentation, reporting, and full verification

**Files:**

- Create: `fasttrack/README.md`
- Create: `fasttrack/src/report.py`
- Create: `fasttrack/tests/test_report.py`

**Steps:**

1. Document local commands, artifact review, approval, and later credential setup.
2. Generate a baseline weekly report from the content calendar/ledger.
3. Run `python -m unittest discover -s fasttrack/tests -v`.
4. Run `python -m compileall -q fasttrack`.
5. Run `git diff --check`.
6. Generate a 14-concept TR/EN pack and verify 28 localized records and 28 storyboards.
7. Confirm legacy workflows and source files are unchanged.
8. Commit intentional changes, push `agent/fasttrack-growth`, and open a draft PR against the repository default branch.

