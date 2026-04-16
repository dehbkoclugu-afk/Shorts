# Smart Dispatcher Setup Guide

## 📋 Overview

The **Smart Dispatcher** system allows you to choose between two independent daily posting systems:
- **FREQ SHORTS**: Solfeggio frequency content with binaural beats (78 frequencies)
- **WAR SHORTS**: Military/geopolitical news content (English & Turkish)

**Important**: Only ONE system can be active at a time for daily posting.

---

## 🚀 Quick Start

### Enable FREQ SHORTS (Hz)
```
Go to GitHub Actions → "Smart Dispatcher — Unified Daily System"
→ Run workflow
  - system: "Hz (FREQ SHORTS)"
  - count: 7 (optional, default)
  - action: "enable"
```

### Enable WAR SHORTS (English)
```
Go to GitHub Actions → "Smart Dispatcher — Unified Daily System"
→ Run workflow
  - system: "en (WAR SHORTS - English)"
  - count: 10 (optional, default)
  - action: "enable"
```

### Enable WAR SHORTS (Turkish)
```
Go to GitHub Actions → "Smart Dispatcher — Unified Daily System"
→ Run workflow
  - system: "tr (WAR SHORTS - Türkçe)"
  - count: 10 (optional, default)
  - action: "enable"
```

### Check Status
```
Go to GitHub Actions → "Smart Dispatcher — Unified Daily System"
→ Run workflow
  - system: "status" (or just check the log)
```

### Stop Daily Posting
```
Go to GitHub Actions → "Smart Dispatcher — Unified Daily System"
→ Run workflow
  - system: [select active system]
  - action: "stop"
```

---

## 📊 GitHub Configuration Required

### Required Secrets

Add these to your GitHub repository **Settings → Secrets and variables → Secrets**:

```
GEMINI_API_KEY              # Google Gemini API key
PEXELS_API_KEY              # Pexels video API key
YOUTUBE_TOKEN_JSON          # YouTube OAuth token (JSON)
TELEGRAM_BOT_TOKEN          # Telegram bot token
TELEGRAM_CHAT_ID            # Telegram chat ID for notifications
DVIDS_API_KEY               # DVIDS API key (War shorts)
UNSPLASH_ACCESS_KEY         # Unsplash API key
PIXABAY_API_KEY             # Pixabay API key
INSTAGRAM_ACCESS_TOKEN      # Instagram access token
INSTAGRAM_USER_ID           # Instagram user ID
TIKTOK_ACCESS_TOKEN         # TikTok access token
DISCORD_WEBHOOK_URL         # Discord webhook for notifications
TWITTER_API_KEY             # Twitter API key
TWITTER_API_SECRET          # Twitter API secret
TWITTER_ACCESS_TOKEN        # Twitter access token
TWITTER_ACCESS_TOKEN_SECRET # Twitter access token secret
FACEBOOK_ACCESS_TOKEN       # Facebook access token
FACEBOOK_PAGE_ID            # Facebook page ID
YT_COOKIES                  # YouTube cookies (optional, for video download)
GOOGLE_DRIVE_BACKUP         # Google Drive backup key (optional)
```

### Required Variables (GitHub Settings → Secrets and variables → Variables)

These control which system is active:

```
ACTIVE_SYSTEM               # Which system is currently active: "Hz", "en", or "tr"
LANGUAGE                    # Language for War shorts: "en" or "tr" (default: "en")
USE_FREQ_QUEUE             # Enable frequency queue mode: "true" or "false"
USE_QUEUE                  # Enable war shorts queue mode: "true" or "false"
TOPIC_KEYWORDS             # Keywords for War shorts topic selection
COMPETITOR_CHANNEL_IDS     # YouTube competitor channels to analyze
TRANSLATE_LANGUAGES        # Languages for caption translation
GOOGLE_DRIVE_BACKUP        # Enable Google Drive backups: "true" or "false"
```

---

## 🔄 How It Works

### 1. Initial Setup
```
User runs: python dispatcher.py Hz --count 7
  ↓
Dispatcher creates queue: freq_scheduled_queue.json
  ↓
Stores state: dispatcher_scheduler.json
  ↓
Updates GitHub variable: ACTIVE_SYSTEM = "Hz"
```

