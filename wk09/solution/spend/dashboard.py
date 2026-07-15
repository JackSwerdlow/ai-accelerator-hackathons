#!/usr/bin/env python3
"""
Interactive AI spend dashboard.

Run:
    streamlit run spend/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

ROOT = Path(__file__).parent.parent

st.set_page_config(page_title="AI Spend", layout="wide")
st.title("AI Spend Dashboard")


@st.cache_data(ttl=30)  # reload CSVs every 30 s as new rows arrive
def load():
    files = sorted(ROOT.glob("ai-spend-log-*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
    df["CostGBP"] = pd.to_numeric(df["CostGBP"], errors="coerce").fillna(0)
    df["UploadTokens"] = pd.to_numeric(df["UploadTokens"], errors="coerce").fillna(0)
    df["DownloadTokens"] = pd.to_numeric(df["DownloadTokens"], errors="coerce").fillna(0)
    df["Date"] = df["Timestamp"].dt.date
    return df.sort_values("Timestamp").reset_index(drop=True)


df = load()
if df.empty:
    st.warning("No spend logs found. Run analyse.py or wait for the Stop hook to fire.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    group_by = st.radio(
        "Group by",
        ["AgentName", "Purpose", "Model", "CallType"],
        format_func={"AgentName": "Agent", "Purpose": "Purpose",
                     "Model": "Model", "CallType": "Call type"}.get,
    )
    st.divider()
    st.subheader("Filters")
    agents = st.multiselect("Agents", sorted(df["AgentName"].unique()),
                            default=sorted(df["AgentName"].unique()))
    call_types = st.multiselect("Call type", sorted(df["CallType"].unique()),
                                default=sorted(df["CallType"].unique()))

df = df[df["AgentName"].isin(agents) & df["CallType"].isin(call_types)]

# ── Summary metrics ───────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total spend", f"£{df['CostGBP'].sum():.4f}")
m2.metric("Sessions logged", f"{len(df):,}")
m3.metric("Input tokens", f"{df['UploadTokens'].sum():,.0f}")
m4.metric("Output tokens", f"{df['DownloadTokens'].sum():,.0f}")

st.divider()

# ── Cumulative spend over time ────────────────────────────────────────────────
st.subheader("Cumulative spend over time")
cum = df.copy()
cum["Cumulative £"] = cum.groupby("AgentName")["CostGBP"].cumsum()
st.plotly_chart(
    px.line(cum, x="Timestamp", y="Cumulative £", color="AgentName",
            markers=True, hover_data=["Purpose", "Model", "CostGBP"]),
    use_container_width=True,
)

# ── Breakdown + daily burn ────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    label = {"AgentName": "agent", "Purpose": "purpose",
             "Model": "model", "CallType": "call type"}[group_by]
    st.subheader(f"Total spend by {label}")
    totals = df.groupby(group_by)["CostGBP"].sum().reset_index().sort_values("CostGBP")
    st.plotly_chart(
        px.bar(totals, x="CostGBP", y=group_by, orientation="h",
               text_auto=".3f", labels={"CostGBP": "£", group_by: ""}),
        use_container_width=True,
    )

with right:
    st.subheader("Daily spend by agent")
    daily = df.groupby(["Date", "AgentName"])["CostGBP"].sum().reset_index()
    st.plotly_chart(
        px.bar(daily, x="Date", y="CostGBP", color="AgentName",
               barmode="stack", labels={"CostGBP": "£", "Date": ""}),
        use_container_width=True,
    )

# ── Token efficiency ──────────────────────────────────────────────────────────
st.subheader("Average tokens per session by purpose  (input vs output)")
tok = (df.groupby("Purpose")[["UploadTokens", "DownloadTokens"]]
         .mean().reset_index()
         .melt(id_vars="Purpose", var_name="Direction", value_name="Avg tokens"))
tok["Direction"] = tok["Direction"].map({"UploadTokens": "Input", "DownloadTokens": "Output"})
st.plotly_chart(
    px.bar(tok, x="Avg tokens", y="Purpose", color="Direction",
           orientation="h", barmode="group",
           labels={"Avg tokens": "Avg tokens / session"}),
    use_container_width=True,
)

# ── Full log ──────────────────────────────────────────────────────────────────
with st.expander("All sessions (click a column header to sort)"):
    st.dataframe(
        df.sort_values("CostGBP", ascending=False)
          .reset_index(drop=True),
        use_container_width=True,
    )
