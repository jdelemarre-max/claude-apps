"""
validate.py — Validatie-gauntlet voor trading-regels (dip-scan skill).

Vertaalt de 9.000-backtests-les naar code: één backtest is waardeloos
(44% van 'sterke' strategieën faalt out-of-sample). Elke nieuwe dip-scan-
regel moet hier doorheen vóór hij in de watchlist/het systeem komt.

Lessen die hierin zitten:
  1. Walk-forward: tunen op oud, scoren op ongezien (geen overfit).
  2. Zes filters: Sharpe>0,5 OOS · maxDD<35% · overfit-degradatie · min. trades.
  3. Bootstrap (500×): is de edge echt of padafhankelijk geluk?
  4. Regime-gate: mean-reversion = ruggengraat; momentum alleen in trend.

Afhankelijkheden: numpy, pandas. (hmmlearn optioneel voor regimes; fallback ingebouwd.)
Een 'strategy' is een functie: strategy(prices: pd.Series, **params) -> pd.Series
posities in [-1, 1], geïndexeerd als prices. Long-only mean-reversion =
posities in {0, 1}.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Iterable
import numpy as np
import pandas as pd

ANN = 252  # handelsdagen


# ---------- kern-statistieken ----------
def strategy_returns(prices: pd.Series, positions: pd.Series) -> pd.Series:
    """Posities werken op de VOLGENDE bar (geen look-ahead)."""
    ret = prices.pct_change().fillna(0.0)
    return (positions.shift(1).fillna(0.0) * ret).rename("ret")


def sharpe(returns: pd.Series, ann: int = ANN) -> float:
    r = returns.dropna()
    sd = r.std()
    if sd == 0 or len(r) < 2:
        return 0.0
    return float(np.sqrt(ann) * r.mean() / sd)


def max_drawdown(returns: pd.Series) -> float:
    eq = (1 + returns.fillna(0)).cumprod()
    peak = eq.cummax()
    return float((eq / peak - 1).min())  # negatief, bv. -0.28


def n_trades(positions: pd.Series) -> int:
    """Aantal positie-wisselingen = ruwe trade-teller."""
    p = positions.fillna(0)
    return int((p != p.shift(1)).sum())


@dataclass
class Stats:
    sharpe: float
    max_dd: float
    trades: int
    total_return: float

    @classmethod
    def of(cls, prices, positions):
        r = strategy_returns(prices, positions)
        return cls(sharpe(r), max_drawdown(r), n_trades(positions),
                   float((1 + r).prod() - 1))


# ---------- walk-forward ----------
def _grid(param_grid: dict) -> Iterable[dict]:
    keys = list(param_grid)
    for combo in product(*(param_grid[k] for k in keys)):
        yield dict(zip(keys, combo))


def walk_forward(prices: pd.Series, strategy: Callable, param_grid: dict,
                 n_splits: int = 5, train_frac: float = 0.6):
    """
    Rollende splits. Per split: kies op het TRAIN-deel de params met de
    hoogste Sharpe, pas DIE toe op het ongeziene TEST-deel. Geef de
    aaneengeschakelde IS- en OOS-returns terug (voor de overfit-check).
    """
    n = len(prices)
    fold = n // (n_splits + 1)
    is_ret, oos_ret = [], []
    chosen = []
    for i in range(1, n_splits + 1):
        end = fold * (i + 1)
        split = fold * i + int(fold * (train_frac - 1))  # train/test-grens
        train, test = prices.iloc[:fold * i], prices.iloc[fold * i:end]
        if len(train) < 30 or len(test) < 10:
            continue
        best, best_s = None, -np.inf
        for params in _grid(param_grid):
            s = sharpe(strategy_returns(train, strategy(train, **params)))
            if s > best_s:
                best_s, best = s, params
        chosen.append(best)
        is_ret.append(strategy_returns(train, strategy(train, **best)))
        oos_ret.append(strategy_returns(test, strategy(test, **best)))
    return (pd.concat(is_ret) if is_ret else pd.Series(dtype=float),
            pd.concat(oos_ret) if oos_ret else pd.Series(dtype=float),
            chosen)


# ---------- bootstrap ----------
def bootstrap(returns: pd.Series, n: int = 500, seed: int = 7):
    """Reshuffle de returns n× → verdeling van Sharpe & maxDD. Geeft de
    5e-percentiel (slechte-paden) waarden = is de edge robuust of geluk?"""
    rng = np.random.default_rng(seed)
    r = returns.dropna().to_numpy()
    if len(r) < 10:
        return {"sharpe_p05": 0.0, "maxdd_p05": -1.0}
    sh, dd = [], []
    for _ in range(n):
        s = rng.choice(r, size=len(r), replace=True)
        ser = pd.Series(s)
        sh.append(sharpe(ser))
        dd.append(max_drawdown(ser))
    return {"sharpe_p05": float(np.percentile(sh, 5)),
            "maxdd_p05": float(np.percentile(dd, 5))}


# ---------- regime-gate ----------
def regime_series(prices: pd.Series, lookback: int = 40, hmm: bool = False) -> pd.Series:
    """
    'trend' vs 'chop' per bar. Default: trend-sterkte = |gem. return| / std
    over lookback (t-stat-achtig). Hoog = trend, laag = chop.
    hmm=True gebruikt hmmlearn (2 states) als beschikbaar, anders fallback.
    """
    ret = prices.pct_change()
    if hmm:
        try:
            from hmmlearn.hmm import GaussianHMM
            X = ret.dropna().to_numpy().reshape(-1, 1)
            m = GaussianHMM(n_components=2, covariance_type="diag",
                            n_iter=100, random_state=7).fit(X)
            states = pd.Series(m.predict(X), index=ret.dropna().index)
            # state met hoogste |mean| = trend
            means = {s: abs(X[states.values == s].mean()) for s in states.unique()}
            trend_state = max(means, key=means.get)
            lab = states.map(lambda s: "trend" if s == trend_state else "chop")
            return lab.reindex(prices.index).ffill().fillna("chop")
        except Exception:
            pass  # fallback hieronder
    strength = ret.rolling(lookback).mean().abs() / ret.rolling(lookback).std()
    med = strength.median()
    return (strength > med).map({True: "trend", False: "chop"}).fillna("chop")


# ---------- de gauntlet ----------
@dataclass
class Verdict:
    passed: bool
    reasons: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def __str__(self):
        head = "✅ PASS" if self.passed else "❌ FAIL"
        m = self.metrics
        body = (f"OOS Sharpe {m.get('oos_sharpe', 0):.2f} · maxDD "
                f"{m.get('oos_maxdd', 0):.0%} · trades {m.get('trades', 0)} · "
                f"overfit {m.get('overfit_ratio', 0):.2f} · "
                f"bootstrap Sharpe p05 {m.get('boot_sharpe_p05', 0):.2f}")
        tail = "" if self.passed else "\n   ↳ " + "; ".join(self.reasons)
        return f"{head} — {body}{tail}"


@dataclass
class Gauntlet:
    min_sharpe: float = 0.5      # OOS Sharpe-drempel
    max_dd: float = 0.35         # max drawdown (abs)
    min_overfit_ratio: float = 0.5   # OOS Sharpe / IS Sharpe; <0,5 = overfit
    min_trades: int = 30
    min_boot_sharpe: float = 0.0  # 5e-percentiel bootstrap-Sharpe moet > 0
    n_bootstrap: int = 500

    def run(self, prices: pd.Series, strategy: Callable, param_grid: dict,
            n_splits: int = 5, train_frac: float = 0.6) -> Verdict:
        is_r, oos_r, chosen = walk_forward(prices, strategy, param_grid,
                                           n_splits, train_frac)
        if oos_r.empty:
            return Verdict(False, ["te weinig data voor walk-forward"])
        is_s, oos_s = sharpe(is_r), sharpe(oos_r)
        oos_dd = max_drawdown(oos_r)
        trades = int((oos_r != 0).sum())  # OOS actieve bars als trade-proxy
        overfit = (oos_s / is_s) if is_s > 0 else 0.0
        boot = bootstrap(oos_r, self.n_bootstrap)

        reasons = []
        if oos_s < self.min_sharpe:
            reasons.append(f"OOS Sharpe {oos_s:.2f} < {self.min_sharpe}")
        if oos_dd < -self.max_dd:
            reasons.append(f"maxDD {oos_dd:.0%} > {self.max_dd:.0%}")
        if overfit < self.min_overfit_ratio:
            reasons.append(f"overfit-ratio {overfit:.2f} < {self.min_overfit_ratio} (IS≫OOS)")
        if trades < self.min_trades:
            reasons.append(f"trades {trades} < {self.min_trades}")
        if boot["sharpe_p05"] <= self.min_boot_sharpe:
            reasons.append(f"bootstrap Sharpe p05 {boot['sharpe_p05']:.2f} ≤ {self.min_boot_sharpe}")

        metrics = {"is_sharpe": is_s, "oos_sharpe": oos_s, "oos_maxdd": oos_dd,
                   "trades": trades, "overfit_ratio": overfit,
                   "boot_sharpe_p05": boot["sharpe_p05"], "chosen_params": chosen}
        return Verdict(len(reasons) == 0, reasons, metrics)


# ---------- voorbeeld-strategieën ----------
def mean_reversion_rsi(prices: pd.Series, period: int = 2, buy: int = 10,
                       sell: int = 60) -> pd.Series:
    """Long-only RSI-snapback (de familie die breed overleeft)."""
    d = prices.diff()
    up = d.clip(lower=0).rolling(period).mean()
    dn = (-d.clip(upper=0)).rolling(period).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    pos = pd.Series(0.0, index=prices.index)
    pos[rsi < buy] = 1.0
    pos[rsi > sell] = 0.0
    return pos.ffill().fillna(0.0)


def trend_ma_cross(prices: pd.Series, fast: int = 20, slow: int = 100) -> pd.Series:
    """Trend-volger (situationeel; alleen in trend-regime gebruiken)."""
    f, s = prices.rolling(fast).mean(), prices.rolling(slow).mean()
    return (f > s).astype(float).fillna(0.0)


if __name__ == "__main__":
    # smoke-test op synthetische reeks
    rng = np.random.default_rng(0)
    idx = pd.date_range("2010-01-01", periods=2000, freq="B")
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx)))), index=idx)
    g = Gauntlet()
    v = g.run(px, mean_reversion_rsi,
              {"period": [2, 3], "buy": [5, 10], "sell": [55, 65]})
    print("mean-reversion:", v)
    print("regimes:", regime_series(px).value_counts().to_dict())