### 2. Daily Automatic Run
```
GitHub Actions schedule (1:00 UTC for Freq, 2:00 UTC for War)
  ↓
Checks: vars.ACTIVE_SYSTEM
  ↓
If ACTIVE_SYSTEM == "Hz": Runs USE_FREQ_QUEUE=true python freq_main.py
If ACTIVE_SYSTEM == "en": Runs USE_QUEUE=true LANGUAGE=en python main.py
If ACTIVE_SYSTEM == "tr": Runs USE_QUEUE=true LANGUAGE=tr python main.py
  ↓
Posts video from queue
  ↓
Updates queue and caches
```

### 3. System Switch
```
User runs: python dispatcher.py en --count 10
  ↓
Dispatcher detects other active system (Hz)
  ↓
Deactivates Hz → Updates ACTIVE_SYSTEM = "Hz" (disabled in state)
  ↓
Activates en → Updates ACTIVE_SYSTEM = "en"
  ↓
Creates War shorts queue
  ↓
Next scheduled run posts War shorts (en) instead of Freq shorts
```

---

## 📅 Scheduling Details

### FREQ SHORTS Schedule
```yaml
- cron: '0 1 * * *'  # 01:00 UTC daily (if ACTIVE_SYSTEM == "Hz")
```

### WAR SHORTS Schedule
```yaml
- cron: '0 2 * * *'  # 02:00 UTC daily (if ACTIVE_SYSTEM == "en" or "tr")
```

You can modify these times in `.github/workflows/dispatcher.yml`

---

## 🎯 System Requirements

### For FREQ SHORTS:
- Gemini API key
- Pexels API key
- YouTube OAuth token
- Telegram bot (optional, for notifications)

### For WAR SHORTS:
- All of the above +
- DVIDS API key (for military videos)
- Unsplash, Pixabay API keys
- Instagram, TikTok, Twitter, Facebook tokens (for cross-posting)

---

## ⚙️ Queue Management

Each system maintains its own queue file:

### FREQ SHORTS Queue
```json
File: freq_scheduled_queue.json
Format: Array of objects with:
  - scheduled_date: YYYY-MM-DD
  - script_path: path to script
  - audio_path: path to audio
  - video_path: path to video
  - published: boolean
```

### WAR SHORTS Queue
```json
File: war_scheduled_queue.json (English) / war_scheduled_queue_tr.json (Turkish)
Format: Similar to Freq queue
```

### Dispatcher State
```json
File: dispatcher_scheduler.json
Tracks: active systems, scheduled tasks, last runs
```

---

## 🐛 Troubleshooting

### Queue is empty
```
Check: Does queue file exist?
  → No: Run dispatcher setup again
  → Yes: Check batch producer logs

Run: python freq_batch_producer.py --count 7
     OR
     python batch_producer.py --language en --count 10
```

### No video posted
```
Check:
1. Is ACTIVE_SYSTEM variable set correctly?
2. Do queue files exist and have unpublished items?
3. Are all secrets configured?
4. Check GitHub Actions workflow logs
```

### Wrong system is posting
```
Fix:
1. Go to Actions → Dispatcher workflow
2. Run: "status" to see what's active
3. If wrong system is active, run: "stop" then "enable" the correct one
```

### GitHub Actions execution slow
```
This is normal for first run (dependencies, Cloudflare WARP setup).
Subsequent runs cache dependencies and should be faster.
```

---

## 🔐 Security Notes

1. **Never commit secrets** - Always use GitHub Secrets, not `.env` files
2. **Token rotation** - Rotate YouTube tokens periodically
3. **API keys** - Keep Gemini, Pexels, etc. keys private
4. **Cache privacy** - Queues contain file paths, not sensitive data

---

## 📞 Support

If dispatcher is not working:

1. Check `.github/workflows/dispatcher.yml` for syntax errors
2. Verify all secrets are set correctly
3. Run `python dispatcher.py status` locally
4. Check GitHub Actions logs for detailed errors
5. Review queue files: `freq_scheduled_queue.json`, `war_scheduled_queue.json`

---

## 📝 File Reference

| File | Purpose |
|------|---------|
| `.github/workflows/dispatcher.yml` | Main dispatcher workflow |
| `dispatcher.py` | Dispatcher logic & queue management |
| `freq_scheduled_queue.json` | FREQ SHORTS video queue |
| `freq_used_topics.json` | Track used frequencies |
| `war_scheduled_queue.json` | WAR SHORTS (en) video queue |
| `war_scheduled_queue_tr.json` | WAR SHORTS (tr) video queue |
| `dispatcher_scheduler.json` | Dispatcher state & settings |

---

**Last Updated**: 2026-04-16
**Dispatcher Version**: 1.0
