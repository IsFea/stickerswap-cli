# StickerSwap CLI

`stickerswap-cli` is a local command-line tool that:

- downloads a Telegram video sticker pack,
- swaps faces across the whole pack using a local AI model,
- encodes stickers back to Telegram-compatible `.webm`,
- validates them,
- publishes a new pack through Telegram Bot API.

The main user flow is one command:

```bash
stickerswap run
```

The tool is optimized for Apple Silicon when available and falls back to CPU-only execution on other machines.

## Features

- One-command guided flow with prompts for missing inputs.
- Local-only secrets via `.env.local`.
- Automatic platform detection:
  - Apple Silicon: CoreML + CPU fallback
  - other systems: CPU path
- Automatic model download with fallback URL.
- Automatic dependency checks for `ffmpeg` and `ffprobe`.
- Resume-friendly workspace pipeline.
- Optional live Telegram integration test with 1 sticker.
- Local pre-publish hygiene check to avoid committing secrets or dynamic artifacts.

## Requirements

- Python 3.12+
- `ffmpeg`
- Telegram bot token from `@BotFather`
- your Telegram owner user id

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[face-swap,dev]"
```

`stickerswap run` will verify system dependencies and try to help with setup if something is missing.

## Quick Start

1. Copy the template:

```bash
cp .env.example .env.local
```

2. Fill only your local file `.env.local`.

Example:

```bash
TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_OWNER_USER_ID=123456789
OUTPUT_PACK_NAME=my_new_pack_by_faces_isfea_bot
OUTPUT_PACK_TITLE=My New Pack
```

3. Run:

```bash
source .venv/bin/activate
stickerswap run
```

If a value is missing, the tool will ask for it interactively and can save it back into `.env.local`.

## Main Commands

### Guided run

```bash
stickerswap run
stickerswap run --source-pack video_gachi --face-image /abs/path/face.jpg
```

### Local checks before publishing

```bash
stickerswap check
```

This runs:

- CLI smoke checks,
- unit tests,
- syntax/import checks,
- git hygiene checks,
- secret-pattern scan on candidate repo files.

### Live Telegram integration test

```bash
stickerswap test-live --source-pack video_gachi --face-image /abs/path/face.jpg
```

This creates a separate debug test pack using exactly one source sticker. It only runs when local secrets are available.

### Advanced pipeline commands

```bash
stickerswap fetch-pack --source-pack video_gachi --workdir workspaces/video_gachi --resume
stickerswap swap-faces --workdir workspaces/video_gachi --face-image /abs/path/face.jpg --resume
stickerswap encode-pack --workdir workspaces/video_gachi --resume
stickerswap validate-pack --workdir workspaces/video_gachi
stickerswap publish-pack --workdir workspaces/video_gachi --resume
```

## Local-only Configuration

Tracked:

- `.env.example`

Ignored:

- `.env.local`
- workspaces
- local face images
- downloaded models
- debug and temp files

Do not store real tokens or personal data in tracked files.

## Typical Workspace Layout

- `workspaces/<pack>/manifest/stickers.json`
- `workspaces/<pack>/raw/`
- `workspaces/<pack>/frames/`
- `workspaces/<pack>/swapped/`
- `workspaces/<pack>/encoded/`
- `workspaces/<pack>/temp/`

## Publishing Notes

- Output pack short name must end with `_by_<bot_username>`.
- The tool preserves resume state and can continue publishing into an existing pack.
- The guided flow uses a safe default workspace path under `workspaces/`.

## Development

Run local checks:

```bash
source .venv/bin/activate
stickerswap check
```

## License

MIT

