# architectuur.md — Executor-agent

> IJsberg-trio, doc 3/3. Componenten, dataflow, secret-flow, stack.

## Het centrale idee: denken ≠ handelen

```
DENK-LAAG (Claude, chat)  --change-manifest + artefacten (Drive)-->  EXECUTOR-AGENT (vault-cred)  --git/push-->  GitHub claude-apps
   geen secret             <--status → Action Board--                                              <--Netlify auto-deploy--
                                                          |
                                                          v
                                                    Action Board (log)
```

De denk-laag (Claude) raakt nooit een sleutel aan. De executor is het enige
component met credentials, en die zitten in een vault — niet in de chat, niet in
de repo.

## Componenten

1. **Denk-laag (Claude-in-chat / Claude Code).** Produceert bestanden +
   `change-manifest.json` naar de Drive-map. Schrijft géén secrets.
2. **Drive-map (artefact-bus).** Tussenstation: hier landen de bestanden + het
   manifest. De executor leest hieruit.
3. **Executor-agent.** Python-proces met vault-credentials. Stappen per run:
   a. lees nieuw manifest · b. valideer paden tegen de repo-tree ·
   c. check `irreversible` (zo ja → stop + bevestiging) · d. `git apply` op een
   verse branch · e. push + PR · f. log status naar Action Board.
4. **Vault.** Secret-store met de fine-grained GitHub-credential. Env-injectie bij
   run. Enige plek waar de sleutel leeft.
5. **GitHub `claude-apps`.** Doel-repo. Push → Netlify auto-deploy (bestaand).
6. **Action Board (Notion).** Audit-log: elke run, diff-samenvatting, status.

## Secret-flow (de hele crux)

```
vault --env-injectie--> executor-proces --auth--> GitHub
   ^
   +-- sleutel komt NOOIT langs: chat, repo, Notion-platte-tekst, Drive-manifest
```

Het manifest bevat **verwijzingen** (drive-id's, paden, messages) — nooit
credentials. Daarmee is een gelekt manifest onschadelijk.

## Tech-stack

- **Python** + `subprocess`/`pygit2` voor git, `requests` voor GitHub/Notion API.
- **Auth:** GitHub App (aanbevolen, installable + fijnmazige scope) of
  fine-grained PAT (`claude-apps` · `contents:write` + `pull_requests:write`).
- **Vault:** lokaal `keyring`/`.env` buiten repo, óf cloud secret-store als de
  agent op Console/cron draait.
- **Runtime:** Jops machine (Claude Code-trigger) in F1–F5; cloud-scheduled in F6.
- **Hergebruik:** kan op de bestaande n8n/Docker-infra draaien, maar standalone
  script is simpeler en beter te scopen — voorkeur standalone.

## Faalmodi & checks (ingebouwd)

| Faalmodus | Guardrail |
|---|---|
| Secret in log/output | nooit secrets aanraken; output-scrubber op env-namen |
| Fout pad / overschrijft verkeerd bestand | manifest valideren tegen repo-tree vóór apply |
| Onomkeerbare actie | `irreversible:true` → stop + expliciete bevestiging |
| Instructie verstopt in bestandsinhoud | alleen geautoriseerde manifests; geen exec van bestandsinhoud |
| `main` kapot | branch + PR in F1–F5, nooit direct naar main |
| PAT verlopen | rotatie-herinnering + heldere foutmelding |

## Wat dit oplevert

Het commit-loopje draait zonder Jops handmatige tussenkomst en zonder dat er ooit
een sleutel door de chat gaat. De denk-laag blijft sterk in redeneren; de
executor blijft dom-maar-veilig in uitvoeren. Precies de hybride die we wilden.
