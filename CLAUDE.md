# CLAUDE.md — claude-apps

Monorepo voor Jops eigen apps, skills en tools. Vier Netlify-PWA's, een set
skills, losse tools en de guardrail-hooks staan hier naast elkaar in één repo.

> **Deze repo is PUBLIC.** Alles wat hier gecommit wordt is voorgoed openbaar,
> ook na een latere verwijdering (forks, caches, indexering). Zie *Wat hier
> niet in hoort*.

## Layout

| Pad | Wat |
|---|---|
| `briefing/` | Briefing-PWA (Netlify + functions) |
| `budget-app/` | Budget-PWA, bonnetjes-scan via Netlify function |
| `trading-monitor/` | ALT-monitor PWA + Notion-sync functions |
| `voeding-app/` | Voedings-PWA |
| `skills/dca-huisstijl/` | DCA-huisstijl: DOCX/HTML/PDF-generatie + gepinde fonts |
| `skills/dip-scan/` | Dip-scan skill + `validate.py` (validatie-gauntlet) |
| `skills/intel-synthese/` | Intel-synthese skill |
| `executor-agent/` | IJsberg-trio (CLAUDE/projectplan/architectuur), nog geen code |
| `tools/pdfmerge/` | `merge_pdf.py` |
| `tools/alt-sync/` | Notion → `trading-monitor/data.json` sync |
| `docs/` | Losse documentatie |
| `.claude/hooks/` | Guardrail-hooks (zie hieronder) |

Projectspecifieke regels staan in een eigen `CLAUDE.md` naast de code:
[`trading-monitor/CLAUDE.md`](trading-monitor/CLAUDE.md) (backtest-validatie,
edge-hiërarchie) en [`executor-agent/CLAUDE.md`](executor-agent/CLAUDE.md).
Dit bestand geldt repo-breed; een project-CLAUDE.md gaat lokaal voor.

## Guardrails

Drie hooks in `.claude/hooks/`, aangesloten via `.claude/settings.json`. Ze
blokkeren met exit 0 + JSON (`permissionDecision: deny`), niet met exit 2.

| Hook | Event | Blokkeert |
|---|---|---|
| `guard-bash.ps1` | PreToolUse · `Bash` | `authuser`, `rm -rf /`, force-push, `git reset --hard`, `Remove-Item -Recurse -Force` |
| `guard-write.ps1` | PreToolUse · `Write\|Edit` | schrijven naar `.env`, `secrets/`, `credentials.json`, `*token*.json`, `id_rsa`, `.git-credentials`; en content die matcht op `ghp_…`, `AKIA…`, `sk-…` |
| `posttest-py.ps1` | PostToolUse · `Write\|Edit` | een `.py` met syntaxfout (draait `python -m py_compile`) |

De patronen in `guard-bash.ps1` zijn bewust een korte, leesbare lijst — breid
die uit in plaats van er omheen te werken.

## Wat hier niet in hoort

`.gitignore` dekt de bekende gevallen af: `credentials.json`, `client_secret*`,
`gcp-oauth*`, `*token*.json`, `.env*` (behalve `.env.example`), `__pycache__/`,
`.venv/`, `node_modules/`, `.netlify/`, `*.sqlite`, `*.db`, `*.log`, `*.pdf`.

Daarnaast, met opzet buiten deze repo:

- **Secrets in welke vorm dan ook.** Keys komen uit de omgeving:
  `Netlify.env.get(...)` in functions, `${{ secrets.* }}` in workflows,
  `os.environ` in Python. Nooit een letterlijke waarde in een bestand.
- **Auteursrechtelijk materiaal van derden** — lesmethodes, transcripten,
  ingekochte PGN/CBV-databases, boeken. Dat is de reden dat het CASM-project
  buiten GitHub blijft en via een bare repo op iCloud synct.
- **Grote binaire datadumps.** Uitzondering: de gepinde fonts in
  `skills/dca-huisstijl/fonts/`, want de huisstijl-skill moet offline werken.

## Werkwijze

- **Branch + PR, niet rechtstreeks op `main`.** Naamgeving: `batch/<datum>-<naam>`
  voor een verzamelbatch, `fix/<onderwerp>` voor een losse fix.
- **Eén onderwerp per commit**, met een berichtregel die zegt wát er verandert.
- Netlify deployt automatisch na een merge naar `main`. Een PR die blijft
  hangen betekent dus dat de live-versie achterloopt — controleer bij twijfel
  `gh pr list` vóór je concludeert dat iets "gepusht" is.
- Nieuw project = eerst het IJsberg-trio (CLAUDE.md, projectplan.md,
  architectuur.md), dan pas code. `executor-agent/` is daar het voorbeeld van.

## Verify-first

Repo-breed geldt dezelfde regel als in het trading-project: **niet gokken, eerst
kijken.** Koersen en feiten uit een actuele bron, geen aanname uit het geheugen;
een edge pas "echt" na de gauntlet in `skills/dip-scan/validate.py`. Bij code
betekent het: lees het bestand voordat je erover concludeert, en draai de test
voordat je zegt dat iets werkt.
