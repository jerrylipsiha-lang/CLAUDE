"""Streamlit-дашборд: концентрация экономической активности в агломерациях РФ.

Запуск:
    pip install streamlit pandas numpy plotly
    streamlit run app.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Агломерации РФ", layout="wide", page_icon=None)


@st.cache_data
def load_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    cities = [
        ("Москва", 13.1, 55.75, 37.62),
        ("Санкт-Петербург", 5.6, 59.93, 30.33),
        ("Новосибирск", 1.6, 55.03, 82.92),
        ("Екатеринбург", 1.5, 56.84, 60.61),
        ("Казань", 1.3, 55.79, 49.12),
        ("Нижний Новгород", 1.2, 56.30, 43.94),
        ("Челябинск", 1.2, 55.16, 61.40),
        ("Самара", 1.1, 53.20, 50.15),
        ("Омск", 1.1, 54.98, 73.37),
        ("Ростов-на-Дону", 1.1, 47.22, 39.72),
        ("Уфа", 1.1, 54.73, 55.97),
        ("Красноярск", 1.1, 56.01, 92.85),
        ("Воронеж", 1.0, 51.66, 39.20),
        ("Пермь", 1.0, 58.01, 56.25),
        ("Волгоград", 1.0, 48.71, 44.51),
    ]
    years = np.arange(2010, 2024)
    rows = []
    for name, pop, lat, lon in cities:
        base_gdp = pop * rng.uniform(380, 520)
        base_lq = rng.uniform(0.9, 1.8)
        for y in years:
            growth = 1 + 0.02 * (y - 2010) + rng.normal(0, 0.03)
            rows.append({
                "город": name,
                "год": y,
                "население_млн": pop * (1 + 0.005 * (y - 2010)),
                "ВРП_млрд_руб": base_gdp * growth,
                "LQ_услуги": base_lq + rng.normal(0, 0.05),
                "производительность": (base_gdp * growth) / (pop * 0.5),
                "широта": lat,
                "долгота": lon,
            })
    return pd.DataFrame(rows)


df = load_data()

st.title("Концентрация экономической активности в агломерациях РФ")
st.caption("Демонстрационный дашборд · синтетические данные · 2010–2023")

with st.sidebar:
    st.header("Фильтры")
    year = st.slider("Год", int(df.год.min()), int(df.год.max()), 2023)
    top_n = st.slider("Топ городов", 5, 15, 10)
    metric = st.selectbox(
        "Метрика",
        ["ВРП_млрд_руб", "производительность", "LQ_услуги", "население_млн"],
    )

snap = df[df.год == year].nlargest(top_n, "ВРП_млрд_руб")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Городов в выборке", len(snap))
c2.metric("Суммарный ВРП, трлн ₽", f"{snap.ВРП_млрд_руб.sum()/1000:.1f}")
c3.metric("Население, млн", f"{snap.население_млн.sum():.1f}")
hhi = ((snap.ВРП_млрд_руб / snap.ВРП_млрд_руб.sum()) ** 2).sum() * 10000
c4.metric("Индекс HHI", f"{hhi:.0f}")

left, right = st.columns([3, 2])

with left:
    st.subheader(f"Карта: {metric} ({year})")
    fig_map = px.scatter_geo(
        snap,
        lat="широта",
        lon="долгота",
        size=metric,
        color=metric,
        hover_name="город",
        color_continuous_scale="Viridis",
        scope="asia",
    )
    fig_map.update_geos(
        projection_type="mercator",
        lataxis_range=[42, 68],
        lonaxis_range=[25, 100],
        showcountries=True,
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=450)
    st.plotly_chart(fig_map, width="stretch")

with right:
    st.subheader(f"Рейтинг по {metric}")
    fig_bar = px.bar(
        snap.sort_values(metric),
        x=metric,
        y="город",
        orientation="h",
        color=metric,
        color_continuous_scale="Viridis",
    )
    fig_bar.update_layout(height=450, showlegend=False)
    st.plotly_chart(fig_bar, width="stretch")

st.subheader("Динамика во времени")
fig_line = px.line(
    df[df.город.isin(snap.город)],
    x="год",
    y=metric,
    color="город",
    markers=True,
)
fig_line.update_layout(height=400)
st.plotly_chart(fig_line, width="stretch")

with st.expander("Посмотреть таблицу"):
    st.dataframe(snap.reset_index(drop=True), width="stretch")
