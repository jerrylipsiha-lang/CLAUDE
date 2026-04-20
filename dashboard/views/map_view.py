"""Страница: географическое распределение и сравнение по округам."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from lib.data import END_YEAR, START_YEAR, city_year_panel
from lib.theme import CATEGORICAL

st.title("География агломераций")
st.markdown(
    '<p class="section-caption">Пузырьковая карта, распределение по '
    "федеральным округам и децильные группы</p>",
    unsafe_allow_html=True,
)

cy = city_year_panel()

with st.sidebar:
    st.header("Фильтры карты")
    year = st.slider("Год", START_YEAR, END_YEAR, END_YEAR, key="map_year")
    metric = st.selectbox(
        "Показатель",
        [
            "ВРП_млрд",
            "население_млн",
            "занятость_тыс",
            "инвестиции_млрд",
            "производительность_млн_на_чел",
            "средняя_зп_тыс",
        ],
        key="map_metric",
    )
    districts = st.multiselect(
        "Федеральные округа",
        sorted(cy["округ"].unique()),
        default=sorted(cy["округ"].unique()),
        key="map_fd",
    )

snap = cy[(cy["год"] == year) & (cy["округ"].isin(districts))]

tab_map, tab_fd, tab_scatter = st.tabs(
    ["Карта", "По округам", "Население × производительность"]
)

with tab_map:
    fig = px.scatter_geo(
        snap,
        lat="широта",
        lon="долгота",
        size=metric,
        color="округ",
        hover_name="город",
        hover_data={
            metric: ":.1f",
            "ВРП_млрд": ":.0f",
            "население_млн": ":.2f",
            "широта": False,
            "долгота": False,
        },
        color_discrete_sequence=CATEGORICAL,
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
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, width="stretch")

with tab_fd:
    by_fd = (
        snap.groupby("округ", as_index=False)
        .agg({metric: "sum", "город": "count"})
        .rename(columns={"город": "городов"})
        .sort_values(metric, ascending=True)
    )
    fig = px.bar(
        by_fd,
        x=metric,
        y="округ",
        orientation="h",
        text="городов",
        color="округ",
        color_discrete_sequence=CATEGORICAL,
    )
    fig.update_traces(texttemplate="%{text} гор.", textposition="outside")
    fig.update_layout(
        height=400, showlegend=False,
        xaxis_title=metric, yaxis_title="",
    )
    st.plotly_chart(fig, width="stretch")

with tab_scatter:
    fig = px.scatter(
        snap,
        x="население_млн",
        y="производительность_млн_на_чел",
        size="ВРП_млрд",
        color="округ",
        hover_name="город",
        text="город",
        size_max=45,
        color_discrete_sequence=CATEGORICAL,
        log_x=True,
    )
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(
        height=520,
        xaxis_title="Население, млн (log)",
        yaxis_title="Производительность, млн ₽ / занятого",
    )
    st.plotly_chart(fig, width="stretch")
