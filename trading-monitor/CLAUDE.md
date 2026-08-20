# CLAUDE.md — trading-project

Staande projectregels voor het trading-project (ALT-monitor, dip-scan, watchlist).

> Backtest-validatie: vertaling van de 9.000-backtests-les naar staande projectregels.

## Verify-first geldt OOK voor strategieën, niet alleen voor prijzen

Zoals ik koersen/feiten nooit op een patroon gok, gok ik een edge nooit op één
backtest. **Eén mooie backtest = waarschijnlijk overfit** — 44% van strategieën
die in-sample sterk lijken, faalt out-of-sample. Een strategie/regel telt pas als
"echt" als hij door de validatie-gauntlet is (`validate.py`):

- walk-forward (tunen op oud, scoren op ongezien),
- OOS Sharpe > 0,5 · maxDD < 35% · min. 30 trades,
- overfit-ratio OOS/IS ≥ 0,5 (IS≫OOS = curve-fit),
- bootstrap 500× met Sharpe-p05 > 0 (edge ≠ geluk).

Faalt één check → de regel gaat niet live. Geen uitzondering "in dit ene pad werkt het".

## Edge-hiërarchie

1. **Mean-reversion = de ruggengraat.** Enige familie die breed (30 assets, 15 jaar)
   stand-alone overleeft. Dip-buy bouwt hierop.
2. **Trend/momentum = situationeel.** Werkt op specifieke sterke namen (AAPL, NVDA)
   of regime-gated, niet breed op autopilot. Stand-alone trend op één asset ≈ nul.
3. **Cross-sectional momentum** (rank long sterkste / short zwakste) > stand-alone
   momentum. Als ik momentum gebruik, dan zo.

## Bouwvolgorde van élk trading-systeem

basis-edge (mean-reversion) → risk & sizing → ongecorreleerde signalen stapelen →
regime-gate (mean-reversion in chop, momentum in trend; hidden-markov of
trend-sterkte/vol). Nooit in omgekeerde volgorde: een signaal zonder edge
oppoetsen met sizing en regimes is lippenstift op ruis.

## Koppeling

- Validatie-engine: `validate.py` (gauntlet + walk-forward + bootstrap + regime).
- Dip-scan skill: SKILL.md draagt de gauntlet als verplichte poort vóór de watchlist.
- Systematische driver tracker (F18-gat): gebruik `regime_series()` als startpunt —
  welk regime staat de markt in → welke familie zet ik aan.
