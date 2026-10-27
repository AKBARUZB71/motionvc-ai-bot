# MOTIONVC AI Content Agent

Daily @motionvc Telegram album: 3 editorial slides in white/black/yellow (1080×1350), three-line Uzbek caption, Gemini TTS male voice (OGG/Opus).

## Setup

1. Repository > **Settings** > **Secrets and variables** > **Actions** > **New repository secret**
2. Add **GEMINI_API_KEY** and **TELEGRAM_BOT_TOKEN** (fresh keys only; do not commit keys to this public repository).
3. Ensure bot is channel administrator in **@motionvc** with **Post messages** rights.
4. Repository > **Actions** > **MOTIONVC Daily AI Carousel** > **Run workflow**. Leave **preview_only = true** for a dry run, then inspect artifacts.
5. For an actual test post, run again with **preview_only = false**. This posts 3 images and an OGG voice.
6. Schedule is 03:00 UTC = 08:00 Tashkent. GitHub Actions scheduled execution can run late; it isn't precise guaranteed timing.

## Security and operational notes

- Never use previously exposed tokens. Rotate them first.
- GitHub Actions workflow logs may contain metadata. Secrets are read from GitHub Secrets, not committed.
- Public repo code is visible; images and generated voice can be downloaded by those with access to run artifacts.
- Gemini model availability, quota and billing may cause failures. Failing runs appear in Actions logs.
- If TTS fails, the bot does **not** publish an incomplete album. Post retries after partial failure may duplicate an album; review the channel before retrying.
- The automation is not deployed or tested until Secrets are configured and a workflow run succeeds.
- For reliable exactly-once publishing, add durable state tracking and a service with stronger scheduling guarantees.
