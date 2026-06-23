#!/bin/bash
# Lanza el bot del Mundial vía API (sin Claude Code, sin cuenta de empresa).
# Portable: usa $HOME, funciona en cualquier Mac/usuario.
# Pensado para dispararse desde launchd (ver com.ramon.fifabot.plist).
set -euo pipefail

JOBS_DIR="$HOME/.claude/jobs"

# Autoactualiza los scripts desde el repo antes de publicar. Indicamos origin/main
# explícitamente para no depender de la config de tracking de la rama. No bloquea el
# envío si falla (sin red, sin repo, o cambios locales): en ese caso usa lo que haya.
git -C "$JOBS_DIR" pull --quiet --ff-only origin main 2>/dev/null || true

# Carga claves y config (créalo a partir de fifa-bot.env.example):
#   TELEGRAM_CHAT_ID, TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, YOUTUBE_API_KEY, FIFA_BOT_MODEL...
set -a
# shellcheck disable=SC1091
source "$JOBS_DIR/fifa-bot.env"

# Si no hay token en el .env, reutiliza el del canal de Claude Code (si existe).
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && [ -f "$HOME/.claude/channels/telegram/.env" ]; then
  # shellcheck disable=SC1091
  source "$HOME/.claude/channels/telegram/.env"
fi
set +a

# uv suele instalarse en ~/.local/bin; Homebrew en /opt/homebrew (Apple Silicon)
# o /usr/local (Intel). Cubrimos los tres.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

exec uv run "$JOBS_DIR/fifa-bot-telegram.py"
