import streamlit as st
import pandas as pd
import plotly.express as px

# === Load data ===
@st.cache_data(ttl=3600)
def load_data():
    url = "https://raw.githubusercontent.com/E-man85/itjobs-data-automation/main/itjobs_data_analyst.csv"
    df = pd.read_csv(url)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

df = load_data()

import requests
from datetime import datetime

# === Get last update timestamp from GitHub ===
def get_last_commit_time():
    api_url = "https://api.github.com/repos/E-man85/itjobs-data-automation/commits?path=itjobs_data_analyst.csv&page=1&per_page=1"
    try:
        r = requests.get(api_url)
        if r.status_code == 200 and len(r.json()) > 0:
            commit_date = r.json()[0]["commit"]["committer"]["date"]
            dt = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%d %b %Y %H:%M UTC")
        else:
            return "Unknown"
    except Exception:
        return "Unknown"

last_update = get_last_commit_time()

# === Page configuration ===
st.set_page_config(
    page_title="ITJobs Data Analyst Tracker",
    page_icon="📊",
    layout="wide"
)

st.title("📈 ITJobs Data Analyst Dashboard")
st.caption(f"🔄 Last data update: {last_update}")
st.caption("Automated daily data extraction from itjobs.pt")

# === Metrics section ===
col1, col2, col3 = st.columns(3)
col1.metric("Total job records", len(df))
col2.metric("Active jobs", int(df["ativo"].sum()))
col3.metric("Inactive jobs", int(len(df) - df["ativo"].sum()))

# === Tabs for different views ===
tab1, tab2 = st.tabs(["💼 Current Openings", "📆 Historical Trends"])

# --- TAB 1: Current Jobs ---
with tab1:
    st.subheader("Current Job Openings")

    active_jobs = df[df["ativo"] == 1].sort_values("date", ascending=False)
    
    # Filters
    companies = sorted(active_jobs["company"].dropna().unique())
    selected_company = st.selectbox("Filter by company", ["All"] + companies)
    
    if selected_company != "All":
        active_jobs = active_jobs[active_jobs["company"] == selected_company]

    st.write(f"Showing {len(active_jobs)} active job(s).")

    # Display table
    st.dataframe(
        active_jobs[["date", "title", "company", "details", "link"]],
        use_container_width=True,
        hide_index=True
    )

# --- TAB 2: Historical data ---
with tab2:
    st.subheader("Job Posting History")

    # Number of active/inactive jobs over time
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly_jobs = df.groupby("month").agg({"title": "count"}).reset_index()
    monthly_jobs.columns = ["month", "num_jobs"]

    fig = px.bar(
        monthly_jobs,
        x="month",
        y="num_jobs",
        title="Number of job postings per month",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Full Job History")
    st.dataframe(
        df.sort_values("date", ascending=False)[["date", "title", "company", "ativo", "details", "link"]],
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")
st.caption("🔁 Updated automatically via GitHub Actions")
