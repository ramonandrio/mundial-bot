#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["anthropic>=0.40", "requests>=2.32"]
# ///
"""
Bot diario del Mundial — versión API de Anthropic.

Busca resultados/partidos/goleadores con la tool web_search de Anthropic,
formatea un mensaje estilo WhatsApp y lo envía POSTeando al bridge local.

NO usa Claude Code ni tu cuenta de empresa: factura a la API key personal.

Uso:
    export ANTHROPIC_API_KEY="sk-ant-..."        # cuenta personal
    export FIFA_BOT_RECIPIENT="34600111222"      # número (prefijo país, sin +) o JID
    uv run ~/.claude/jobs/fifa-bot-anthropic.py

Requisitos: el bridge Go (whatsapp-bridge) corriendo en local.
"""
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import anthropic

MODEL = os.environ.get("FIFA_BOT_MODEL", "claude-sonnet-4-6")
RECIPIENT = os.environ.get("FIFA_BOT_RECIPIENT", "").strip()
BRIDGE_URL = os.environ.get("WHATSAPP_API_BASE_URL", "http://localhost:8080/api")

if not RECIPIENT:
    sys.exit("ERROR: define FIFA_BOT_RECIPIENT (número con prefijo de país sin +, o JID).")

hoy = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%A %d de %B de %Y")

PROMPT = f"""Eres un bot que prepara el resumen diario del Mundial de fútbol en curso. Hoy es {hoy} (hora de Madrid, CEST).

Busca en la web y verifica con al menos dos fuentes (web oficial FIFA y un medio deportivo grande):
1. Resultados de AYER: partidos con marcador final y un dato breve.
2. Partidos de HOY: enfrentamientos con hora de inicio en CEST y fase/grupo.
3. Goleadores: top de la tabla de máximos goleadores del torneo.

Si un bloque no tiene datos fiables o las fuentes no coinciden, omítelo y dilo en una línea. Nunca inventes marcadores ni horarios.

Redacta un mensaje en español, estilo chat de WhatsApp, con emojis y *negrita* al estilo WhatsApp (asteriscos, no markdown). Tres secciones: Ayer, Hoy, Goleadores. Frases variadas, tono natural, sin guiones largos.

No narres tu proceso de búsqueda. Devuelve SOLO el mensaje final, entre estos marcadores exactos:
===MENSAJE===
(aquí el mensaje)
===FIN==="""

client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
resp = client.messages.create(
    model=MODEL,
    max_tokens=2000,
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
    messages=[{"role": "user", "content": PROMPT}],
)

full = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
m = re.search(r"===MENSAJE===\s*(.*?)\s*===FIN===", full, re.S)
message = (m.group(1) if m else full).strip()

if not message:
    sys.exit("ERROR: el modelo no devolvió mensaje. No se envía nada.")

r = requests.post(f"{BRIDGE_URL}/send", json={"recipient": RECIPIENT, "message": message}, timeout=30)
r.raise_for_status()
print("Enviado a", RECIPIENT)
print(r.json())
