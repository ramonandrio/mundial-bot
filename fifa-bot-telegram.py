#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.40", "requests>=2.32"]
# ///
"""
Bot diario del Mundial — canal Telegram (Bot API oficial).

Busca resultados/partidos/goleadores con la tool web_search de Anthropic,
formatea un mensaje y lo envía con la Bot API de Telegram. Sin bridge, sin QR,
sin proceso local: solo una llamada HTTPS a api.telegram.org.

Variables de entorno necesarias:
    TELEGRAM_BOT_TOKEN   token del bot (de @BotFather)
    TELEGRAM_CHAT_ID     id del chat destino (p.ej. tu user id)
    ANTHROPIC_API_KEY    tu API key personal de Anthropic
    FIFA_BOT_MODEL       (opcional) modelo; por defecto claude-sonnet-4-6
"""
import os
import re
import sys
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import anthropic

MODEL = os.environ.get("FIFA_BOT_MODEL", "claude-sonnet-4-6")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
# Uno o varios destinos separados por comas: ids de persona o de canal (@canal o -100...).
CHAT_IDS = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]

if not TOKEN:
    sys.exit("ERROR: falta TELEGRAM_BOT_TOKEN.")
if not CHAT_IDS:
    sys.exit("ERROR: falta TELEGRAM_CHAT_ID.")

# Fecha de referencia. Por defecto hoy; FIFA_BOT_TODAY=YYYY-MM-DD permite generar la
# edición de un día pasado (para pruebas o backfill).
_override = os.environ.get("FIFA_BOT_TODAY", "").strip()
if _override:
    _base = datetime.strptime(_override, "%Y-%m-%d")
else:
    _base = datetime.now(ZoneInfo("Europe/Madrid"))
hoy = _base.strftime("%A %d de %B de %Y")

PROMPT = """Eres un bot que prepara el resumen diario del Mundial de fútbol en curso. Hoy es __HOY__ (hora de Madrid, CEST).

Busca en la web y verifica con al menos dos fuentes (web oficial FIFA y un medio deportivo grande):
1. Próximo partido de ESPAÑA: día, hora en CEST y rival de su siguiente encuentro, más su posición actual en el grupo.
2. Resultados de AYER: partidos terminados con marcador final y un dato breve.
3. Partidos de HOY: enfrentamientos con hora de inicio en CEST y fase/grupo.
4. Goleadores: top de la tabla de máximos goleadores del torneo.

Reglas de datos:
- Nunca inventes marcadores ni horarios. Da el marcador de ayer solo si está confirmado.
- La info de clasificación (quién está eliminado, quién se ha clasificado, qué necesita cada selección, contra quién juega en la última jornada) es lo más interesante: inclúyela cuando puedas. Pero ANTES consulta la clasificación real del grupo y el calendario en una fuente, y básate solo en esos datos verificados, no en deducciones de memoria. Si la situación es matemáticamente clara (un equipo ya eliminado o ya clasificado), dilo con seguridad. Si depende de combinaciones o desempates complejos, mantente general ("se juega el pase en la última jornada") sin afirmar detalles que no hayas confirmado. Nunca inventes marcador, rival ni escenario.
- Si un partido está EN JUEGO ahora mismo (en directo, sin resultado final), NO des marcador parcial ni hables de fuentes ni de incertidumbre. Trátalo como un partido más: di que está en juego y añade un comentario breve de qué se juega cada selección, igual que con los de hoy.
- Si de un bloque entero no hay datos fiables, omítelo sin más.
- Bloque de España: EXACTAMENTE dos frases cortas, nada más. Frase 1: cuándo juega su próximo partido (día de la semana y hora CEST) y contra quién. Frase 2: su posición en el grupo ("Va primera del Grupo H"). NO añadas puntos, ni qué necesita, ni cómo llega el rival, ni paréntesis con la madrugada: solo el día y la hora. Todo verificado en calendario y clasificación reales. Si juega hoy, di "hoy a las...". Si España ya está eliminada, una sola frase ("España quedó eliminada en la fase de grupos.").
- Usa el nombre completo del país (Estados Unidos, no EE.UU.; Países Bajos, no Holanda). Esto es importante para emparejar después el resumen en vídeo.
- No incluyas enlaces de ningún tipo. Los enlaces a los resúmenes se añaden después automáticamente.

FORMATO EXACTO (Telegram HTML). Sigue esta plantilla al pie de la letra: misma estructura, mismos emojis, mismas líneas divisorias. Solo cambia los datos.

⚽ <b>Resumen diario Mundial 2026</b>
{Fecha de hoy, ej: Sábado 20 de junio de 2026}

🇪🇸 <b>España</b>
Juega el {día} a las {hora} CEST contra {rival}. Va {posición, ej: primera} del Grupo {X}.

───────────────────
🗓 <b>Ayer ({día y fecha de ayer, ej: viernes 19 de junio})</b>
───────────────────

{bandera1}🆚{bandera2} <b>{Equipo1} {marcador} {Equipo2}</b>
Grupo {X}. {Comentario de 1-2 frases con un detalle concreto: goleador, contexto o qué implica en la clasificación. Tono natural y con color.}

({repite el bloque por cada partido de ayer})

───────────────────
📅 <b>Hoy ({día y fecha de hoy})</b>
───────────────────

{bandera1}🆚{bandera2} <b>{Equipo1} vs {Equipo2}</b>
Grupo {X}. {hora} CEST. {Comentario de 1-2 frases: cómo llega cada selección y qué se juega.}

({repite el bloque por cada partido de hoy})

───────────────────
🥾 <b>Tabla de goleadores</b>
───────────────────

🥇 {Jugador} {bandera} · {N} goles — {detalle breve}
🥈 Con {N} goles: {lista breve de nombres con su bandera}

Reglas de formato:
- Usa <b>...</b> SOLO donde aparece en la plantilla: título, los tres encabezados de sección y el nombre de cada enfrentamiento. Nada más en negrita.
- Cada sección lleva una línea divisoria (─ repetido) ARRIBA y otra ABAJO de su encabezado, como en la plantilla.
- Aparte de <b>, no uses otro HTML, ni markdown, ni asteriscos. No uses los caracteres &, < o > en el texto normal (escribe "y" en vez de "&").
- Banderas y emojis como en la plantilla. Sin guiones largos. Redacción cuidada, no telegráfica.
- El mensaje completo NO debe superar los 3500 caracteres. Comentario de 1 frase por partido (2 cortas como máximo). Prioriza concisión sobre exhaustividad.
- Escribe "Turquía" (en español), no "Türkiye".

CRÍTICO: no narres tu proceso ni escribas una sola palabra de explicación. Tu respuesta debe EMPEZAR directamente por la línea ===MENSAJE=== (sin nada antes) y TERMINAR con ===FIN===. Entre medias, solo el mensaje.
===MENSAJE===
(aquí el mensaje)
===FIN===""".replace("__HOY__", hoy)

