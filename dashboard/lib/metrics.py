"""Экономические индексы: HHI, Джини, Тейл, LQ, shift-share, primacy, Zipf."""
from __future__ import annotations

import numpy as np
import pandas as pd


def herfindahl(values: pd.Series) -> float:
    """Индекс Херфиндаля–Хиршмана. Возвращает значение в шкале 0..10000.

    HHI = 10000 · Σ (s_i)², где s_i — доля наблюдения i в сумме.
    < 1500 — низкая концентрация, 1500–2500 — умеренная, > 2500 — высокая.
    """
    v = values.to_numpy(dtype=float)
    total = v.sum()
    if total <= 0:
        return np.nan
    shares = v / total
    return float(np.sum(shares**2) * 10000)


def gini(values: pd.Series) -> float:
    """Коэффициент Джини: 0 — абсолютное равенство, 1 — максимальное неравенство."""
    v = np.sort(values.to_numpy(dtype=float))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return np.nan
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * v) / (n * v.sum())) - (n + 1) / n)


def theil(values: pd.Series) -> float:
    """Индекс Тейла T (decomposable entropy-based inequality)."""
    v = values.to_numpy(dtype=float)
    v = v[v > 0]
    if len(v) == 0:
        return np.nan
    mean = v.mean()
    return float(np.sum((v / mean) * np.log(v / mean)) / len(v))


def location_quotient(
    panel: pd.DataFrame,
    entity_col: str = "город",
    sector_col: str = "отрасль",
    value_col: str = "занятость_тыс",
) -> pd.DataFrame:
    """Location Quotient: степень отраслевой специализации города.

    LQ_ij = (E_ij / E_i) / (E_j / E)
    LQ > 1.25 — выраженная специализация; LQ < 0.75 — недопредставленность.
    """
    tot_entity = panel.groupby(entity_col)[value_col].sum()
    tot_sector = panel.groupby(sector_col)[value_col].sum()
    grand_total = panel[value_col].sum()

    matrix = panel.pivot_table(
        index=entity_col, columns=sector_col, values=value_col, aggfunc="sum"
    )
    lq = matrix.div(tot_entity, axis=0).div(tot_sector / grand_total, axis=1)
    return lq.round(3)


def primacy_index(values: pd.Series) -> float:
    """Индекс примаси: доля крупнейшего наблюдения в сумме (City Primacy)."""
    v = values.to_numpy(dtype=float)
    if v.sum() == 0:
        return np.nan
    return float(v.max() / v.sum())


def zipf_fit(values: pd.Series) -> tuple[float, float]:
    """Оценивает показатель Ципфа: log(rank) = a − β · log(size).

    Возвращает (β, R²). β ≈ 1 соответствует классическому правилу Ципфа.
    """
    sizes = np.sort(values.to_numpy(dtype=float))[::-1]
    sizes = sizes[sizes > 0]
    if len(sizes) < 3:
        return (np.nan, np.nan)
    ranks = np.arange(1, len(sizes) + 1)
    x = np.log(sizes)
    y = np.log(ranks)
    beta, intercept = np.polyfit(x, y, 1)
    y_hat = beta * x + intercept
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot else np.nan
    return (float(-beta), float(r2))


def shift_share(
    panel: pd.DataFrame,
    year_from: int,
    year_to: int,
    value_col: str = "занятость_тыс",
) -> pd.DataFrame:
    """Shift-share декомпозиция прироста занятости по городам.

    ΔE_i = NS_i + IM_i + CS_i, где
      NS — национальный рост,
      IM — отраслевой эффект (industry mix),
      CS — конкурентный сдвиг (competitive shift).
    """
    a = panel[panel["год"] == year_from]
    b = panel[panel["год"] == year_to]

    a_nat = a[value_col].sum()
    b_nat = b[value_col].sum()
    g_nat = b_nat / a_nat - 1

    g_sector = (
        b.groupby("отрасль")[value_col].sum()
        / a.groupby("отрасль")[value_col].sum()
        - 1
    )

    rows = []
    for city in a["город"].unique():
        a_city = a[a["город"] == city].set_index("отрасль")[value_col]
        b_city = b[b["город"] == city].set_index("отрасль")[value_col]
        e0 = a_city.sum()
        ns = e0 * g_nat
        im = float(((g_sector - g_nat) * a_city).sum())
        cs = float(
            ((b_city / a_city - 1) - g_sector).mul(a_city, fill_value=0).sum()
        )
        rows.append({
            "город": city,
            "NS_нац_рост": ns,
            "IM_отраслевой": im,
            "CS_конкурентный": cs,
            "всего": ns + im + cs,
        })
    return pd.DataFrame(rows).round(2)


def cagr(start: float, end: float, years: int) -> float:
    """Среднегодовой темп роста (CAGR)."""
    if start <= 0 or years <= 0:
        return np.nan
    return float((end / start) ** (1 / years) - 1)


def lorenz_curve(values: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Точки кривой Лоренца: (кум. доля наблюдений, кум. доля объёма)."""
    v = np.sort(values.to_numpy(dtype=float))
    if v.sum() == 0:
        return np.array([0, 1]), np.array([0, 1])
    cum = np.cumsum(v) / v.sum()
    x = np.arange(1, len(v) + 1) / len(v)
    return np.concatenate(([0], x)), np.concatenate(([0], cum))
