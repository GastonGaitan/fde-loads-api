"""Acme Logistics — Inbound Carrier Sales metrics dashboard.

A standalone Streamlit app (Objective 2). It does NOT touch the database
directly: it reads the FastAPI endpoints GET /metrics and GET /calls over HTTP,
so the API stays the single source of truth.
"""
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8010").rstrip("/")
API_KEY = os.getenv("API_KEY", "dev-secret-change-me")
HEADERS = {"X-API-Key": API_KEY}

SENTIMENT_COLORS = {"positive": "#2ecc71", "neutral": "#95a5a6", "negative": "#e74c3c"}

st.set_page_config(
    page_title="Acme Carrier Sales — Metrics",
    page_icon="🚚",
    layout="wide",
)


@st.cache_data(ttl=30)
def fetch(path: str):
    r = requests.get(f"{API_BASE}{path}", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


st.title("🚚 Acme Logistics — Inbound Carrier Sales")
st.caption(f"Use-case metrics · source: {API_BASE}")

if st.button("🔄 Refresh data"):
    st.cache_data.clear()

try:
    metrics = fetch("/metrics")
    calls = pd.DataFrame(fetch("/calls"))
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not reach the API at {API_BASE}.\n\n{exc}")
    st.stop()

# ---- KPI row ---------------------------------------------------------------
total = metrics["total_calls"]
deals = metrics["deals_booked"]
avg_rate = metrics["avg_final_rate_for_deals"]
avg_rounds = metrics["avg_negotiation_rounds_for_deals"]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total calls", total)
k2.metric("Deals booked", deals)
k3.metric("Conversion rate", f"{metrics['conversion_rate'] * 100:.1f}%")
k4.metric("Avg deal rate", f"${avg_rate:,.0f}" if avg_rate else "—")
k5.metric("Avg rounds / deal", f"{avg_rounds:.1f}" if avg_rounds else "—")

st.divider()

# ---- Charts ----------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Call outcomes")
    outcomes = metrics.get("outcomes") or {}
    if outcomes:
        df = pd.DataFrame(outcomes.items(), columns=["outcome", "count"])
        fig = px.pie(df, names="outcome", values="count", hole=0.45)
        fig.update_traces(textinfo="percent+label", sort=False)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No outcomes recorded yet.")

with col2:
    st.subheader("Carrier sentiment")
    sentiments = metrics.get("sentiments") or {}
    if sentiments:
        df = pd.DataFrame(sentiments.items(), columns=["sentiment", "count"])
        fig = px.pie(
            df,
            names="sentiment",
            values="count",
            hole=0.45,
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
        )
        fig.update_traces(textinfo="percent+label", sort=False)
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sentiment recorded yet.")

# ---- Deals by load + final rates ------------------------------------------
if not calls.empty:
    booked = calls[calls["agreed"] == True]  # noqa: E712
    if not booked.empty:
        st.subheader("Booked deals by load")
        by_load = (
            booked.groupby("load_id")
            .agg(deals=("id", "count"), avg_rate=("final_rate", "mean"))
            .reset_index()
        )
        fig = px.bar(
            by_load,
            x="load_id",
            y="deals",
            text="deals",
            hover_data={"avg_rate": ":.0f"},
        )
        fig.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# ---- Calls table -----------------------------------------------------------
st.subheader("Recent calls")
if calls.empty:
    st.info("No calls logged yet. Make a test call to populate the dashboard.")
else:
    cols = [
        "created_at", "call_id", "mc_number", "carrier_name", "eligible",
        "load_id", "outcome", "sentiment", "agreed", "final_rate",
        "negotiation_rounds",
    ]
    present = [c for c in cols if c in calls.columns]
    st.dataframe(
        calls[present].sort_values("created_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
