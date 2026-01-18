import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =========================
# Page config
# =========================
st.set_page_config(page_title="Salary Distribution", layout="wide")

st.title("Salary Distribution by Job Title (USD)")

# =========================
# Load data
# =========================
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # Fix: Check if file exists in current dir, otherwise check parent dir
    if not os.path.exists(path):
        if os.path.exists(f"../{path}"):
            path = f"../{path}"
    return pd.read_csv(path)

df = load_data("database_ai_job_final.csv")

# =========================
# Basic cleaning
# =========================
required_cols = {
    "job_title",
    "salary_usd",
    "experience_level",
    "company_location",
    "employee_residence"
}

if not required_cols.issubset(df.columns):
    st.error(f"Missing required columns: {required_cols - set(df.columns)}")
    st.stop()

df["salary_usd"] = pd.to_numeric(df["salary_usd"], errors="coerce")
df = df.dropna(subset=["job_title", "salary_usd"])

# =========================
# Sidebar filters
# =========================
st.sidebar.header("Filters")

filter_cols = ["experience_level", "employment_type", "company_location"]
filtered_df = df.copy()

for col in filter_cols:
    if col in filtered_df.columns:
        options = sorted(filtered_df[col].dropna().unique())
        chosen = st.sidebar.multiselect(col, options, default=options)
        filtered_df = filtered_df[filtered_df[col].isin(chosen)]

# --- UPDATED SLIDER ---
top_n = st.sidebar.slider(
    "Number of job titles to display (Top N)",
    min_value=5,
    max_value=14,  # Max limit remains 14
    value=10       # Default value set to 10
)

# =========================
# Remove job titles with < 5 records
# =========================
job_counts = filtered_df["job_title"].value_counts()
valid_jobs = job_counts[job_counts >= 5].index
filtered_df = filtered_df[filtered_df["job_title"].isin(valid_jobs)]

if filtered_df.empty:
    st.warning("No job titles with at least 5 records after filtering.")
    st.stop()

# =========================
# Keep Top N job titles
# =========================
top_jobs = (
    filtered_df["job_title"]
    .value_counts()
    .head(top_n)
    .index
)
filtered_df = filtered_df[filtered_df["job_title"].isin(top_jobs)]

# =========================
# Sort job titles by median salary
# =========================
median_salary_by_job = (
    filtered_df
    .groupby("job_title")["salary_usd"]
    .median()
    .sort_values(ascending=False)
)

sorted_job_titles = median_salary_by_job.index.tolist()

# =========================
# BOX PLOT – Salary by Job Title (Colored by Experience)
# =========================

# Define consistent colors for both charts
experience_colors = {
    "EN": "#e169d9",  # pink
    "MI": "#3182bd",  # blue
    "SE": "#31a354",  # green
    "EX": "#e6550d",  # orange
}

# 1. Create Box Plot
fig1 = px.box(
    filtered_df,
    x="job_title",
    y="salary_usd",
    color="experience_level",
    category_orders={
        "job_title": sorted_job_titles,
        "experience_level": ["EN", "MI", "SE", "EX"]
    },
    color_discrete_map=experience_colors,
    points="outliers",
    labels={
        "job_title": "Job Title",
        "salary_usd": "Salary (USD)",
        "experience_level": "Exp Level"
    }
)

fig1.update_layout(template="none")

# --- CUSTOMIZED LAYOUT FOR VISIBILITY ---
fig1.update_layout(
    xaxis_tickangle=-45,
    height=650,
    # Increased left margin (l=80) to move chart right and give space for numbers
    margin=dict(l=80, r=20, t=40, b=140),
    legend_title="Experience Level",
    yaxis=dict(
        tickformat="$,.0f",       # Adds $ and commas (e.g., $150,000)
        tickfont=dict(size=14),   # Larger font for salary numbers
        showgrid=True,            # Horizontal grid lines for readability
        gridcolor="#eee"
    ),
    xaxis=dict(
        tickfont=dict(size=12)
    )
)

st.plotly_chart(fig1, use_container_width=True)

# =========================
# Unified COUNTRY column
# =========================
filtered_df["country"] = (
    filtered_df["company_location"]
    .fillna(filtered_df["employee_residence"])
)

# =====================================================================
# DOT PLOT – Median salary by country and experience level
# =====================================================================
st.subheader("Median Salary by Country and Experience Level")

selected_job = st.selectbox(
    "Select job title",
    sorted(filtered_df["job_title"].unique())
)

df_job = filtered_df[filtered_df["job_title"] == selected_job]

if df_job.empty:
    st.warning("No data for this job title with current filters.")
else:
    # Order experience levels
    experience_order = ["EN", "MI", "SE", "EX"]

    # Ensure categorical consistency
    df_job = df_job.copy()
    df_job["experience_level"] = pd.Categorical(
        df_job["experience_level"],
        categories=experience_order,
        ordered=True
    )

    # Aggregate median salary
    dot_df = (
        df_job
        .groupby(["country", "experience_level"])["salary_usd"]
        .median()
        .reset_index()
    )

    # Count countries
    country_counts = dot_df["country"].value_counts()

    # 🔹 Progressive disclosure: how many countries to show
    st.sidebar.subheader("Country scope")

    if len(country_counts) > 0:
        max_slider = min(30, len(country_counts))
        min_slider = min(5, max_slider)

        num_countries = st.sidebar.slider(
            "Number of countries to display",
            min_value=min_slider,
            max_value=max_slider,
            value=min(10, max_slider),
            step=1
        )

        top_countries = country_counts.head(num_countries).index
        dot_df = dot_df[dot_df["country"].isin(top_countries)]

        # Plot
        fig2 = px.scatter(
            dot_df,
            x="salary_usd",
            y="country",
            color="experience_level",
            color_discrete_map=experience_colors, # Use same color map
            labels={
                "salary_usd": "Median Salary (USD)",
                "country": "Country",
                "experience_level": "Experience Level"
            }
        )

        fig2.update_traces(marker=dict(size=11))

        fig2.update_layout(
            height=600,
            legend_title_text="Experience Level",
            xaxis_title="Median Salary (USD)",
            yaxis_title="Country",
            xaxis=dict(
                tickformat="$,.0f" # Applied consistent formatting to bottom chart too
            )
        )

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough data to display country stats for this role.")

st.caption(
    "Experience levels: EN = Entry | MI = Mid | SE = Senior | EX = Executive"
)