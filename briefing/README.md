# DCA Briefing PWA

Persoonlijke ochtendbriefing voor Jop. Eén tap op homescreen → quote + top 3 NU-taken.

## Deploy stappen

### 1. Folder in claude-apps repo plakken
Copy `briefing/` folder naar root van `claude-apps` repo.

### 2. Notion integration aanmaken (1 min)
1. Open https://www.notion.so/my-integrations
2. **New integration** → naam: `DCA Briefing PWA`, type: Internal
3. Submit, kopieer token (`ntn_...`)
4. Open **Action Board** in Notion (id `56a334ea9e874ec1ade0d1ee073d4528`)
5. `...` rechtsboven → **Connections** → zoek `DCA Briefing PWA` → toevoegen

### 3. Env vars in Netlify (2 min)
Netlify dashboard → site settings → Environment variables:

| Variable | Waarde |
|----------|--------|
| `NOTION_TOKEN` | Token uit stap 2 |
| `ANTHROPIC_API_KEY` | Uit Notion Secrets-pagina |
| `ACCESS_KEY` | Verzin een random string van ≥32 chars |

### 4. Deploy via git
```bash
cd ~/claude-apps
git add briefing/
git commit -m "feat: briefing PWA"
git push
```

### 5. Eerste open op iPhone
1. Open Safari op iPhone
2. Ga naar `https://<site>.netlify.app/?key=<ACCESS_KEY>`
3. Briefing laadt → key wordt in localStorage opgeslagen, uit URL gestript
4. Tik **Deel** (vierkant met pijl) → **Zet op beginscherm**
5. Vanaf nu: tap homescreen-icoon = briefing direct

## URL structuur

- Eerste keer: `https://<site>.netlify.app/?key=<ACCESS_KEY>` (key wordt onthouden)
- Daarna: `https://<site>.netlify.app/`
- Key vergeten / nieuw apparaat: voeg `?key=...` opnieuw toe

## Wat de PWA toont

1. **Quote** — gegenereerd door Claude Sonnet met jop-voice prompt, geen platitudes
2. **Top 3 🔴 NU-taken** — uit Action Board, gesorteerd op priority (Hoog → Normaal → Laag)
3. Klik op taak → opent Notion-pagina

## Troubleshooting

| Probleem | Fix |
|----------|-----|
| "Geen toegangscode" | URL met `?key=...` openen |
| "Verkeerde toegangscode" | `ACCESS_KEY` env var checken in Netlify |
| "Notion-fout 401" | Integration token verkeerd of niet gedeeld met Action Board |
| "Notion-fout 404" | Database ID hardcoded in `briefing.js` — checken of klopt |
| Geen taken zichtbaar | Geen taken met Status=`🔴 NU` → geen bug |
| Oude versie blijft | Service worker — sw.js `CACHE_VERSION` bumpen + redeploy |

## Kosten

| Bron | Per briefing | Per maand (1×/dag) |
|------|--------------|---------------------|
| Anthropic Sonnet | ~$0.003 | ~$0.09 |
| Notion API | Gratis | Gratis |
| Netlify | Gratis tier | Gratis |
| **Totaal** | | **<€0.10** |

## Niet inbegrepen (volgende iteraties)

- Push notifications (iOS PWA limitation)
- Offline data (alleen shell is offline; quote+taken vereisen netwerk)
- Multi-user / family share
- Statistieken (hoe vaak geopend, welke taken meest geklikt)
