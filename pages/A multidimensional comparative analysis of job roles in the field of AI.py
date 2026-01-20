import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------
# 1. Page Configuration
# ------------------------------------------------
st.set_page_config(
    page_title="AI Job Market Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Multidimensional Comparison of AI Job Roles")
st.markdown(
    "Compare AI job roles across disparate metrics (Salary, Frequency, Remote availability) using **Min-Max Normalization**.")


# ------------------------------------------------
# 2. Data Loading (Cached for Performance)
# ------------------------------------------------
@st.cache_data
def load_data(filepath):
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        return None


DATA_FILE = "database_ai_job_final.csv"
df = load_data(DATA_FILE)

if df is None:
    st.error(f"File '{DATA_FILE}' not found. Please ensure the file is in the root directory.")
    st.stop()



# ------------------------------------------------
# 3. Metric Configuration
# ------------------------------------------------
# Format: "Label": {"column": "col_name", "agg": "function", "color": "hex"}
# Note: agg="size" ignores column, agg="nunique" counts unique values
METRICS_CONFIG = {
    "Average Salary (USD)": {"column": "salary_usd", "agg": "mean", "color": "#F1C40F"},  # Yellow
    "Job Count": {"column": None, "agg": "size", "color": "#E377C2"},  # Pink
    "Years of Experience": {"column": "years_experience", "agg": "mean", "color": "#8172B2"}, # Purple
    "Benefits Score": {"column": "benefits_score", "agg": "mean", "color": "#8D6E63"},  # brown
    "Remote Work Ratio (%)": {"column": "remote_ratio", "agg": "mean", "color": "#D95F02" } # Orange
}

# Handle column name variations (consistency check)
if "Remote Work Ratio (%)" in df.columns and "remote_ratio" not in df.columns:
    METRICS_CONFIG["Remote Work Ratio (%)"]["column"] = "Remote Work Ratio (%)"

# ------------------------------------------------
# 4. Sidebar / Controls
# ------------------------------------------------
st.subheader("Select Metrics for Comparison")

# Toggle to select all
all_metrics = list(METRICS_CONFIG.keys())
default_metrics = ["Average Salary (USD)", "Job Count"]

# Create 6 columns for checkboxes to keep it compact
cols = st.columns(len(all_metrics))
selected_metrics = []

for col, metric_name in zip(cols, all_metrics):
    is_default = metric_name in default_metrics
    if col.checkbox(metric_name, value=is_default):
        selected_metrics.append(metric_name)

if not selected_metrics:
    st.warning("⚠️ Please select at least one metric to visualize.")
    st.stop()

# ------------------------------------------------
# 5. Data Processing & Normalization
# ------------------------------------------------
plot_data = []

for metric in selected_metrics:
    config = METRICS_CONFIG[metric]
    col_name = config["column"]
    agg_func = config["agg"]

    # 1. Aggregation
    if agg_func == "size":
        temp_df = df.groupby("job_title").size().reset_index(name="raw_value")
    elif agg_func == "nunique":
        temp_df = df.groupby("job_title")[col_name].nunique().reset_index(name="raw_value")
    else:
        temp_df = df.groupby("job_title")[col_name].mean().reset_index(name="raw_value")

    # 2. Normalization (Min-Max Scaling to 0-1 range)
    min_val = temp_df["raw_value"].min()
    max_val = temp_df["raw_value"].max()

    # Minimal visible height to allow hover on zero values
    epsilon = 0.02

    # Protect against division by zero
    if max_val - min_val == 0:
        temp_df["normalized_value"] = 1.0
    else:
        temp_df["normalized_value"] = (temp_df["raw_value"] - min_val) / (max_val - min_val)

    # Apply epsilon so bars with value 0 are still hoverable
    temp_df["normalized_value"] = temp_df["normalized_value"].clip(lower=epsilon)

    temp_df["metric"] = metric
    plot_data.append(temp_df)

# Concatenate all prepared dataframes
plot_df = pd.concat(plot_data, ignore_index=True)

# Sort logic: Maintain a consistent order for the X-axis
job_order = sorted(df["job_title"].unique())

# ------------------------------------------------
# 6. Plotting
# ------------------------------------------------
fig = px.bar(
    plot_df,
    x="job_title",
    y="normalized_value",
    color="metric",
    barmode="group",
    category_orders={"job_title": job_order},
    # Map colors dynamically based on selection
    color_discrete_map={m: METRICS_CONFIG[m]["color"] for m in selected_metrics},
    # Pass raw_value explicitly to custom_data for the hover tooltip
    custom_data=["raw_value", "metric"],
    title="Normalized Multidimensional Comparison"
)

# Refine Hover Tooltip
# %{customdata[0]} refers to the first item in the custom_data list (raw_value)
fig.update_traces(
    hovertemplate="<br>".join([
        "<b>%{x}</b>",
        "Metric: %{customdata[1]}",
        "Raw Value: <b>%{customdata[0]:,.2f}</b>",
        "Normalized Score: %{y:.2f}",
        "<extra></extra>"  # Removes the secondary box on the side
    ])
)

# Layout Styling
fig.update_layout(
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="#333"),
    xaxis=dict(
        title="Job Title",
        tickangle=-45,
        linecolor="black"
    ),
    yaxis=dict(
        title="Normalized Score (0=Low, 1=High)",
        range=[0, 1.1],  # Give a little headroom for tooltips
        gridcolor="#eee",
        showgrid=True
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title=None
    ),
    margin=dict(t=80, b=100)  # Add margin for titles and rotated labels
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# 7. Detailed Data Table
# ------------------------------------------------
st.divider()
st.subheader("📋 Underlying Data (Raw Values)")

# Pivot table to show Job Titles as rows and Metrics as columns
pivot_df = plot_df.pivot(index="job_title", columns="metric", values="raw_value")

# Display with nice formatting
st.dataframe(
    pivot_df.style.format("{:,.2f}").background_gradient(cmap="Blues", axis=0),
    use_container_width=True
)