#!/bin/bash
# Instalador del bot del Mundial (Telegram). Monta el envío diario con launchd.
#
# Uso:
#   bash ~/.claude/jobs/install.sh [HORA] [MINUTO]
# Ej:  bash ~/.claude/jobs/install.sh 7 30     (envío diario a las 07:30)
#
# Requisitos previos:
#   - uv instalado
#   - ~/.claude/jobs/ con los scripts y fifa-bot.env relleno
#     (TELEGRAM_CHAT_ID, TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, YOUTUBE_API_KEY)
set -euo pipefail

HOUR="${1:-7}"
MINUTE="${2:-30}"

JOBS_DIR="$HOME/.claude/jobs"
LA="$HOME/Library/LaunchAgents"
mkdir -p "$LA"

if [ ! -f "$JOBS_DIR/fifa-bot.env" ]; then
  echo "ERROR: falta $JOBS_DIR/fifa-bot.env (cópialo de fifa-bot.env.example y rellénalo)."
  exit 1
fi

# --- LaunchAgent: job diario ---
cat > "$LA/com.ramon.fifabot.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.ramon.fifabot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$JOBS_DIR/fifa-bot.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>$HOUR</integer>
        <key>Minute</key><integer>$MINUTE</integer>
    </dict>
    <key>StandardOutPath</key><string>$JOBS_DIR/fifa-bot.out.log</string>
    <key>StandardErrorPath</key><string>$JOBS_DIR/fifa-bot.err.log</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
PLIST

launchctl unload "$LA/com.ramon.fifabot.plist" 2>/dev/null || true
launchctl load "$LA/com.ramon.fifabot.plist"

echo "Instalado. Job diario a las $HOUR:$(printf '%02d' "$MINUTE")."
echo
echo "Prueba el envío ahora mismo con:  launchctl start com.ramon.fifabot"
echo "Logs:  $JOBS_DIR/fifa-bot.out.log  y  fifa-bot.err.log"
echo
echo "IMPORTANTE: evita que la máquina se duerma para que dispare a su hora:"
echo "  sudo pmset -a sleep 0 disksleep 0 womp 1"