client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
resp = client.messages.create(
    model=MODEL,
    max_tokens=4000,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 14}],
    messages=[{"role": "user", "content": PROMPT}],
)

full = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
# Extracción robusta: descarta cualquier preámbulo antes de ===MENSAJE=== y acepta
# que falte ===FIN=== (p.ej. si el modelo se quedó sin tokens). Si no hay marcador
# de inicio, no enviamos nada (mejor silencio que basura).
if "===MENSAJE===" in full:
    message = full.split("===MENSAJE===", 1)[1].split("===FIN===", 1)[0].strip()
else:
    message = ""

if not message:
    sys.exit("ERROR: el modelo no devolvió un mensaje con el formato esperado. No se envía nada.")


# --- Enlaces a los resúmenes de DAZN (descubrimiento + validación en Python) ---
# Para cada partido de AYER buscamos su resumen en YouTube y validamos que es un vídeo
# de DAZN del partido correcto (autor DAZN, título de highlight y ambos equipos en él).
# Vía principal: API oficial de YouTube (YOUTUBE_API_KEY). Respaldo: scraping + oEmbed.
# Nunca se inventa una URL ni se bloquea el envío: si algo falla, el partido va sin enlace.
YT_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
SOCS = "CAISEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg"  # cookie para esquivar el muro de consentimiento
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _tokens(team):
    return [t for t in re.split(r"[^a-z]+", _norm(team)) if len(t) >= 4]


def _api_search(query):
    """Candidatos vía API oficial de YouTube: lista de {id, title, author}."""
    if not YT_API_KEY:
        return []
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search",
                         params={"key": YT_API_KEY, "part": "snippet", "q": query,
                                 "type": "video", "maxResults": 8}, timeout=15)
        if r.status_code != 200:
            return []
        out = []
        for it in r.json().get("items", []):
            vid = it.get("id", {}).get("videoId")
            sn = it.get("snippet", {})
            if vid:
                out.append({"id": vid, "title": sn.get("title", ""),
                            "author": sn.get("channelTitle", "")})
        return out
    except Exception:
        return []


