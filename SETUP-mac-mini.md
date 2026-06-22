# Montaje en el Mac mini (host siempre encendido)

El bot corre 100% en local. El Mac mini, al estar siempre encendido, es el host ideal:
el bridge de WhatsApp y el job diario viven ahí y no dependen de tu portátil de empresa.

Haz TODO esto **en el Mac mini** (puedes entrar por SSH desde el portátil: `ssh usuario@ip-del-mini`;
el QR de WhatsApp se dibuja en la propia terminal, así que funciona por SSH).

## 1. Prerrequisitos

```bash
# Homebrew (si no está): https://brew.sh
brew install go
curl -LsSf https://astral.sh/uv/install.sh | sh        # instala uv
```

## 2. Traer el código

```bash
mkdir -p ~/code && cd ~/code
git clone https://github.com/lharries/whatsapp-mcp.git
```

Copia la carpeta de scripts desde el portátil (AirDrop, scp o repo privado). Deben quedar en
`~/.claude/jobs/` del mini estos ficheros:
`fifa-bot-anthropic.py`, `fifa-bot-openai.py`, `fifa-bot.sh`, `fifa-bot.env.example`,
`install-mac-mini.sh`, `.gitignore`.

NO copies `fifa-bot.env` por canales inseguros: recréalo en el mini (paso 4).

## 3. Compilar y autenticar el bridge (QR)

```bash
cd ~/code/whatsapp-mcp/whatsapp-bridge
go build -o whatsapp-bridge .
./whatsapp-bridge        # imprime un QR: WhatsApp > Dispositivos vinculados > escanéalo
```

Cuando veas que conecta y sincroniza, corta con Ctrl+C (el LaunchAgent del paso 5 lo relanzará solo;
la sesión queda guardada en store/).

## 4. Crear el .env con tu API key (en el mini)

```bash
cp ~/.claude/jobs/fifa-bot.env.example ~/.claude/jobs/fifa-bot.env
nano ~/.claude/jobs/fifa-bot.env
```

Rellena `BOT_PROVIDER=anthropic`, `FIFA_BOT_RECIPIENT=TU_NUMERO`, `ANTHROPIC_API_KEY=sk-ant-...`.

## 5. Instalar los LaunchAgents

```bash
bash ~/.claude/jobs/install-mac-mini.sh 9 0      # envío diario a las 09:00
```

Genera y carga el LaunchAgent del bridge (siempre vivo) y el del job diario, con las rutas del mini.

## 6. Probar y evitar que se duerma

```bash
launchctl start com.ramon.fifabot               # disparo manual de prueba -> te llega el mensaje
sudo pmset -a sleep 0 disksleep 0 womp 1         # el mini nunca se suspende
```

Logs: `~/.claude/jobs/fifa-bot.out.log` y `fifa-bot.err.log`.

## Mantenimiento

- La sesión de WhatsApp caduca ~cada 20 días: vuelve a correr `./whatsapp-bridge` y re-escanea el QR.
- Cambiar la hora del envío: `bash install-mac-mini.sh 8 30` y listo (regenera y recarga).
- El portátil de empresa ya no pinta nada aquí; puedes borrar de él
  `~/Library/LaunchAgents/com.ramon.fifabot.plist` (nunca se llegó a cargar).
