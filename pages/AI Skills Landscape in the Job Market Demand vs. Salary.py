import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Page Configuration ---
st.set_page_config(page_title="The AI Skill Wars", layout="wide")


# --- Load Data & Preprocess ---
@st.cache_data
def load_data():
    try:
        # Load the main database
        file_path = 'database_ai_job_final.csv'

        # Robust path check (handles running from pages/ folder)
        if not os.path.exists(file_path):
            if os.path.exists(f"../{file_path}"):
                file_path = f"../{file_path}"

        df = pd.read_csv(file_path)

        # 1. Normalize column names
        df.columns = df.columns.str.strip()

        # 2. Identify the skills column
        skill_col = 'required_skills'

        if skill_col not in df.columns:
            # Fallback if column names are slightly different
            return None

        # 3. Data Cleaning & Explode
        # Drop rows with missing skills
        df = df.dropna(subset=[skill_col])

        # Clean string representation (removes brackets/quotes if present)
        df[skill_col] = df[skill_col].astype(str).str.replace(r"[\[\]']", "", regex=True)

        # Split by comma and explode
        df['skills_list'] = df[skill_col].str.split(',')
        df = df.explode('skills_list')

        # Trim whitespace
        df['skills_list'] = df['skills_list'].str.strip()

        # Remove empty strings
        df = df[df['skills_list'] != '']

        # Ensure Salary is numeric
        if 'salary_usd' in df.columns:
            df['salary_usd'] = pd.to_numeric(df['salary_usd'], errors='coerce')

        return df

    except FileNotFoundError:
        st.error(f"File '{file_path}' not found. Please ensure it is in the main directory.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def main():
    st.title("The Skill Wars: Which Tech Knowledge Pays the Most?")

    df = load_data()

    if df is not None:

        # --- Sidebar: Experience Level Filter ---
        st.sidebar.subheader("Experience Level:")

        # Get unique levels from the data
        if 'experience_level' in df.columns:
            all_levels = sorted(df['experience_level'].dropna().unique().tolist())
        else:
            all_levels = []

        # 1. "All Levels" Checkbox
        check_all = st.sidebar.checkbox("All Levels", value=True)

        # 2. Manual Selection below
        selected_levels_manual = []
        for level in all_levels:
            if st.sidebar.checkbox(level, value=True, key=level):
                selected_levels_manual.append(level)

        # --- Filter Logic ---
        if check_all:
            final_selection = all_levels
            st.sidebar.caption("Showing all experience levels (All Levels is checked).")
        else:
            final_selection = selected_levels_manual

        if not final_selection:
            st.warning("Please select at least one experience level.")
            st.stop()

        # Filter the dataframe
        filtered_df = df[df['experience_level'].isin(final_selection)]

        # --- Identify Current View Scenario (For Smart Text Positioning) ---
        current_scenario = "OTHER"

        if set(final_selection) == set(all_levels):
            current_scenario = "ALL"
        elif len(final_selection) == 1:
            level_code = final_selection[0]
            if 'SE' in level_code:
                current_scenario = "SE"
            elif 'MI' in level_code:
                current_scenario = "MI"
            elif 'EX' in level_code:
                current_scenario = "EX"
            elif 'EN' in level_code:
                current_scenario = "EN"

        # --- Data Processing ---
        # 1. Specific Renaming (from app2 logic)
        filtered_df['skills_list'] = filtered_df['skills_list'].replace({
            'Data Visualization': 'Data Viz',
            'Machine Learning': 'ML',
            'Natural Language Processing': 'NLP',
            'Computer Vision': 'CV'
        })

        # 2. Aggregation
        skill_stats = filtered_df.groupby('skills_list').agg(
            Average_Salary=('salary_usd', 'mean'),
            Job_Count=('salary_usd', 'count')  # Using salary col count as proxy for job count
        ).reset_index()

        # 3. Filter minimum noise
        skill_stats = skill_stats[skill_stats['Job_Count'] >= 10]
        skill_stats['Average_Salary'] = skill_stats['Average_Salary'].round(0)

        if skill_stats.empty:
            st.warning("Not enough data to display (need at least 10 job postings per skill).")
            st.stop()

        # --- Label & Score Logic ---
        # This prevents overcrowding by only labeling the "most interesting" bubbles (High Salary OR High Demand)
        num_labels = 30

        skill_stats['Score'] = (skill_stats['Average_Salary'] / skill_stats['Average_Salary'].max()) + \
                               (skill_stats['Job_Count'] / skill_stats['Job_Count'].max())

        top_skills = skill_stats.nlargest(num_labels, 'Score')['skills_list'].tolist()
        skill_stats['Label'] = skill_stats['skills_list'].apply(lambda x: x if x in top_skills else '')

        # --- Text Positioning Logic (Adapted from app2) ---
        median_count = skill_stats['Job_Count'].median()

        def get_text_position(row):
            skill_name = row['skills_list']

            # Scenario-specific tweaks for cleaner charts
            if current_scenario == "ALL":
                if 'Deep Learning' in skill_name: return 'middle left'
                if 'Hadoop' in skill_name: return 'middle right'
                if 'Mathematics' in skill_name: return 'bottom center'
                if 'GCP' in skill_name: return 'top center'

            elif current_scenario == "SE":
                if 'Deep Learning' in skill_name: return 'top center'
                if 'Tableau' in skill_name: return 'middle left'

            elif current_scenario == "MI":
                if 'MLO' in skill_name: return 'middle left'
                if 'Azure' in skill_name: return 'middle left'
                if 'Tableau' in skill_name: return 'middle right'

            elif current_scenario == "EX":
                if 'Mathematics' in skill_name: return 'top center'
                if 'Docker' in skill_name: return 'top center'
                if 'Hadoop' in skill_name: return 'middle right'
                if 'Tableau' in skill_name: return 'middle left'
                if 'GCP' in skill_name: return 'middle right'
                if 'Data Viz' in skill_name: return 'bottom center'
                if 'Deep Learning' in skill_name: return 'middle left'
                if skill_name == 'Java': return 'middle right'

            elif current_scenario == "EN":
                if 'Git' in skill_name: return 'middle right'
                if 'Tableau' in skill_name: return 'middle right'
                if 'Linux' in skill_name: return 'middle right'
                if 'Data Viz' in skill_name: return 'bottom center'

            # General rules
            if 'Spark' in skill_name:
                return 'middle left'
            elif 'Data Viz' in skill_name:
                return 'middle right'

            # Default logic based on position relative to median
            if row['Job_Count'] > median_count:
                return 'middle left'
            else:
                return 'middle right'

        skill_stats['TextPos'] = skill_stats.apply(get_text_position, axis=1)

        # --- Plot Creation ---
        median_salary = skill_stats['Average_Salary'].median()

        fig = px.scatter(
            skill_stats,
            x="Job_Count",
            y="Average_Salary",
            size="Job_Count",
            color="Average_Salary",
            text="Label",
            color_continuous_scale="RdBu",  # Red to Blue heatmap style
            hover_name="skills_list",
            hover_data={"Job_Count": True, "Average_Salary": ":$,.0f", "Label": False, "TextPos": False},
            title=f"AI Skills Landscape: Demand vs. Salary ({current_scenario if current_scenario != 'ALL' else 'All Levels'})",
            labels={"Job_Count": "Demand (Job Count)", "Average_Salary": "Yearly Salary ($)"}
        )

        # Add Median Lines
        fig.add_hline(y=median_salary, line_dash="dash", line_color="gray", opacity=0.7)
        fig.add_vline(x=median_count, line_dash="dash", line_color="gray", opacity=0.7)

        # Add Annotations
        fig.add_annotation(
            x=0, xref="paper",
            y=median_salary, yref="y",
            text="Median Salary",
            showarrow=False,
            yshift=10,
            xshift=2,
            align="left",
            font=dict(color="gray", size=12)
        )

        fig.add_annotation(
            x=median_count, xref="x",
            y=0, yref="paper",
            text="Median Demand",
            showarrow=False,
            yshift=10,
            xshift=40,
            align="center",
            font=dict(color="gray", size=12)
        )

        fig.update_traces(
            textposition=skill_stats['TextPos'],
            textfont_size=12,
            marker=dict(line=dict(width=1, color='black'), opacity=0.9)
        )

        fig.update_layout(height=700, plot_bgcolor='rgba(240,240,240,0.5)')

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top Salaries")
            st.dataframe(skill_stats.nlargest(5, 'Average_Salary')[['skills_list', 'Average_Salary']].style.format(
                {'Average_Salary': '${:,.0f}'}), hide_index=True)
        with c2:
            st.subheader("Highest Demand")
            st.dataframe(skill_stats.nlargest(5, 'Job_Count')[['skills_list', 'Job_Count']], hide_index=True)


if __name__ == "__main__":
    main()