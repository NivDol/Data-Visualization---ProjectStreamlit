import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title="The AI Skill Wars", layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('ai_job_dataset - all.csv')
        return df
    except FileNotFoundError:
        st.error("Data file not found. Please check 'ai_job_dataset - all.csv' exists.")
        return None


def main():
    st.title("The Skill Wars: Which Tech Knowledge Pays the Most?")

    df = load_data()

    if df is not None:
        
        # --- Sidebar: Experience Level Filter ---
        st.sidebar.subheader("Experience Level:")
        
        all_levels = sorted(df['experience_level'].unique().tolist())
        
        check_all = st.sidebar.checkbox("All Levels", value=True)
        
        selected_levels_manual = []
        for level in all_levels:
            if st.sidebar.checkbox(level, value=True, key=level):
                selected_levels_manual.append(level)
        
        if check_all:
            final_selection = all_levels
            st.sidebar.caption("Showing all experience levels (All Levels is checked).")
        else:
            final_selection = selected_levels_manual

        # Filter Data
        if final_selection:
            filtered_df = df[df['experience_level'].isin(final_selection)]
        else:
            st.warning("Please select at least one experience level.")
            st.stop()

        # --- Identify Current View Scenario (For Text Positioning) ---
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
        filtered_df = filtered_df.assign(skills_list=filtered_df['required_skills'].str.split(', '))
        df_exploded = filtered_df.explode('skills_list')
        
        df_exploded['skills_list'] = df_exploded['skills_list'].replace({
            'Data Visualization': 'Data Viz',
            'Machine Learning': 'ML',
            'Natural Language Processing': 'NLP',
            'Computer Vision': 'CV'
        })
        
        skill_stats = df_exploded.groupby('skills_list').agg(
            Average_Salary=('salary_usd', 'mean'),
            Job_Count=('job_id', 'count')
        ).reset_index()

        skill_stats = skill_stats[skill_stats['Job_Count'] >= 10]
        skill_stats['Average_Salary'] = skill_stats['Average_Salary'].round(0)

        # --- Label Logic ---
        num_labels = 30 
        
        skill_stats['Score'] = (skill_stats['Average_Salary'] / skill_stats['Average_Salary'].max()) + \
                               (skill_stats['Job_Count'] / skill_stats['Job_Count'].max())
        
        top_skills = skill_stats.nlargest(num_labels, 'Score')['skills_list'].tolist()
        skill_stats['Label'] = skill_stats['skills_list'].apply(lambda x: x if x in top_skills else '')

        # --- Text Positioning Logic ---
        median_count = skill_stats['Job_Count'].median()
        
        def get_text_position(row):
            skill_name = row['skills_list']
            
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

            if 'Spark' in skill_name:
                return 'middle left'
            elif 'Data Viz' in skill_name:
                return 'middle right'
            
            if row['Job_Count'] > median_count:
                return 'middle left'
            else:
                return 'middle right'
        
        skill_stats['TextPos'] = skill_stats.apply(get_text_position, axis=1)

        # --- Plot Creation ---
        if not skill_stats.empty:
            
            median_salary = skill_stats['Average_Salary'].median()
            
            fig = px.scatter(
                skill_stats,
                x="Job_Count",
                y="Average_Salary",
                size="Job_Count", 
                color="Average_Salary", 
                text="Label", 
                color_continuous_scale="RdBu", 
                hover_name="skills_list",
                hover_data={"Job_Count": True, "Average_Salary": ":$,.0f", "Label": False, "TextPos": False},
                title=f"AI Skills Landscape: Demand vs. Salary ({current_scenario if current_scenario != 'ALL' else 'All Levels'})",
                labels={"Job_Count": "Demand (Job Count)", "Average_Salary": "Yearly Salary ($)"}
            )

            fig.add_hline(y=median_salary, line_dash="dash", line_color="gray", opacity=0.7)
            fig.add_vline(x=median_count, line_dash="dash", line_color="gray", opacity=0.7)

            fig.add_annotation(
                x=0, xref="paper",
                y=median_salary, yref="y",
                text="Median Salary",
                showarrow=False,
                yshift=10,
                xshift=2,
                align="left",
                font=dict(color="#333333", size=12) 
            )

            fig.add_annotation(
                x=median_count, xref="x",
                y=0, yref="paper",
                text="Median Demand",
                showarrow=False,
                yshift=10,                  
                xshift=40,
                align="center",
                font=dict(color="#333333", size=12)
            )

            fig.update_traces(
                textposition=skill_stats['TextPos'],
                textfont_size=12,
                marker=dict(line=dict(width=1, color='black'), opacity=0.9)
            )
            
            fig.update_layout(
                height=700, 
                plot_bgcolor='rgba(240,240,240,0.5)',
                xaxis=dict(
                    title_font=dict(size=18), 
                    tickfont=dict(size=14)    
                ),
                yaxis=dict(
                    title_font=dict(size=18), 
                    tickfont=dict(size=14)    
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Top Salaries")
                st.dataframe(skill_stats.nlargest(5, 'Average_Salary')[['skills_list', 'Average_Salary']].style.format({'Average_Salary': '${:,.0f}'}), hide_index=True)
            with c2:
                st.subheader("Highest Demand")
                st.dataframe(skill_stats.nlargest(5, 'Job_Count')[['skills_list', 'Job_Count']], hide_index=True)

        else:
            st.warning("No data to display.")

if __name__ == "__main__":
    main()