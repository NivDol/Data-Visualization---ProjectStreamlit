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
    "Years of Experience": {"column": "years_experience", "agg": "mean", "color": "#8172B2"},  # Purple
    "Benefits Score": {"column": "benefits_score", "agg": "mean", "color": "#8D6E63"},  # Brown
    "Remote Work Ratio (%)": {"column": "remote_ratio", "agg": "mean", "color": "#D95F02"}  # Orange
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

# Create columns for checkboxes
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

# Iterate through selected metrics to calculate and normalize values
for metric in selected_metrics:
    config = METRICS_CONFIG[metric]
    col_name = config["column"]
    agg_func = config["agg"]

    # 1. Aggregation based on configuration
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

    # Apply epsilon clip
    temp_df["normalized_value"] = temp_df["normalized_value"].clip(lower=epsilon)

    temp_df["metric"] = metric
    plot_data.append(temp_df)

# Concatenate all prepared dataframes
plot_df = pd.concat(plot_data, ignore_index=True)

# --- Sort Settings ---
st.subheader("Chart Sort Settings")

# Add "Name (A-Z)" to the list of currently selected metrics
sort_options = ["Name (A-Z)"] + selected_metrics
sort_by = st.selectbox("Sort Chart By:", sort_options)

# Determine the categorical order of the X-axis based on selection
if sort_by == "Name (A-Z)":
    # Default alphabetical sort
    job_order = sorted(plot_df["job_title"].unique())
else:
    # Filter data for the selected metric to determine rank
    sorter_df = plot_df[plot_df["metric"] == sort_by]

    # Sort by normalized value (descending) to show highest bars first
    sorter_df = sorter_df.sort_values(by="normalized_value", ascending=False)

    # Extract the ordered list of job titles
    job_order = sorter_df["job_title"].tolist()

# ------------------------------------------------
# 6. Plotting
# ------------------------------------------------
fig = px.bar(
    plot_df,
    x="job_title",
    y="normalized_value",
    color="metric",
    barmode="group",
    # Apply the calculated sort order
    category_orders={"job_title": job_order},
    # Map colors dynamically based on configuration
    color_discrete_map={m: METRICS_CONFIG[m]["color"] for m in selected_metrics},
    # Pass raw values to custom_data for tooltips
    custom_data=["raw_value", "metric"],
    title=f"Normalized Multidimensional Comparison (Sorted by: {sort_by})"
)

# Refine Hover Tooltip
fig.update_traces(
    hovertemplate="<br>".join([
        "<b>%{x}</b>",
        "Metric: %{customdata[1]}",
        "Raw Value: <b>%{customdata[0]:,.2f}</b>",
        "Normalized Score: %{y:.2f}",
        "<extra></extra>"
    ])
)

# Layout Styling
fig.update_layout(
    height=600,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Arial", size=14, color="#333"),
    title=dict(font=dict(size=22)),
    xaxis=dict(
        title="Job Title",
        tickangle=-45,
        linecolor="black",
        title_font=dict(size=18),
        tickfont=dict(size=16)
    ),
    yaxis=dict(
        title="Normalized Score (0=Low, 1=High)",
        range=[0, 1.1],
        gridcolor="#eee",
        showgrid=True,
        title_font=dict(size=18),
        tickfont=dict(size=16)
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title=None,
        font=dict(size=14)
    ),
    margin=dict(t=100, b=120)
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------
# 7. Detailed Data Table (Clean, High Visibility & Searchable)
# ------------------------------------------------
st.divider()
st.subheader("📋 Underlying Data (Raw Values)")

# 1. Prepare Base Data
pivot_df = plot_df.pivot(index="job_title", columns="metric", values="raw_value")

# Clean up table structure
pivot_df.columns.name = None          # Remove "metric" label from header
pivot_df = pivot_df.reset_index()     # Flatten the table

# --- Search Functionality ---
# Text input for filtering
search_query = st.text_input("🔍 Search by Job Title", placeholder="Type job name...")

# Filter logic (Case-insensitive)
if search_query:
    pivot_df = pivot_df[pivot_df["job_title"].str.contains(search_query, case=False, na=False)]

# --- Styling ---
# Define numeric columns for specific formatting
numeric_cols = pivot_df.columns.drop("job_title")

# Create Styler object on the (potentially filtered) dataframe
styler = pivot_df.style\
    .format("{:,.2f}", subset=numeric_cols)\
    .background_gradient(cmap="Blues", axis=0, subset=numeric_cols)\
    .hide(axis="index")

# Apply Custom CSS
styler.set_table_styles([
    # Header styling
    {'selector': 'th', 'props': [
        ('background-color', '#4e79a7'),
        ('color', 'white'),
        ('font-size', '20px'),
        ('text-align', 'center'),
        ('padding', '12px'),
        ('border', '1px solid #ddd')
    ]},
    # Cell styling
    {'selector': 'td', 'props': [
        ('font-size', '18px'),
        ('text-align', 'center'),
        ('padding', '10px'),
        ('border', '1px solid #ddd')
    ]},
    # Specific styling for the Job Title column
    {'selector': 'td.col0', 'props': [
        ('text-align', 'left'),
        ('font-weight', 'bold')
    ]}
])

# Render
st.markdown(styler.to_html(), unsafe_allow_html=True)