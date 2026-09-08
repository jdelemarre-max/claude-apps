---
name: intel-synthese
description: >
  Werkwijze voor het samenvatten van macro/trading-bronnen (transcripts van
  interviews, podcasts, video's, artikelen) en het bouwen van één cross-sector
  synthese-interpretatie in het Intel Synthese-dashboard. Gebruik bij geplakte
  finance/macro-transcripts of bij de codewoorden "intel", "smvt + dashboard",
  "werk dashboard bij", "cross-sector". Elke bron krijgt een losse 10-punts
  NL-samenvatting + bronlink en wordt één rij in de Bronnen-feed; daarna wordt
  over ÁLLE bronnen heen de convergentie + spanning + 3-scenario eindconclusie
  herleid. Triggert op geplakte transcripts, "intel", "synthese",
  "dashboard bijwerken".
---

# Intel Synthese — werkwijze

> ⚙️ **Lees eerst de RUNBOOK.** De canonieke, plan-veilige stap-voor-stap staat
> in de Notion-runbook (kindpagina onder dashboard
> `38ccb9b9-b2b4-8144-b3bc-d6a16eae49bb`). Bij twijfel of conflict → **runbook
> wint**. Deze SKILL is de kaart; de runbook is het terrein.
>
> Geen SQL. De Laag-2-leesstap hieronder is al search-only (zie ⚠️ bij Laag 2).

Doel: losse bronnen die je los kunt updaten, plus een synthese die altijd over
álle bronnen heen een interpretatie geeft — zonder elke keer alle transcripten
opnieuw in te lezen.

## Vaste infra (IDs)
- Dashboard (synthese-pagina): Notion `38ccb9b9-b2b4-8144-b3bc-d6a16eae49bb`
- Parent: 🧭 MASTER BTC-bodem `373cb9b9-b2b4-8164-883b-f6aef0e39b97`
- Bronnen-feed (database): `data_source_id = 70f2072e-4fdf-4bd2-af4a-b279fe951971`
- Gekoppelde master-frames: F18 Metalen · F19 AI⇄liquiditeit · IPO Playbook (SPCX)

## Laag 1 — Bron (los, herhaalbaar)
Per geplakte bron exact dit, niets meer:
1. **10 punten**, NL, kort, concreet — getallen/targets/tickers, geen vage taal.
2. **Eén regel** `🔗 Bron: [titel](url)`. Geen URL? Eerlijk noteren
   "exacte URL niet gepind (geplakt transcript)" + kanaal/host. Nooit een
   video-ID gokken.
3. **Geen integrale transcripten** opslaan (auteursrecht) — smvt + link dekt het.
4. Schrijf de bron weg als **één rij** in de Bronnen-feed met properties:
   - `Titel`, `Spreker`, `Kanaal`, `Bron-URL`, `Datum`
   - `Sectoren` (multi): Crypto-BTC · Altcoins · Metalen · AI-Tech · Energie ·
     Macro-Fed · Geopolitiek · Aandelen · IPO
   - `Bias`: Bull · Bear · Neutraal · Mixed
   - `Impact-laag` (multi): F18 · F19 · Energie · BTC-ankers · IPO-Playbook
   - `Kernclaim` (1 zin) · `Convergentie/spanning` (bevestigt of botst met base case)
   - `Status`: Nieuw · Verwerkt
   - Body = de 10 punten + 🔗 Bron.

**Verify-first scoping (token-bewust):** alleen het *geverifieerd anker*
(prijzen, market caps, IPO-cijfers) web-checken met ≥2 bronnen. Bron-claims zijn
"wat de spreker zei" → niet verifiëren, niet zoeken.

## Laag 2 — Synthese (incrementeel, plan-veilig)
⚠️ SQL-tools (`query_data_sources` / `query_database_view`) vereisen Notion
Business + AI — niet beschikbaar op dit plan. NIET gebruiken (harde plan-error).
Lees in plaats daarvan:
- De staande synthese-conclusie + 3-scenario-tabel op het dashboard.
- Alleen de **Nieuw**-rijen via `notion-search` op de data source
  (`data_source_url = collection://70f2072e-4fdf-4bd2-af4a-b279fe951971`),
  property `Status = Nieuw`. Lees per rij alleen de properties (`Kernclaim`,
  `Sectoren`, `Bias`, `Impact-laag`, `Convergentie/spanning`) — niet de
  10-punts bodies.

Werkset blijft zo onder de ~25-cap van search → compleet. Na verwerking:
flip elke verwerkte rij naar `Status = Verwerkt`. Daarna:
1. **Geverifieerd anker** (sectie 0): actuele prijzen, ≥2 bronnen, wekelijks vers.
2. **Per sector** convergentie + spanning (groepeer op `Sectoren`).
3. **Cross-sector impact-map**: welke sector dríjft welke. Vaste kern-keten:
   AI-capex → consument (memory) → aandelen-fragiliteit (circulair geld) →
   crypto-liquiditeit → metalen → energie/Fed. Energie = de fuse op het Fed-pad
   (WTI $58-60 = trigger).
4. **3-scenario eindconclusie** (geen enkel pad): basecase domino-flush /
   melt-up-eerst / energie-disinflatie-turn — elk met trigger + subjectieve kans.
5. **Wat verandert voor het plan**, gemapt op F18 / F19 / energie / IPO Playbook.
6. CTA onderaan in blockquote (emoji + vette titel + Notion-link).

> ⚠️ Volledige her-aggregatie over de hele historie (niet incrementeel) kan niet
> via search alleen (max ~25 rijen) — dan rijen één voor één fetchen. Voor de
> normale incrementele run nooit nodig.

## Token-discipline
- Bron toevoegen = 1 rij aanmaken; **nooit de hele synthese-pagina herschrijven**.
- Synthese leest de staande conclusie + alleen Nieuw-rijen (properties), niet
  bodies, niet de hele tabel.
- Alleen sectie 0 web-checken; bron-claims niet.
- Batch: alle geplakte transcripts in één pass verwerken.
- Titel-teller (`— N bronnen`) bijwerken; geen losse bevestiging tussen items.

## Output
Update de synthese-conclusie + 3-scenario-tabel op het dashboard. Meld terug:
welke bronnen toegevoegd, wat de netto-verandering in de interpretatie is, en
één eerlijke leertip (welke bron wél/niet nieuwe sector-info gaf).
