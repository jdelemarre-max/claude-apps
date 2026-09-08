# alt-sync

Brug tussen de Notion-pagina **ALT Dashboard Data (auto-sync bron)** en de
ALT-monitor (`trading-monitor/`).

## Waarom dit bestaat

`trading-monitor/index.html` had alle data hardcoded (`CATS`, `POS`, `SCN`, `SO`,
`SNAPS`) en stond daardoor stil op 11 mei 2026, terwijl de Notion-bron wél
bijgewerkt werd. De Notion-pagina claimde dat een GitHub Action de sync deed —
die Action bestond niet. Dit is die Action.

## Hoe het werkt

1. `sync_alt_data.py` leest het eerste json-codeblok van de Notion-pagina.
2. Het valideert dat alle verwachte sleutels aanwezig zijn.
3. Het schrijft `trading-monitor/data.json`.
4. `index.html` haalt `data.json` op bij het laden; faalt dat, dan vallen de
   hardcoded waarden terug in (de monitor blijft dus altijd werken).

## Eenmalige setup

In de repo-instellingen op GitHub:

- **Secret** `NOTION_API_KEY` — integratietoken met leesrechten op de pagina.
- **Variable** `NOTION_ALT_DATA_PAGE` — optioneel; zonder deze gebruikt het
  script de bekende pagina-ID.

Deel de Notion-pagina daarna expliciet met de integratie, anders geeft de API 404.

## Handmatig draaien

```
NOTION_API_KEY=secret_xxx python tools/alt-sync/sync_alt_data.py
```
