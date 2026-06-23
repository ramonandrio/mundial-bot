# Despliegue del bot (host siempre encendido)

El bot publica solo cada mañana. Necesita una máquina encendida a esa hora. Estos son los
pasos para dejarlo corriendo.

## 1. Prerrequisitos

```bash
# uv (gestor de Python). Si no está:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

No hace falta instalar nada más: el script declara sus dependencias en línea y `uv` las
resuelve solo.

## 2. Traer el código

```bash
mkdir -p ~/.claude && git clone https://github.com/ramonandrio/mundial-bot.git ~/.claude/jobs
```

## 3. Configurar el .env (claves y destino)

```bash
cp ~/.claude/jobs/fifa-bot.env.example ~/.claude/jobs/fifa-bot.env
nano ~/.claude/jobs/fifa-bot.env
```

Rellena:
- `BOT_SCRIPT=fifa-bot-telegram.py`
- `TELEGRAM_CHAT_ID=` tu chat o `@canal`
- `TELEGRAM_BOT_TOKEN=` token de @BotFather
- `ANTHROPIC_API_KEY=` tu clave de Anthropic
- `YOUTUBE_API_KEY=` tu clave de YouTube Data API v3

El `.env` no se versiona (está en `.gitignore`): vive solo en cada máquina.

## 4. Instalar el envío diario

```bash
bash ~/.claude/jobs/install.sh 7 30      # hora del envío (7:30)
```

## 5. Probar y evitar que se duerma

```bash
launchctl start com.ramon.fifabot                 # disparo de prueba
sudo pmset -a sleep 0 disksleep 0 womp 1          # que la máquina no se suspenda
```

Logs en `~/.claude/jobs/fifa-bot.out.log` y `fifa-bot.err.log`.

## Mantenimiento

- **Desplegar cambios:** se hace `git push` desde donde edites. La máquina hace `git pull`
  sola antes de cada envío, así que no hay que tocarla.
- **Cambiar la hora:** `bash install.sh 8 30` (regenera y recarga el job).
