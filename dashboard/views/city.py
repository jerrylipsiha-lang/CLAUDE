"""Страница: карточка выбранного города."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data import END_YEAR, START_YEAR, SECTORS, build_panel, city_year_panel
from lib.metrics import cagr, location_quotient
from lib.theme import ACCENT, PRIMARY

st.title("Карточка города")

panel = build_panel()
cy = city_year_panel()

with st.sidebar:
    city = st.selectbox(
        "Город", sorted(panel["город"].unique()), key="card_city"
    )

city_hist = cy[cy["город"] == city].sort_values("год")
last = city_hist.iloc[-1]
first = city_hist.iloc[0]

st.markdown(
    f'<p class="section-caption">{city} · {last["округ"]} · '
    f"координаты ({last['широта']:.2f}, {last['долгота']:.2f})</p>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Население", f"{last['население_млн']:.2f} млн",
          f"{(last['население_млн']/first['население_млн'] - 1)*100:+.1f}% c {START_YEAR}")
c2.metric("ВРП", f"{last['ВРП_млрд']:,.0f} млрд ₽".replace(",", " "),
          f"CAGR {cagr(first['ВРП_млрд'], last['ВРП_млрд'], END_YEAR - START_YEAR)*100:.1f}%")
c3.metric("Занятость", f"{last['занятость_тыс']:,.0f} тыс.".replace(",", " "))
c4.metric("Производительность",
          f"{last['производительность_млн_на_чел']:.2f} млн ₽/чел.")
c5.metric("Средняя з/п", f"{last['средняя_зп_тыс']:.1f} тыс. ₽")

st.markdown("---")

left, right = st.columns(2)

with left:
    st.subheader("Динамика ключевых показателей")
    metric = st.selectbox(
        "Показатель",
        ["ВРП_млрд", "занятость_тыс", "производительность_млн_на_чел",
         "инвестиции_млрд", "средняя_зп_тыс"],
        key="card_metric",
    )
    all_cities = cy.copy()
    fig = go.Figure()
    for c in sorted(all_cities["город"].unique()):
        sub = all_cities[all_cities["город"] == c]
        is_sel = c == city
        fig.add_trace(go.Scatter(
            x=sub["год"], y=sub[metric],
            mode="lines", name=c,
            line=dict(
                color=PRIMARY if is_sel else "#d6dde7",
                width=4 if is_sel else 1.2,
            ),
            showlegend=is_sel,
            hovertemplate=f"<b>{c}</b><br>%{{x}}: %{{y:,.1f}}<extra></extra>",
        ))
    fig.update_layout(height=420, xaxis_title="", yaxis_title=metric)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Отраслевой профиль (LQ)")
    lq = location_quotient(panel[panel["год"] == END_YEAR])
    profile = lq.loc[city].sort_values(ascending=True)
    fig = px.bar(
        x=profile.values, y=profile.index, orientation="h",
        color=profile.values, color_continuous_scale="RdBu_r",
        color_continuous_midpoint=1.0,
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color="#666")
    fig.update_layout(
        height=420, coloraxis_showscale=False,
        xaxis_title="LQ (занятость)", yaxis_title="",
    )
    st.plotly_chart(fig, width="stretch")

st.markdown("---")

st.subheader("Радар: профиль города vs среднее по выборке")
metrics_rc = {
    "ВРП": "ВРП_млрд",
    "Население": "население_млн",
    "Занятость": "занятость_тыс",
    "Производительность": "производительность_млн_на_чел",
    "Инвестиции": "инвестиции_млрд",
    "Зарплата": "средняя_зп_тыс",
}
snap = cy[cy["год"] == END_YEAR]
city_row = snap[snap["город"] == city].iloc[0]
vals_city = [city_row[c] / snap[c].max() for c in metrics_rc.values()]
vals_mean = [snap[c].mean() / snap[c].max() for c in metrics_rc.values()]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=vals_mean + [vals_mean[0]],
    theta=list(metrics_rc.keys()) + [list(metrics_rc.keys())[0]],
    fill="toself", name="Среднее по выборке",
    line_color="#b8c2cf",
))
fig.add_trace(go.Scatterpolar(
    r=vals_city + [vals_city[0]],
    theta=list(metrics_rc.keys()) + [list(metrics_rc.keys())[0]],
    fill="toself", name=city,
    line_color=PRIMARY,
))
fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickformat=".0%")),
    height=460, showlegend=True,
)
st.plotly_chart(fig, width="stretch")

with st.expander("Годовые данные"):
    st.dataframe(
        city_hist.drop(columns=["широта", "долгота"]).reset_index(drop=True),
        width="stretch",
    )
