"""Главная страница: ключевые показатели и визуальный обзор."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from lib.data import END_YEAR, START_YEAR, build_panel, city_year_panel
from lib.metrics import cagr, gini, herfindahl, primacy_index
from lib.theme import ACCENT, PRIMARY

st.title("Концентрация экономической активности в агломерациях РФ")
st.markdown(
    '<p class="section-caption">Аналитический дашборд · 20 крупнейших '
    "городов · 2010–2023 · синтетические данные</p>",
    unsafe_allow_html=True,
)

panel = build_panel()
cy = city_year_panel()

with st.sidebar:
    st.header("Параметры обзора")
    year = st.slider("Год", START_YEAR, END_YEAR, END_YEAR)
    st.caption(
        "Все страницы используют общий кеш данных. "
        "Фильтры на каждой странице независимые."
    )

snap = cy[cy["год"] == year].copy()
prev = cy[cy["год"] == year - 1].copy() if year > START_YEAR else snap

total_grp = snap["ВРП_млрд"].sum()
total_pop = snap["население_млн"].sum()
total_emp = snap["занятость_тыс"].sum()
prev_grp = prev["ВРП_млрд"].sum()

hhi = herfindahl(snap["ВРП_млрд"])
gi = gini(snap["ВРП_млрд"])
prim = primacy_index(snap["ВРП_млрд"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    "Суммарный ВРП",
    f"{total_grp/1000:,.2f} трлн ₽".replace(",", " "),
    f"{(total_grp/prev_grp - 1)*100:+.1f}% г/г" if prev_grp else None,
)
c2.metric(
    "Население",
    f"{total_pop:,.1f} млн".replace(",", " "),
)
c3.metric(
    "Занятость",
    f"{total_emp/1000:,.1f} млн чел.".replace(",", " "),
)
c4.metric(
    "HHI концентрации ВРП",
    f"{hhi:,.0f}".replace(",", " "),
    help="Индекс Херфиндаля–Хиршмана. > 2500 — высокая концентрация.",
)
c5.metric(
    "Джини",
    f"{gi:.3f}",
    help="Неравенство ВРП между городами: 0 — равенство, 1 — максимальное неравенство.",
)

st.markdown("---")

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Географическое распределение ВРП")
    fig = px.scatter_geo(
        snap,
        lat="широта",
        lon="долгота",
        size="ВРП_млрд",
        color="ВРП_млрд",
        hover_name="город",
        hover_data={
            "ВРП_млрд": ":.0f",
            "население_млн": ":.2f",
            "округ": True,
            "широта": False,
            "долгота": False,
        },
        color_continuous_scale="Blues",
        size_max=55,
    )
    fig.update_geos(
        projection_type="mercator",
        lataxis_range=[41, 68],
        lonaxis_range=[19, 135],
        showcountries=True,
        countrycolor="#c9d2df",
        landcolor="#f7f9fc",
        showland=True,
    )
    fig.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="ВРП, млрд ₽"),
    )
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Топ-10 по ВРП")
    top = snap.nlargest(10, "ВРП_млрд").sort_values("ВРП_млрд")
    fig = px.bar(
        top,
        x="ВРП_млрд",
        y="город",
        orientation="h",
        color="ВРП_млрд",
        color_continuous_scale="Blues",
        text="ВРП_млрд",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        height=480,
        showlegend=False,
        coloraxis_showscale=False,
        xaxis_title="ВРП, млрд ₽",
        yaxis_title="",
    )
    st.plotly_chart(fig, width="stretch")

st.markdown("---")

st.subheader("Динамика концентрации 2010–2023")
st.markdown(
    '<p class="section-caption">'
    "Как менялась концентрация экономической активности между городами</p>",
    unsafe_allow_html=True,
)

trend = []
for y in range(START_YEAR, END_YEAR + 1):
    sub = cy[cy["год"] == y]
    trend.append({
        "год": y,
        "HHI": herfindahl(sub["ВРП_млрд"]),
        "Джини": gini(sub["ВРП_млрд"]),
        "Доля Москвы": primacy_index(sub["ВРП_млрд"]),
    })
import pandas as pd  # noqa: E402

trend_df = pd.DataFrame(trend)

t1, t2, t3 = st.tabs(["HHI", "Коэффициент Джини", "Доля крупнейшего города"])
with t1:
    fig = px.line(trend_df, x="год", y="HHI", markers=True)
    fig.update_traces(line_color=PRIMARY, line_width=3)
    fig.update_layout(height=320, yaxis_title="HHI (0–10000)")
    fig.add_hline(y=2500, line_dash="dot", line_color=ACCENT,
                  annotation_text="порог высокой концентрации")
    st.plotly_chart(fig, width="stretch")
with t2:
    fig = px.line(trend_df, x="год", y="Джини", markers=True)
    fig.update_traces(line_color=PRIMARY, line_width=3)
    fig.update_layout(height=320, yaxis_title="Коэффициент Джини")
    st.plotly_chart(fig, width="stretch")
with t3:
    fig = px.line(trend_df, x="год", y="Доля Москвы", markers=True)
    fig.update_traces(line_color=PRIMARY, line_width=3)
    fig.update_layout(height=320, yaxis_title="Доля крупнейшего города", yaxis_tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

st.markdown("---")

st.subheader("Среднегодовые темпы роста ВРП, 2010–2023")
first = cy[cy["год"] == START_YEAR].set_index("город")["ВРП_млрд"]
last = cy[cy["год"] == END_YEAR].set_index("город")["ВРП_млрд"]
growth = (
    pd.DataFrame({
        "город": first.index,
        "CAGR": [cagr(first[c], last[c], END_YEAR - START_YEAR) for c in first.index],
    })
    .sort_values("CAGR", ascending=True)
)
fig = px.bar(
    growth,
    x="CAGR",
    y="город",
    orientation="h",
    color="CAGR",
    color_continuous_scale="RdBu",
    color_continuous_midpoint=growth["CAGR"].median(),
)
fig.update_layout(
    height=520,
    xaxis_tickformat=".1%",
    xaxis_title="CAGR ВРП",
    yaxis_title="",
    coloraxis_showscale=False,
)
st.plotly_chart(fig, width="stretch")

with st.expander("Показать исходные агрегаты"):
    st.dataframe(
        snap.drop(columns=["широта", "долгота"]).reset_index(drop=True),
        width="stretch",
    )
    csv = snap.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Скачать CSV",
        csv,
        file_name=f"agglomerations_{year}.csv",
        mime="text/csv",
    )