_oembed_cache = {}


def _oembed(video_id):
    if video_id in _oembed_cache:
        return _oembed_cache[video_id]
    data = None
    try:
        r = requests.get("https://www.youtube.com/oembed",
                         params={"url": f"https://www.youtube.com/watch?v={video_id}",
                                 "format": "json"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
    except Exception:
        data = None
    _oembed_cache[video_id] = data
    return data


def _scrape_search(query):
    """Respaldo sin API key: IDs del HTML de búsqueda, enriquecidos con oEmbed."""
    ids, seen = [], set()
    try:
        r = requests.get("https://www.youtube.com/results",
                         params={"search_query": query},
                         headers={"Cookie": f"SOCS={SOCS}", "Accept-Language": "es",
                                  "User-Agent": UA}, timeout=15)
        for vid in re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', r.text):
            if vid not in seen:
                seen.add(vid)
                ids.append(vid)
    except Exception:
        return []
    out = []
    for vid in ids[:8]:
        data = _oembed(vid)
        if data:
            out.append({"id": vid, "title": data.get("title", ""),
                        "author": data.get("author_name", "")})
    return out


def _score(text):
    """Marcador normalizado 'x-y' encontrado en el texto, o None."""
    m = re.search(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})", text)
    return f"{m.group(1)}-{m.group(2)}" if m else None


def find_highlight(team1, team2, score=None):
    """URL del resumen DAZN del partido, o None. Acepta un candidato de DAZN (highlight)
    si menciona a ambos equipos, O si menciona a uno y el marcador coincide (cubre
    variantes de grafía tipo Iraq/Irak, Curazao/Curaçao). Usa la API; respaldo: scraper."""
    t1, t2 = _tokens(team1), _tokens(team2)
    if not t1 or not t2:
        return None
    query = f"{team1} vs {team2} resumen y goles Copa Mundial 2026 DAZN"
    cands = _api_search(query) or _scrape_search(query)
    for c in cands:
        author, title = _norm(c["author"]), _norm(c["title"])
        if "dazn" not in author or not ("resumen" in title or "highlights" in title):
            continue
        has1, has2 = any(t in title for t in t1), any(t in title for t in t2)
        score_ok = score is not None and _score(title) == score
        if (has1 and has2) or ((has1 or has2) and score_ok):
            return f"https://www.youtube.com/watch?v={c['id']}"
    return None


def add_highlights(text):
    """Para cada bloque de partido terminado (negrita 'Equipo1 x-y Equipo2'), añade la
    línea 📺 con el enlace al resumen si se encuentra."""
    added = 0
    out = []
    for block in text.split("\n\n"):
        # Marcador: dígitos con guion, tolerando espacios y guion largo (2-0, 4 - 0, 1–1).
        m = re.search(r"<b>(.+?)\s+(\d{1,2})\s*[-–—]\s*(\d{1,2})\s+(.+?)</b>", block)
        if m:
            url = find_highlight(m.group(1), m.group(4), f"{m.group(2)}-{m.group(3)}")
            if url:
                block = f'{block}\n📺 <a href="{url}">Resumen y goles</a>'
                added += 1
        out.append(block)
    return "\n\n".join(out), added


message, links_added = add_highlights(message)
print(f"Enlaces de resumen añadidos: {links_added}")

def send(chat_id, text, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload, timeout=30)


def split_message(text, limit=4000):
    """Parte el mensaje en trozos <= limit por líneas en blanco (sin romper <b>...</b>,
    que siempre van en una sola línea)."""
    parts, cur = [], ""
    for block in text.split("\n\n"):
        if cur and len(cur) + len(block) + 2 > limit:
            parts.append(cur)
            cur = block
        else:
            cur = f"{cur}\n\n{block}" if cur else block
    if cur:
        parts.append(cur)
    return parts


ok = 0
parts = split_message(message)
for cid in CHAT_IDS:
    delivered = True
    for part in parts:
        r = send(cid, part, "HTML")
        if r.status_code == 400:
            # Fallback: si Telegram rechaza el HTML, manda ese trozo en texto plano.
            r = send(cid, re.sub(r"</?b>", "", part))
        if not r.ok:
            delivered = False
            print(f"Aviso: fallo enviando a {cid}: {r.status_code} {r.text[:200]}")
    if delivered:
        ok += 1

print(f"Enviado a {ok}/{len(CHAT_IDS)} destino(s) en {len(parts)} mensaje(s).")
if ok == 0:
    sys.exit("ERROR: no se entregó a ningún destino.")
print(message)
