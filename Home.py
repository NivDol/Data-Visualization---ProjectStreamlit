import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="AI Job Market Analysis",
    page_icon=None,
    layout="wide"
)

# --- Custom CSS for Font Sizes ---
st.markdown("""
    <style>
    /* Main titles (h1) */
    h1 {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    /* Subheaders (h2, h3) */
    h2, h3 {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    /* Regular text, list items, and metric labels */
    p, li, span, label, div {
        font-size: 16px !important;
    }
    /* Metric values - making them stand out slightly more than the title */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# 2. Data Loading and Dynamic Calculations
@st.cache_data
def get_dashboard_stats():
    try:
        df = pd.read_csv("database_ai_job_final.csv")

        avg_salary = df['salary_usd'].mean()
        median_salary = df['salary_usd'].median()

        # New Global Coverage Calculation: Union of Company and Employee locations
        unique_countries = set(df['company_location'].unique()).union(set(df['employee_residence'].unique()))
        num_countries = len(unique_countries)

        # Leading Profession: Highest average salary for roles with at least 5 entries
        counts = df['job_title'].value_counts()
        popular_roles = counts[counts >= 5].index
        leading_prof = df[df['job_title'].isin(popular_roles)].groupby('job_title')['salary_usd'].mean().idxmax()

        return {
            "avg": avg_salary,
            "median": median_salary,
            "countries": num_countries,
            "top_role": leading_prof
        }
    except Exception as e:
        return None


stats = get_dashboard_stats()

# 3. Main Header
st.title("Global AI Adoption and Job Market Portal")

st.markdown("""
### Welcome to the AI Job Market Insights Dashboard
This platform provides a comprehensive look at how Artificial Intelligence is reshaping the global workforce. 
Navigate through the sidebar to explore different dimensions of the data.
""")

# 4. Dynamic Statistics Section
st.divider()
st.subheader("Global Market Statistics")

if stats:
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric(label="Average Annual Salary", value=f"${stats['avg']:,.0f}")
        st.caption("Calculated average across the entire dataset.")
    with col_stat2:
        st.metric(label="Median Market Salary", value=f"${stats['median']:,.0f}")
        st.caption("The midpoint salary value for professionals.")
    with col_stat3:
        st.metric(label="Global Coverage", value=f"{stats['countries']}")
        st.caption("Total unique countries (Companies + Employees).")
    with col_stat4:
        st.metric(label="Leading Profession", value=stats['top_role'])
        st.caption("Role with the highest average compensation (min. 5 entries).")
else:
    st.error("Could not load database_ai_job_final.csv for calculations.")

st.divider()

# 5. Project Overview
st.markdown("### Project Overview")
st.write(
    "This dashboard is based on the Global AI Job Market and Salary Trends dataset, providing insights into the current state of AI employment across various metrics.")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Our Missions:**")
    st.write("""
    * Are there significant geographical differences in AI adoption around the world?
    * A multidimensional comparative analysis of job roles in the field of AI.
    * Comparison between the level of demand for different skills in the AI job market and the salary level offered for them.
    * Mission 4: Are there significant differences in salaries in the field of AI depending on the role, geographical region, and level of experience?
    """)

with col_right:
    st.markdown("**Data Information:**")
    st.write(
        "**Features:** Job Titles, Salary (USD), Experience Level (EN, MI, SE, EX), Employment Type, Company Location, Remote Ratio, and Required Skills.")
    st.write(
        "**Source:** [Global AI Job Market and Salary Trends 2025 (Kaggle)](https://www.kaggle.com/datasets/bismasajjad/global-ai-job-market-and-salary-trends-2025?resource=download)")

st.divider()

# 6. Module Descriptions
st.markdown("""
#### Available Analysis Modules:
* **Geographical Overview of AI Impact**: Explore adoption by country and compare residence vs. company locations.
* **Salary Distribution by Job Title**: Deep dive into pay scales across different roles and experience levels.
* **AI Skills Landscape**: Analyze which technical skills are most sought after and high-paying.
* **Multidimensional Comparative Analysis**: A high-level view comparing roles across frequency and remote availability.
""")