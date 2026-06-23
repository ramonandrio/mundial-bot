# Mundial al día

Un bot que cada mañana publica en un canal de Telegram el parte diario del Mundial 2026.
Se actualiza solo: nadie toca nada.

Canal: [t.me/mundial_al_dia](https://t.me/mundial_al_dia)

## Qué publica

Cada mensaje lleva cuatro bloques:

- **España:** cuándo juega y contra quién, su posición de grupo y un cotilleo del día del entorno de la Selección.
- **Ayer:** resultados con contexto y un enlace al resumen en vídeo de DAZN de cada partido.
- **Hoy:** los partidos del día con hora en CEST y qué se juega cada selección.
- **Goleadores:** la tabla del torneo, al día.

## La idea: el LLM para el criterio, las fuentes para los datos

El bot empezó dejando que el modelo lo escribiera todo, datos incluidos. La lió: coronaba
goleadores equivocados, inventaba marcadores y se sacaba enlaces de YouTube que no existían.

La solución no fue pedirle que no mintiera. Fue **quitarle los datos de las manos**. Ahora el
modelo solo redacta y da formato; los datos que cambian vienen de fuentes fiables y se validan
en código:

- **Goleadores:** se leen de un feed JSON autoritativo. El modelo solo los formatea.
- **Enlaces de vídeo:** los busca el código en la API de YouTube y solo acepta un candidato si
  lo subió DAZN, el título dice "resumen" y aparecen los dos equipos del partido. Si ninguno
  pasa, ese partido va sin vídeo antes que con uno equivocado. El modelo nunca genera una URL.

## Cómo funciona

```
máquina siempre encendida (launchd, 7:30)
   └─ git pull (coge la última versión)
   └─ fifa-bot-telegram.py (uv, dependencias en línea)
        ├─ API de Claude + búsqueda web → redacta y verifica el texto
        ├─ feed JSON                    → tabla de goleadores
        ├─ API de YouTube + validación  → enlaces de resúmenes
        └─ API de Telegram              → publica en el canal
```

El despliegue es por `git pull`: editas, haces push, y la máquina coge la última versión sola
antes de publicar.

## Puesta en marcha

Ver [SETUP.md](SETUP.md). En resumen: clonar, rellenar `fifa-bot.env` (a partir de
`fifa-bot.env.example`) y ejecutar `install.sh`.

## Stack

Python + uv · API de Claude (Anthropic) · YouTube Data API v3 · Bot API de Telegram · launchd.
