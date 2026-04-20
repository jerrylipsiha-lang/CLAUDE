"""Точка входа: дашборд концентрации экономической активности в агломерациях РФ.

Запуск: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from lib.theme import CSS, apply_plotly_theme

st.set_page_config(
    page_title="Агломерации РФ · аналитический дашборд",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_plotly_theme()
st.markdown(CSS, unsafe_allow_html=True)

pages = {
    "Обзор": [
        st.Page("views/overview.py", title="Общий обзор", default=True),
    ],
    "Пространственный анализ": [
        st.Page("views/map_view.py", title="География"),
        st.Page("views/sectors.py", title="Отраслевая структура"),
    ],
    "Концентрация и неравенство": [
        st.Page("views/concentration.py", title="Индексы концентрации"),
        st.Page("views/shift_share.py", title="Shift-share анализ"),
    ],
    "Глубокое погружение": [
        st.Page("views/city.py", title="Карточка города"),
    ],
    "Справочно": [
        st.Page("views/methodology.py", title="Методология"),
    ],
}

pg = st.navigation(pages)
pg.run()
