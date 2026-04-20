"""Страница: отраслевая структура и индекс локализации (LQ)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import END_YEAR, START_YEAR, SECTORS, build_panel
from lib.metrics import location_quotient

st.title("Отраслевая структура экономики")
st.markdown(
    '<p class="section-caption">'
    "Вклад отраслей, специализация городов (LQ) и её эволюция во времени</p>",
    unsafe_allow_html=True,
)

panel = build_panel()

with st.sidebar:
    st.header("Параметры")
    year = st.slider("Год", START_YEAR, END_YEAR, END_YEAR, key="sec_year")
    value_col = st.radio(
        "База расчёта LQ",
        ["занятость_тыс", "ВРП_млрд"],
        horizontal=True,
        key="sec_base",
    )

snap = panel[panel["год"] == year]

tab1, tab2, tab3 = st.tabs(
    ["Структура ВРП", "Индекс локализации (LQ)", "Эволюция специализации"]
)

with tab1:
    st.subheader("Отраслевая структура ВРП городов")
    struct = (
        snap.groupby(["город", "отрасль"], as_index=False)["ВРП_млрд"]
        .sum()
    )
    order = (
        struct.groupby("город")["ВРП_млрд"].sum().sort_values(ascending=False).index.tolist()
    )
    fig = px.bar(
        struct,
        x="город",
        y="ВРП_млрд",
        color="отрасль",
        category_orders={"город": order, "отрасль": SECTORS},
        barmode="stack",
    )
    fig.update_layout(
        height=520,
        xaxis_title="",
        yaxis_title="ВРП, млрд ₽",
        legend_title="",
    )
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, width="stretch")

    st.markdown("**Вклад отрасли в совокупный ВРП всех 20 городов**")
    agg = snap.groupby("отрасль", as_index=False)["ВРП_млрд"].sum()
    agg["доля"] = agg["ВРП_млрд"] / agg["ВРП_млрд"].sum()
    fig = px.treemap(
        agg, path=["отрасль"], values="ВРП_млрд",
        color="доля", color_continuous_scale="Blues",
    )
    fig.update_layout(height=360, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, width="stretch")

with tab2:
    st.subheader(f"Матрица LQ · база: {value_col}")
    st.markdown(
        '<p class="section-caption">'
        "LQ > 1.25 — выраженная специализация; LQ < 0.75 — недопредставленность</p>",
        unsafe_allow_html=True,
    )
    lq = location_quotient(snap, value_col=value_col)
    lq_sorted = lq.loc[lq.max(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(
        lq_sorted,
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=1.0,
        aspect="auto",
        text_auto=".2f",
    )
    fig.update_layout(
        height=640,
        xaxis_title="",
        yaxis_title="",
        coloraxis_colorbar=dict(title="LQ"),
    )
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(fig, width="stretch")

    st.markdown("**Наиболее специализированные пары город × отрасль**")
    stacked = (
        lq.stack().reset_index()
        .rename(columns={0: "LQ"})
        .sort_values("LQ", ascending=False)
        .head(15)
    )
    st.dataframe(stacked, width="stretch", hide_index=True)

with tab3:
    st.subheader("Как менялась специализация во времени")
    city = st.selectbox("Город", sorted(panel["город"].unique()), key="sec_city")
    history = panel[panel["город"] == city]
    evolution = (
        history.groupby(["год", "отрасль"])["ВРП_млрд"]
        .sum()
        .groupby(level=0)
        .apply(lambda s: s / s.sum())
        .reset_index(name="доля")
    )
    fig = px.area(
        evolution,
        x="год", y="доля", color="отрасль",
        category_orders={"отрасль": SECTORS},
    )
    fig.update_layout(
        height=440,
        yaxis_tickformat=".0%",
        yaxis_title="Доля отрасли в ВРП города",
        xaxis_title="",
        legend_title="",
    )
    st.plotly_chart(fig, width="stretch")
