"""Страница: shift-share декомпозиция прироста занятости."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import END_YEAR, START_YEAR, build_panel
from lib.metrics import shift_share
from lib.theme import ACCENT, PRIMARY, SUCCESS

st.title("Shift-share анализ")
st.markdown(
    '<p class="section-caption">'
    "Декомпозиция прироста занятости: национальный рост (NS) + отраслевой микс (IM) + "
    "конкурентный сдвиг (CS)</p>",
    unsafe_allow_html=True,
)

panel = build_panel()

with st.sidebar:
    st.header("Окно анализа")
    year_from = st.number_input(
        "С года", min_value=START_YEAR, max_value=END_YEAR - 1,
        value=START_YEAR, step=1, key="ss_from",
    )
    year_to = st.number_input(
        "По год", min_value=year_from + 1, max_value=END_YEAR,
        value=END_YEAR, step=1, key="ss_to",
    )

result = shift_share(panel, int(year_from), int(year_to))
result_sorted = result.sort_values("всего", ascending=True)

st.subheader(f"Компоненты прироста занятости, {year_from} → {year_to}")

fig = go.Figure()
fig.add_trace(go.Bar(
    y=result_sorted["город"], x=result_sorted["NS_нац_рост"],
    orientation="h", name="NS · национальный рост",
    marker_color=PRIMARY,
))
fig.add_trace(go.Bar(
    y=result_sorted["город"], x=result_sorted["IM_отраслевой"],
    orientation="h", name="IM · отраслевой микс",
    marker_color=ACCENT,
))
fig.add_trace(go.Bar(
    y=result_sorted["город"], x=result_sorted["CS_конкурентный"],
    orientation="h", name="CS · конкурентный сдвиг",
    marker_color=SUCCESS,
))
fig.update_layout(
    barmode="relative",
    height=620,
    xaxis_title="Вклад в Δ занятость, тыс. чел.",
    yaxis_title="",
    legend=dict(orientation="h", y=-0.1),
)
st.plotly_chart(fig, width="stretch")

st.markdown("---")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Лидеры по конкурентному сдвигу (CS)")
    top_cs = result.nlargest(8, "CS_конкурентный")[["город", "CS_конкурентный", "всего"]]
    fig = px.bar(
        top_cs.sort_values("CS_конкурентный"),
        x="CS_конкурентный", y="город", orientation="h",
        color="CS_конкурентный", color_continuous_scale="Greens",
    )
    fig.update_layout(height=360, coloraxis_showscale=False,
                      xaxis_title="CS, тыс. чел.", yaxis_title="")
    st.plotly_chart(fig, width="stretch")

with c2:
    st.subheader("Отстающие по CS")
    worst = result.nsmallest(8, "CS_конкурентный")[["город", "CS_конкурентный", "всего"]]
    fig = px.bar(
        worst.sort_values("CS_конкурентный", ascending=False),
        x="CS_конкурентный", y="город", orientation="h",
        color="CS_конкурентный", color_continuous_scale="Reds_r",
    )
    fig.update_layout(height=360, coloraxis_showscale=False,
                      xaxis_title="CS, тыс. чел.", yaxis_title="")
    st.plotly_chart(fig, width="stretch")

st.markdown("**Интерпретация:**")
st.markdown(
    "- **NS** показывает, сколько занятости город получил бы при равномерном росте, "
    "как в среднем по стране.\n"
    "- **IM** положителен для городов, специализированных на быстрорастущих отраслях.\n"
    "- **CS** отражает уникальные локальные преимущества города сверх отраслевого эффекта."
)

with st.expander("Числовая таблица"):
    st.dataframe(result.sort_values("всего", ascending=False),
                 width="stretch", hide_index=True)
    csv = result.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Скачать CSV", csv,
        file_name=f"shift_share_{year_from}_{year_to}.csv",
        mime="text/csv",
    )
