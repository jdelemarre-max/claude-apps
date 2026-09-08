# projectplan.md — Executor-agent

> IJsberg-trio, doc 2/3. Fasen van niets → autonome commit-loop. Geen code vóór
> `architectuur.md` akkoord is.

## Doel in één zin

Claude-in-chat levert artefacten + een change-manifest; de executor-agent commit
en pusht die naar `claude-apps` met eigen vault-credentials — zonder Jops
handmatige tussenkomst en zonder secrets in de chat.

## Fasen

| Fase | Wat | Done-criterium |
|---|---|---|
| **F0 — IJsberg** | deze drie docs | trio akkoord door Jop |
| **F1 — Credential** | fine-grained PAT/GitHub App, scope = claude-apps · contents:write, in vault | agent kan lezen/schrijven, secret nergens in chat/repo |
| **F2 — Minimale executor** | script dat 1 bestand commit+pusht naar een testbranch | groene push, zichtbaar op GitHub |
| **F3 — Manifest-protocol** | Claude levert `change-manifest.json` (bestanden, paden, commit-msg, branch); agent past toe | manifest → correcte commit, 1:1 |
| **F4 — Deploy-hook** | Netlify-deploy bevestigen na push (al auto, maar status terugmelden) | deploy-status in Action Board |
| **F5 — MIL dry-run** | 2 weken: agent logt diff + commit-msg, pusht NIET | Jop keurt elke run; foutratio ~0 |
| **F6 — Go-live** | autonome push op schema / op trigger | loop draait, elke run gelogd |

## Manifest-protocol (kern van F3)

Claude schrijft per handoff een `change-manifest.json` naar de Drive-map:

```json
{
  "repo": "claude-apps",
  "branch": "auto/intel-29jun",
  "commit_message": "dip-scan: validatie-gauntlet + edge-hiërarchie",
  "files": [
    {"path": "dip-scan-skill/validate.py", "source": "drive://<id>"},
    {"path": "dip-scan-skill/SKILL.md", "op": "append", "source": "drive://<id>"}
  ],
  "irreversible": false
}
```

`op: append/replace/create`. `irreversible: true` → agent stopt en vraagt
bevestiging. De agent voert nooit iets uit dat niet in een door Jop/denk-laag
geautoriseerd manifest staat.

## Rollback

Elke run = aparte branch + PR (geen directe push naar `main` in F1–F5). Fout →
branch weggooien, geen schade aan `main`. Pas na MIL eventueel direct-to-main.

## Risico's & mitigatie

- *Secret-lek* → vault + least-privilege scope + nooit loggen.
- *Foute file-paden* → manifest valideren tegen repo-tree vóór apply.
- *Prompt-injection via manifest/bestand* → alleen Jop/denk-laag mag manifests
  autoriseren; agent draait geen instructies uit bestandsinhoud.
- *PAT-expiry* → rotatie-herinnering (oude les).

## Out of scope (nu)

Andere repo's, infra-provisioning, secret-rotatie-automatisering, multi-user.
Eerst: één repo, één loop, betrouwbaar.
