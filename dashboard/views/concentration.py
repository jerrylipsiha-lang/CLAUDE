"""Страница: концентрация и неравенство (HHI, Джини, Тейл, Лоренц, Ципф)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import END_YEAR, START_YEAR, city_year_panel
from lib.metrics import (
    gini, herfindahl, lorenz_curve, primacy_index, theil, zipf_fit,
)
from lib.theme import ACCENT, DANGER, PRIMARY, SUCCESS

st.title("Индексы концентрации и неравенства")
st.markdown(
    '<p class="section-caption">'
    "HHI, Джини, Тейл, кривая Лоренца и проверка правила Ципфа</p>",
    unsafe_allow_html=True,
)

cy = city_year_panel()

with st.sidebar:
    st.header("Параметры")
    year = st.slider("Год", START_YEAR, END_YEAR, END_YEAR, key="conc_year")
    metric = st.selectbox(
        "Показатель",
        ["ВРП_млрд", "занятость_тыс", "инвестиции_млрд", "население_млн"],
        key="conc_metric",
    )

snap = cy[cy["год"] == year]
values = snap[metric]

c1, c2, c3, c4 = st.columns(4)
c1.metric("HHI", f"{herfindahl(values):,.0f}".replace(",", " "))
c2.metric("Джини", f"{gini(values):.3f}")
c3.metric("Тейл", f"{theil(values):.3f}")
c4.metric("Доля лидера", f"{primacy_index(values):.1%}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["Динамика индексов", "Кривая Лоренца", "Правило Ципфа (rank-size)"]
)

with tab1:
    st.subheader("Эволюция концентрации 2010–2023")
    rows = []
    for y in range(START_YEAR, END_YEAR + 1):
        v = cy[cy["год"] == y][metric]
        rows.append({
            "год": y,
            "HHI": herfindahl(v),
            "Джини": gini(v),
            "Тейл": theil(v),
            "Primacy": primacy_index(v),
        })
    dyn = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dyn["год"], y=dyn["HHI"], name="HHI (лев.)",
        line=dict(color=PRIMARY, width=3), mode="lines+markers",
    ))
    fig.add_trace(go.Scatter(
        x=dyn["год"], y=dyn["Джини"], name="Джини (прав.)",
        line=dict(color=ACCENT, width=3, dash="dash"),
        mode="lines+markers", yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        x=dyn["год"], y=dyn["Тейл"], name="Тейл (прав.)",
        line=dict(color=SUCCESS, width=3, dash="dot"),
        mode="lines+markers", yaxis="y2",
    ))
    fig.update_layout(
        height=420,
        yaxis=dict(title="HHI (0–10000)"),
        yaxis2=dict(title="Джини / Тейл", overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig, width="stretch")

with tab2:
    st.subheader(f"Кривая Лоренца · {year}")
    x, y = lorenz_curve(values)
    g = gini(values)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        line=dict(color="#999", dash="dash"),
        name="Абсолютное равенство",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=y, fill="tonexty",
        fillcolor="rgba(31, 78, 140, 0.18)",
        line=dict(color=PRIMARY, width=3),
        name=f"Лоренц (Джини = {g:.3f})",
    ))
    fig.update_layout(
        height=480,
        xaxis=dict(title="Кумулятивная доля городов", tickformat=".0%", range=[0, 1]),
        yaxis=dict(title=f"Кумулятивная доля {metric}", tickformat=".0%", range=[0, 1]),
    )
    st.plotly_chart(fig, width="stretch")

with tab3:
    st.subheader("Rank–size distribution")
    beta, r2 = zipf_fit(values)
    sorted_vals = np.sort(values.to_numpy())[::-1]
    ranks = np.arange(1, len(sorted_vals) + 1)

    fig = px.scatter(
        x=sorted_vals, y=ranks,
        log_x=True, log_y=True,
        labels={"x": metric, "y": "Ранг"},
    )
    fig.update_traces(marker=dict(size=11, color=PRIMARY))
    fig.update_layout(height=480)
    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    col1.metric(
        "Оценка β (показатель Ципфа)",
        f"{beta:.3f}",
        help="β ≈ 1 — классическое правило Ципфа",
    )
    col2.metric("R²", f"{r2:.3f}")
    if abs(beta - 1) < 0.15:
        st.success("Распределение близко к классическому правилу Ципфа (β ≈ 1).")
    elif beta > 1:
        st.warning(f"β = {beta:.2f} > 1: гипертрофия лидера (несколько крупных городов доминируют).")
    else:
        st.info(f"β = {beta:.2f} < 1: распределение более равномерное, чем предполагает Ципф.")
