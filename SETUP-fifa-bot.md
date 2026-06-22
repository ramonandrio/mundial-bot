# Setup del bot del Mundial (WhatsApp) — pasos manuales

Ya están creados por Claude:
- `~/code/whatsapp-mcp/` (repo clonado, Go instalado)
- `~/.claude/jobs/whatsapp-mcp.json` (config MCP)
- `~/.claude/jobs/fifa-bot-prompt.md` (instrucciones del agente)
- `~/.claude/jobs/fifa-bot.sh` (lanzador headless)
- `~/Library/LaunchAgents/com.ramon.fifabot.plist` (disparo diario 09:00)

Faltan estos pasos (los hace el usuario porque ejecutan código de terceros, usan tu cuenta de WhatsApp o instalan un servicio persistente).

## 1. Compilar y arrancar el bridge (escanear QR)

```bash
cd ~/code/whatsapp-mcp/whatsapp-bridge
go build -o whatsapp-bridge .
./whatsapp-bridge          # muestra un QR: escanéalo desde WhatsApp > Dispositivos vinculados
```

Deja esta terminal abierta la primera vez. La sesión caduca ~cada 20 días → re-escaneo.

## 2. Configurar el .env (claves + destinatario)

El job ya NO usa Claude Code ni tu cuenta de empresa: corre un script por API
(`fifa-bot-anthropic.py` o `fifa-bot-openai.py`) que factura a tu API key personal.

```bash
cp ~/.claude/jobs/fifa-bot.env.example ~/.claude/jobs/fifa-bot.env
# edita fifa-bot.env: BOT_PROVIDER, FIFA_BOT_RECIPIENT, y la API key correspondiente
```

Destinatario: tu número con prefijo de país y sin "+", p.ej. `34600111222`.
Para un grupo necesitas su JID (`...@g.us`).

## 3. Probar el envío a mano

```bash
chmod +x ~/.claude/jobs/fifa-bot.sh
~/.claude/jobs/fifa-bot.sh
```

O directamente un proveedor concreto:

```bash
export FIFA_BOT_RECIPIENT=34600111222
export ANTHROPIC_API_KEY=sk-ant-...
uv run ~/.claude/jobs/fifa-bot-anthropic.py     # versión Anthropic
# uv run ~/.claude/jobs/fifa-bot-openai.py       # versión OpenAI
```

Debe llegarte el mensaje. Itera sobre el PROMPT dentro del script si quieres ajustar el formato.

## 4. Dejar el bridge siempre activo (LaunchAgent)

Crea `~/Library/LaunchAgents/com.ramon.whatsapp-bridge.plist` con este contenido y cárgalo:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.ramon.whatsapp-bridge</string>
    <key>ProgramArguments</key>
    <array><string>$HOME/code/whatsapp-mcp/whatsapp-bridge/whatsapp-bridge</string></array>
    <key>WorkingDirectory</key><string>$HOME/code/whatsapp-mcp/whatsapp-bridge</string>
    <key>KeepAlive</key><true/>
    <key>RunAtLoad</key><true/>
    <key>StandardOutPath</key><string>$HOME/.claude/jobs/whatsapp-bridge.out.log</string>
    <key>StandardErrorPath</key><string>$HOME/.claude/jobs/whatsapp-bridge.err.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.ramon.whatsapp-bridge.plist
```

## 5. Activar el disparo diario

```bash
launchctl load ~/Library/LaunchAgents/com.ramon.fifabot.plist
launchctl start com.ramon.fifabot   # disparo manual de prueba
```

Logs en `~/.claude/jobs/fifa-bot.{out,err}.log`.

## Notas

- El Mac debe estar encendido a las 09:00 para que se envíe (limitación de la vía local, como el Task Scheduler del post).
- Para cambiar la hora, edita `StartCalendarInterval` en `com.ramon.fifabot.plist` y recarga el agent (`launchctl unload` + `load`).
- Cuenta personal de WhatsApp + automatización va contra los ToS de WhatsApp. Para uso propio el riesgo es bajo; no lo escales a envíos masivos.
