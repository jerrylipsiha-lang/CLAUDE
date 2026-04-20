"""Генерация превью-картинок основных графиков дашборда в previews/."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))

from lib.data import END_YEAR, START_YEAR, SECTORS, build_panel, city_year_panel
from lib.metrics import (
    gini, herfindahl, location_quotient, lorenz_curve, primacy_index,
    shift_share, theil, zipf_fit,
)
from lib.theme import ACCENT, CATEGORICAL, PRIMARY, SUCCESS, apply_plotly_theme

apply_plotly_theme()

OUT = Path(__file__).parent / "previews"
OUT.mkdir(exist_ok=True)

panel = build_panel()
cy = city_year_panel()
snap = cy[cy["год"] == END_YEAR]


def save(fig: go.Figure, name: str, width: int = 1400, height: int = 700) -> None:
    path = OUT / f"{name}.png"
    fig.update_layout(width=width, height=height)
    fig.write_image(path, scale=2)
    print(f"  wrote {path.name}  ({path.stat().st_size//1024} KB)")


print("Generating previews...")

fig = px.scatter(
    snap, x="долгота", y="широта", size="ВРП_млрд", color="ВРП_млрд",
    hover_name="город", color_continuous_scale="Blues", size_max=70,
    text="город",
    title=f"Распределение ВРП по агломерациям РФ, {END_YEAR}",
)
fig.update_traces(textposition="top center", textfont_size=10)
fig.update_layout(
    coloraxis_colorbar=dict(title="ВРП, млрд ₽"),
    xaxis=dict(title="Долгота", range=[18, 138]),
    yaxis=dict(title="Широта", range=[40, 68]),
    plot_bgcolor="#f7f9fc",
    margin=dict(l=40, r=10, t=60, b=40),
)
save(fig, "01_map")

top = snap.nlargest(15, "ВРП_млрд").sort_values("ВРП_млрд")
fig = px.bar(top, x="ВРП_млрд", y="город", orientation="h",
             color="ВРП_млрд", color_continuous_scale="Blues",
             text="ВРП_млрд",
             title=f"Топ-15 агломераций по ВРП, {END_YEAR}")
fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig.update_layout(coloraxis_showscale=False, xaxis_title="ВРП, млрд ₽",
                  yaxis_title="", margin=dict(l=180, r=80, t=60, b=40))
save(fig, "02_top_cities", height=700)

rows = []
for y in range(START_YEAR, END_YEAR + 1):
    v = cy[cy["год"] == y]["ВРП_млрд"]
    rows.append({"год": y, "HHI": herfindahl(v), "Джини": gini(v),
                 "Тейл": theil(v), "Primacy": primacy_index(v)})
dyn = pd.DataFrame(rows)

fig = go.Figure()
fig.add_trace(go.Scatter(x=dyn["год"], y=dyn["HHI"], name="HHI (лев.)",
                          line=dict(color=PRIMARY, width=3), mode="lines+markers"))
fig.add_trace(go.Scatter(x=dyn["год"], y=dyn["Джини"], name="Джини (прав.)",
                          line=dict(color=ACCENT, width=3, dash="dash"),
                          mode="lines+markers", yaxis="y2"))
fig.add_trace(go.Scatter(x=dyn["год"], y=dyn["Тейл"], name="Тейл (прав.)",
                          line=dict(color=SUCCESS, width=3, dash="dot"),
                          mode="lines+markers", yaxis="y2"))
fig.update_layout(
    title="Эволюция концентрации ВРП, 2010–2023",
    yaxis=dict(title="HHI"),
    yaxis2=dict(title="Джини / Тейл", overlaying="y", side="right"),
    legend=dict(orientation="h", y=-0.15),
)
save(fig, "03_concentration_dynamics")

lq = location_quotient(panel[panel["год"] == END_YEAR])
lq_sorted = lq.loc[lq.max(axis=1).sort_values(ascending=False).index]
fig = px.imshow(lq_sorted, color_continuous_scale="RdBu_r",
                color_continuous_midpoint=1.0, aspect="auto", text_auto=".2f",
                title=f"Матрица локализации (LQ), {END_YEAR} · занятость")
fig.update_layout(coloraxis_colorbar=dict(title="LQ"), xaxis_title="", yaxis_title="",
                  margin=dict(l=180, r=60, t=60, b=180))
fig.update_xaxes(tickangle=-35)
save(fig, "04_lq_heatmap", height=720)

struct = panel[panel["год"] == END_YEAR].groupby(
    ["город", "отрасль"], as_index=False)["ВРП_млрд"].sum()
order = struct.groupby("город")["ВРП_млрд"].sum().sort_values(ascending=False).index.tolist()
fig = px.bar(struct, x="город", y="ВРП_млрд", color="отрасль",
             category_orders={"город": order, "отрасль": SECTORS},
             barmode="stack",
             title=f"Отраслевая структура ВРП городов, {END_YEAR}")
fig.update_layout(xaxis_title="", yaxis_title="ВРП, млрд ₽", legend_title="")
fig.update_xaxes(tickangle=-35)
save(fig, "05_sector_structure", height=650)

ss = shift_share(panel, START_YEAR, END_YEAR).sort_values("всего", ascending=True)
fig = go.Figure()
fig.add_trace(go.Bar(y=ss["город"], x=ss["NS_нац_рост"], orientation="h",
                     name="NS · национальный рост", marker_color=PRIMARY))
fig.add_trace(go.Bar(y=ss["город"], x=ss["IM_отраслевой"], orientation="h",
                     name="IM · отраслевой микс", marker_color=ACCENT))
fig.add_trace(go.Bar(y=ss["город"], x=ss["CS_конкурентный"], orientation="h",
                     name="CS · конкурентный сдвиг", marker_color=SUCCESS))
fig.update_layout(barmode="relative",
                  title=f"Shift-share декомпозиция Δ занятости, {START_YEAR} → {END_YEAR}",
                  xaxis_title="Вклад, тыс. чел.", yaxis_title="",
                  legend=dict(orientation="h", y=-0.08),
                  margin=dict(l=180, r=40, t=60, b=80))
save(fig, "06_shift_share", height=700)

x, y = lorenz_curve(snap["ВРП_млрд"])
g = gini(snap["ВРП_млрд"])
fig = go.Figure()
fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], line=dict(color="#999", dash="dash"),
                          name="Абсолютное равенство"))
fig.add_trace(go.Scatter(x=x, y=y, fill="tonexty",
                          fillcolor="rgba(31, 78, 140, 0.18)",
                          line=dict(color=PRIMARY, width=3),
                          name=f"Лоренц (Джини = {g:.3f})"))
fig.update_layout(
    title=f"Кривая Лоренца по ВРП, {END_YEAR}",
    xaxis=dict(title="Кумулятивная доля городов", tickformat=".0%", range=[0, 1]),
    yaxis=dict(title="Кумулятивная доля ВРП", tickformat=".0%", range=[0, 1]),
)
save(fig, "07_lorenz", width=850, height=700)

beta, r2 = zipf_fit(snap["ВРП_млрд"])
sorted_v = np.sort(snap["ВРП_млрд"].to_numpy())[::-1]
ranks = np.arange(1, len(sorted_v) + 1)
fig = px.scatter(x=sorted_v, y=ranks, log_x=True, log_y=True,
                 labels={"x": "ВРП, млрд ₽", "y": "Ранг"},
                 title=f"Правило Ципфа: β = {beta:.2f}, R² = {r2:.2f}")
fig.update_traces(marker=dict(size=12, color=PRIMARY))
save(fig, "08_zipf", width=850, height=700)

city = "Казань"
lq_profile = lq.loc[city].sort_values(ascending=True)
fig = px.bar(x=lq_profile.values, y=lq_profile.index, orientation="h",
             color=lq_profile.values, color_continuous_scale="RdBu_r",
             color_continuous_midpoint=1.0,
             title=f"LQ профиль города: {city}, {END_YEAR}")
fig.add_vline(x=1.0, line_dash="dash", line_color="#666")
fig.update_layout(coloraxis_showscale=False,
                  xaxis_title="LQ (занятость)", yaxis_title="",
                  margin=dict(l=260, r=40, t=60, b=60))
save(fig, "09_city_lq_profile")

evo_raw = panel[panel["город"] == city].groupby(["год", "отрасль"])["ВРП_млрд"].sum().reset_index()
totals = evo_raw.groupby("год")["ВРП_млрд"].transform("sum")
evo_raw["доля"] = evo_raw["ВРП_млрд"] / totals
evo = evo_raw
fig = px.area(evo, x="год", y="доля", color="отрасль",
              category_orders={"отрасль": SECTORS},
              title=f"Эволюция отраслевой структуры: {city}")
fig.update_layout(yaxis_tickformat=".0%",
                  yaxis_title="Доля в ВРП", xaxis_title="", legend_title="")
save(fig, "10_city_evolution")

print(f"\nDone. {len(list(OUT.glob('*.png')))} previews generated.")
