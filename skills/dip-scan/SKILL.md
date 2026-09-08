---
name: dip-scan
description: Dagelijkse dip-scan over de watchlist — mean-reversion dip-buy-signalen zoeken, valideren en pas daarna live zetten. Gebruik deze skill bij het draaien van de dagelijkse sweep, bij het toevoegen van een nieuwe ticker of regel aan de watchlist, en bij elke vraag of een trading-regel "echt" is. Elke nieuwe regel moet verplicht door de validatie-gauntlet in validate.py voordat hij in watchlist.txt mag.
---

# Dip-scan

Dagelijkse sweep over de watchlist op mean-reversion dip-buy-signalen, met een
verplichte validatiepoort ervoor.

De kernregel: **de watchlist is een gevalideerde set, geen verzamelbak.** Een
ticker of regel komt er pas in nadat hij door `validate.Gauntlet` is gekomen.

## Wanneer gebruik je dit

- de dagelijkse sweep draaien over de bestaande watchlist
- een nieuwe naam of regel overwegen voor de watchlist
- beoordelen of een backtest-resultaat een echte edge is of overfit

## Edge-hiërarchie (waar de dip-scan op staat)

De dip-scan is géén verzameling losse signalen — het is één **mean-reversion
dip-buy-edge** met lagen eromheen. Bouwvolgorde, van onder naar boven:

1. **Basis-edge = mean-reversion.** Koop wat te ver onder zijn gemiddelde is
   gezakt (RSI-snapback / Keltner-revert / Bollinger-revert). Dit is de enige
   familie die over 30 assets × 15 jaar breed positief blijft. Ruggengraat.
2. **Risk & sizing.** Per-trade sizing + stop. Saaie laag, maar bepaalt de
   drawdown — niet de winrate.
3. **Ongecorreleerde signalen.** Eén zwak signaal = ruis; meerdere die niet
   samen bewegen = iets echts. Combineer, stapel niet.
4. **Regime-gate.** Mean-reversion in **chop**, (cross-sectional) momentum in
   **trend**. Draai blind momentum op autopilot → faalt; regime-gated → werkt
   situationeel. Zie `regime_series()` in `validate.py`.

Trend/breakout-regels mogen in de watchlist, maar **alleen als regime-gated of
cross-sectional** (rank long sterkste / short zwakste) — stand-alone trend op
één asset scoort gemiddeld nul tot negatief.

## Validatie-gauntlet (VERPLICHT vóór een regel in de watchlist komt)

Geen enkele nieuwe dip-scan-regel of parameter-set gaat live zonder door
`validate.Gauntlet` heen. Eén mooie backtest = waarschijnlijk overfit.

```python
from validate import Gauntlet, mean_reversion_rsi

g = Gauntlet(min_sharpe=0.5, max_dd=0.35, min_overfit_ratio=0.5,
             min_trades=30, n_bootstrap=500)
verdict = g.run(prices, mean_reversion_rsi,
                {"period": [2, 3], "buy": [5, 10], "sell": [55, 65]})
print(verdict)              # ✅ PASS / ❌ FAIL + reden
if not verdict.passed:
    continue                # regel NIET toevoegen
```

De zes harde checks (alle OOS, op ongeziene data):

| Filter | Drempel | Waarom |
|---|---|---|
| Walk-forward | tunen op oud, scoren op ongezien | geen overfit op het verleden |
| OOS Sharpe | > 0,5 | risk-adjusted écht positief |
| Max drawdown | < 35% | niet fragiel |
| Overfit-ratio | OOS/IS Sharpe ≥ 0,5 | IS≫OOS = curve-fit, weggooien |
| Min. trades | ≥ 30 | statistisch viable, geen toeval |
| Bootstrap (500×) | Sharpe p05 > 0 | edge ≠ padafhankelijk geluk |

Regel: **faalt één filter → regel valt af.** Geen "maar in dit ene pad werkt het".

## Wat dit voor de dagelijkse sweep betekent

- De live sweep van de watchlist blijft draaien, maar de watchlist zelf is nu
  een **gevalideerde** set: elke ticker/regel is door de gauntlet.
- Nieuwe naam → eerst gauntlet op de historie, dan pas in `watchlist.txt`.
- Log per regel het verdict (Sharpe/maxDD/overfit/bootstrap) bij de regel, zodat
  je later ziet wáárom iets erin staat.

## API van validate.py

Een strategie is een functie `strategy(prices: pd.Series, **params) -> pd.Series`
die posities in `[-1, 1]` teruggeeft, geïndexeerd als `prices`. Long-only
mean-reversion = posities in `{0, 1}`.

| Functie | Doet |
|---|---|
| `Gauntlet(...).run(prices, strategy, param_grid)` | volledige poort → `Verdict` |
| `walk_forward(prices, strategy, param_grid, ...)` | tunen op oud, scoren op ongezien |
| `bootstrap(returns, n=500, seed=7)` | is de edge padafhankelijk geluk? |
| `regime_series(prices, lookback=40, hmm=False)` | chop vs. trend, voor de regime-gate |
| `mean_reversion_rsi(prices, period, buy, sell)` | referentie-strategie (ruggengraat) |
| `trend_ma_cross(prices, fast, slow)` | referentie-trendregel (alleen regime-gated) |
| `sharpe` · `max_drawdown` · `n_trades` · `strategy_returns` | losse statistieken |

Posities werken op de **volgende** bar (`strategy_returns` shift't met 1), dus
er zit geen look-ahead in de resultaten.

Afhankelijkheden: `numpy`, `pandas`. `hmmlearn` is optioneel voor regime-detectie;
zonder die package valt `regime_series()` terug op trend-sterkte/vol.

## Herkomst

Bron: 9.000-backtests-analyse (Brendan). Kernles: één backtest is waardeloos —
44% van 'sterke' strategieën faalt out-of-sample. Mean-reversion is de enige
familie die breed stand-alone overleeft.

Dezelfde regels staan als staand projectbeleid in
[`trading-monitor/CLAUDE.md`](../../trading-monitor/CLAUDE.md).
