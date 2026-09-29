"""
Barebones Streamlit demo page. Reads results/results.csv — works today
against the fake results, and needs zero changes once P2 overwrites that
file with real numbers.

Run: .venv/bin/streamlit run src/demo/app.py
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Federated AML Demo", layout="wide")
st.title("Federated AML — local vs. federated vs. pooled")
st.caption(
    "Synthetic IBM HI-Small dataset. Regions are fictional labels grouped by "
    "bank ID. This is a demonstration, not evidence of real-world performance."
)

df = pd.read_csv("results/results.csv")

st.subheader("Results by region")
st.dataframe(df, use_container_width=True)

st.subheader("PR-AUC by setup")
chart_df = df.pivot(index="region", columns="setup", values="pr_auc")
st.bar_chart(chart_df)

st.subheader("Gain from joining (federated - local)")
gain = df.pivot(index="region", columns="setup", values="pr_auc")
gain["gain"] = gain["federated"] - gain["local"]
st.bar_chart(gain["gain"].sort_values())
