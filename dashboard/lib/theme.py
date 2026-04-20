"""Оформление: палитра, константы, вспомогательные функции рендеринга."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

PRIMARY = "#1f4e8c"
ACCENT = "#e0701a"
NEUTRAL = "#6c757d"
SUCCESS = "#2e7d32"
WARNING = "#c77700"
DANGER = "#b3261e"

SEQUENTIAL = [
    "#eef2f7", "#cfdbe8", "#aac3d9", "#7fa4c4",
    "#5686b1", "#2f689d", "#1f4e8c", "#0f3166",
]
DIVERGING = [
    "#b3261e", "#d47a6a", "#e9c6a0", "#f5f5f5",
    "#b8d3d0", "#6a9a9a", "#2f689d", "#0f3166",
]
CATEGORICAL = [
    "#1f4e8c", "#e0701a", "#2e7d32", "#7a3b9d",
    "#c77700", "#5a5a5a", "#b3261e", "#2b9ca1",
]

NUM_FMT = {
    "млрд": ",.0f",
    "доля": ".1%",
    "индекс": ".3f",
}


def apply_plotly_theme() -> None:
    """Регистрирует единый шаблон оформления Plotly."""
    template = go.layout.Template(
        layout=dict(
            font=dict(family="Inter, Arial, sans-serif", size=13, color="#1c1c1c"),
            colorway=CATEGORICAL,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=40, r=20, t=50, b=40),
            xaxis=dict(
                showgrid=True, gridcolor="#eef2f7", zeroline=False,
                linecolor="#c9d2df", ticks="outside", tickcolor="#c9d2df",
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#eef2f7", zeroline=False,
                linecolor="#c9d2df", ticks="outside", tickcolor="#c9d2df",
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0.8)", bordercolor="#e4e9f0",
                borderwidth=1, orientation="h", yanchor="bottom", y=-0.2,
            ),
            hoverlabel=dict(bgcolor="white", bordercolor="#c9d2df", font_size=12),
        )
    )
    pio.templates["regional"] = template
    pio.templates.default = "regional"


CSS = """
<style>
    .stMetric {
        background: #f7f9fc;
        padding: 14px 18px;
        border-radius: 10px;
        border: 1px solid #e4e9f0;
    }
    .stMetric label p {
        color: #6c757d !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        font-weight: 600 !important;
        color: #1f4e8c !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }
    h1, h2, h3 {
        font-family: "Inter", Arial, sans-serif !important;
        color: #1c1c1c !important;
    }
    h1 { font-weight: 700 !important; letter-spacing: -0.02em; }
    h2 { font-weight: 600 !important; margin-top: 1.4rem !important; }
    .section-caption {
        color: #6c757d;
        font-size: 0.92rem;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f7f9fc;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #1f4e8c !important;
        color: white !important;
    }
    hr { margin: 1.5rem 0 !important; border-color: #e4e9f0 !important; }
</style>
"""
