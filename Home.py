import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="Global AI Adoption Landscape",
    page_icon="🌍",
    layout="wide"
)

# ---------------------------------------------------------
# 2. SESSION STATE MANAGEMENT
# ---------------------------------------------------------
if 'primary_country' not in st.session_state:
    st.session_state['primary_country'] = None
if 'secondary_country' not in st.session_state:
    st.session_state['secondary_country'] = None
if 'compare_mode' not in st.session_state:
    st.session_state['compare_mode'] = "Standard View"
if 'show_global_top10' not in st.session_state:
    st.session_state['show_global_top10'] = False


def reset_app():
    st.session_state['primary_country'] = None
    st.session_state['secondary_country'] = None
    st.session_state['compare_mode'] = "Standard View"
    st.session_state['show_global_top10'] = False


# ---------------------------------------------------------
# 3. DATA & HELPERS
# ---------------------------------------------------------
@st.cache_data
def load_data():
    try:
        # ensuring we use the standard dataset
        df = pd.read_csv("database_ai_job_final.csv")
        # Create logic for In-State vs Out-of-State
        # 1 = Same Location, 0 = Different Location
        df['is_same_location'] = (df['employee_residence'] == df['company_location']).astype(int)
        return df
    except FileNotFoundError:
        return pd.DataFrame()


df = load_data()

# Global Constants
experience_col = 'years_experience'
# Handle missing data if file isn't loaded yet
if not df.empty:
    global_exp_avg = df.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
    max_emp_count = df.groupby('employee_residence').size().max()
    max_comp_count = df.groupby('company_location').size().max()
    GLOBAL_MAX_COUNT = max(max_emp_count, max_comp_count)
else:
    GLOBAL_MAX_COUNT = 100


# --- Updated Graphs Generator (Always 4 Graphs) ---
def create_graphs(data, title_suffix, color_main):
    graphs = {}
    if data.empty: return graphs

    # ---------------------------------------------------------
    # G1: Top 5 Roles (Bar Chart)
    # ---------------------------------------------------------
    top_5 = data['job_title'].value_counts().head(5).reset_index()
    fig1 = px.bar(top_5, x='job_title', y='count')
    fig1.update_traces(marker_color=color_main)

    # Logic: Start Y-Axis at 95% of the lowest bar
    if not top_5.empty:
        min_count = top_5['count'].min()
        max_count = top_5['count'].max()
        fig1.update_yaxes(range=[min_count * 0.95, max_count * 1.05])

    fig1.update_layout(height=350, margin=dict(t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", title=f"Top Roles ({title_suffix})")
    graphs['top_roles'] = fig1

    # ---------------------------------------------------------
    # G2: In-State vs Out-of-State (HORIZONTAL Bar Chart)
    # ---------------------------------------------------------
    loc_dist = data['is_same_location'].value_counts().reset_index()
    loc_dist.columns = ['is_same', 'count']

    # Calculate Percentage
    total_count = loc_dist['count'].sum()
    if total_count > 0:
        loc_dist['percentage'] = (loc_dist['count'] / total_count * 100).round(1)
    else:
        loc_dist['percentage'] = 0

    # Map labels
    loc_dist['Location Type'] = loc_dist['is_same'].map({
        1: 'In-State (Domestic)',
        0: 'Out-of-State (Int\'l)'
    })

    # Set Dynamic Title based on context
    if "Emp" in title_suffix or "Employee" in title_suffix:
        chart_title = f"Talent Source ({title_suffix})"
    else:
        chart_title = f"Work Location ({title_suffix})"

    # Colors
    colors_bar = {
        'In-State (Domestic)': color_main,
        'Out-of-State (Int\'l)': '#B0BEC5'
    }

    fig2 = px.bar(
        loc_dist,
        x='count',
        y='Location Type',
        color='Location Type',
        text='percentage',
        orientation='h',
        color_discrete_map=colors_bar
    )

    fig2.update_traces(texttemplate='%{text}%', textposition='outside')

    fig2.update_layout(
        height=350,
        margin=dict(t=40, b=20, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=chart_title,
        showlegend=False,
        xaxis_title="Count",
        yaxis_title=None
    )
    graphs['top_countries'] = fig2

    # ---------------------------------------------------------
    # G3: Scatter (Lucrative Roles)
    # ---------------------------------------------------------
    scatter_full = data.groupby(['job_title', 'experience_level']).agg(
        avg_salary=('salary_usd', 'mean'), job_count=('salary_usd', 'count')).reset_index()
    try:
        top_10_scatter = scatter_full.groupby('experience_level').apply(
            lambda x: x.nlargest(10, 'avg_salary')).reset_index(drop=True)
    except:
        top_10_scatter = scatter_full

    seq_colors = {'EN': '#bdd7e7', 'MI': '#6baed6', 'SE': '#3182bd', 'EX': '#08519c'}

    fig3 = px.scatter(top_10_scatter, x='job_count', y='avg_salary', color='experience_level',
                      hover_name='job_title', color_discrete_map=seq_colors,
                      category_orders={"experience_level": ["EN", "MI", "SE", "EX"]})

    # --- UPDATE: Added Dynamic Y-Axis Lower Limit ---
    if not top_10_scatter.empty:
        min_sal = top_10_scatter['avg_salary'].min()
        max_sal = top_10_scatter['avg_salary'].max()
        # Set range: Start at 95% of the lowest salary to zoom in
        fig3.update_yaxes(range=[min_sal * 0.95, max_sal * 1.05])
    # ------------------------------------------------

    fig3.update_layout(height=350, margin=dict(t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", yaxis_tickformat='$', title=f"Lucrative Roles ({title_suffix})")
    graphs['scatter'] = fig3

    # ---------------------------------------------------------
    # G4: Pay Ladder
    # ---------------------------------------------------------
    curr_exp = data.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=curr_exp[experience_col], y=curr_exp['salary_usd'], mode='lines+markers',
                              line=dict(color=color_main, width=3), name=title_suffix))
    if not df.empty:
        fig4.add_trace(
            go.Scatter(x=global_exp_avg[experience_col], y=global_exp_avg['salary_usd'], mode='lines+markers',
                       line=dict(color='grey', dash='dot', width=1), name='Global Avg'))
    fig4.update_layout(height=350, margin=dict(t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", yaxis_tickformat='$', showlegend=True,
                       title=f"Pay Ladder ({title_suffix})")
    graphs['pay_ladder'] = fig4

    return graphs


# --- Comparison Line Chart ---
def create_comparison_line_chart(df_left, name_left, color_left, df_right, name_right, color_right):
    fig = go.Figure()
    # Global Grey Line
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=global_exp_avg[experience_col],
            y=global_exp_avg['salary_usd'],
            mode='lines',
            line=dict(color='grey', dash='dot', width=2),
            name='Global Average'
        ))

    if not df_left.empty:
        exp_left = df_left.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
        fig.add_trace(go.Scatter(
            x=exp_left[experience_col], y=exp_left['salary_usd'],
            mode='lines+markers', line=dict(color=color_left, width=3), name=name_left
        ))

    if not df_right.empty:
        exp_right = df_right.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
        fig.add_trace(go.Scatter(
            x=exp_right[experience_col], y=exp_right['salary_usd'],
            mode='lines+markers', line=dict(color=color_right, width=3), name=name_right
        ))

    fig.update_layout(
        height=350, margin=dict(t=40, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat='$', title="💸 Salary Comparison",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


# ---------------------------------------------------------
# 4. APP LAYOUT
# ---------------------------------------------------------
st.title("🌍 Global AI Adoption Landscape")

if df.empty:
    st.error("Data file 'database_ai_job_final.csv' not found. Please ensure it is in the same directory.")
else:
    # -----------------------------------
    # CONTROLS ROW
    # -----------------------------------
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        view_mode = st.radio("Select View Mode:", ("Comparator", "Employee Residence", "Company Location"),
                             horizontal=True)
    with c2:
        if st.button("🌎 Global Countries", width="stretch"):
            st.session_state['show_global_top10'] = not st.session_state['show_global_top10']
    with c3:
        if st.button("🔄 Reset Selection", width="stretch"):
            reset_app()
            st.rerun()

    # --- DYNAMIC GLOBAL LIST ---
    if st.session_state['show_global_top10']:
        if view_mode == "Comparator":
            # Sort by Emp + Comp (Total Activity)
            emp_counts = df['employee_residence'].value_counts()
            comp_counts = df['company_location'].value_counts()
            total_activity = emp_counts.add(comp_counts, fill_value=0).sort_values(ascending=False).head(10)
            top_10 = total_activity.reset_index()
            top_10.columns = ['Country', 'Total Activity (Emp + Comp)']
            st.info("Top 10 Countries by Combined Activity (Employees + Companies)")

        elif view_mode == "Employee Residence":
            top_10 = df['employee_residence'].value_counts().head(10).reset_index()
            top_10.columns = ['Country', 'Employee Count']
            st.info("Top 10 Countries by Employee Residence")

        else:  # Company Location
            top_10 = df['company_location'].value_counts().head(10).reset_index()
            top_10.columns = ['Country', 'Company Count']
            st.info("Top 10 Countries by Company Location")

        st.dataframe(top_10, width="stretch", hide_index=True)

    # -----------------------------------
    # MODE 1: COMPARATOR (SPLIT VIEW)
    # -----------------------------------
    if view_mode == "Comparator":
        emp_countries = set(df['employee_residence'].unique())
        comp_countries = set(df['company_location'].unique())
        all_countries = list(emp_countries.union(comp_countries))
        map_data = pd.DataFrame({'country': all_countries})


        def get_category(c):
            is_emp = c in emp_countries
            is_comp = c in comp_countries
            if is_emp and is_comp:
                return "Both (Employees & Companies)"
            elif is_emp:
                return "Employees Only"
            else:
                return "Companies Only"


        map_data['category'] = map_data['country'].apply(get_category)
        color_map = {"Employees Only": "#FFD700", "Companies Only": "#1E88E5",
                     "Both (Employees & Companies)": "#00CC96"}

        if st.session_state['primary_country'] is None:
            st.info("👆 Click a country to analyze. Default: Global Stats.")
        elif st.session_state['compare_mode'] != "Standard View":
            st.warning(f"📍 Select a SECOND country to compare with {st.session_state['primary_country']}.")

        fig_map = px.choropleth(
            map_data, locations="country", locationmode='country names', color="category",
            color_discrete_map=color_map, custom_data=["country", "category"], projection="natural earth"
        )
        fig_map.update_geos(showland=True, landcolor="#f0f0f0", showcountries=True, countrycolor="white")
        fig_map.update_layout(height=450, margin={"r": 0, "t": 0, "l": 0, "b": 0}, legend=dict(y=0.99, x=0.01))

        selection = st.plotly_chart(fig_map, on_select="rerun", width="stretch")

        clicked_country = None
        if isinstance(selection, dict) and selection.get("selection") and selection["selection"].get("points"):
            clicked_country = selection["selection"]["points"][0]["customdata"][0]

        if clicked_country:
            if st.session_state['primary_country'] is None:
                st.session_state['primary_country'] = clicked_country
            elif (st.session_state['primary_country'] is not None) and \
                    (st.session_state['compare_mode'] != "Standard View") and \
                    (clicked_country != st.session_state['primary_country']):
                st.session_state['secondary_country'] = clicked_country

        st.divider()

        # VIEW LOGIC
        if st.session_state['primary_country'] is None:
            # Global
            col_L, col_R = st.columns(2)
            with col_L:
                st.subheader("Global Employees")
                g = create_graphs(df, "Global Emp", "#EF553B")
                st.plotly_chart(g['top_roles'], width="stretch")
                st.plotly_chart(g['top_countries'], width="stretch")
                st.plotly_chart(g['scatter'], width="stretch")
                st.plotly_chart(g['pay_ladder'], width="stretch")
            with col_R:
                st.subheader("Global Companies")
                g = create_graphs(df, "Global Comp", "#1E88E5")
                st.plotly_chart(g['top_roles'], width="stretch")
                st.plotly_chart(g['top_countries'], width="stretch")
                st.plotly_chart(g['scatter'], width="stretch")
                st.plotly_chart(g['pay_ladder'], width="stretch")
        else:
            # Specific
            primary = st.session_state['primary_country']
            st.subheader(f"📍 Analyzing: {primary}")

            # Mode Switcher
            is_both = map_data[map_data['country'] == primary]['category'].iloc[0] == "Both (Employees & Companies)"
            if is_both:
                mode = st.radio("Mode:", ["Standard View", "Compare Employees", "Compare Companies"],
                                horizontal=True,
                                index=["Standard View", "Compare Employees", "Compare Companies"].index(
                                    st.session_state['compare_mode']))
                if mode != st.session_state['compare_mode']:
                    st.session_state['compare_mode'] = mode
                    st.session_state['secondary_country'] = None
                    st.rerun()
            else:
                req = "Compare Employees" if "Employees" in map_data[map_data['country'] == primary]['category'].iloc[
                    0] else "Compare Companies"
                st.session_state['compare_mode'] = req

            # Prep Data
            if st.session_state['compare_mode'] == "Compare Companies":
                df_L = df[df['company_location'] == primary];
                name_L = f"{primary} (Comp)";
                color_L = "#1E88E5"
            else:
                df_L = df[df['employee_residence'] == primary];
                name_L = f"{primary} (Emp)";
                color_L = "#EF553B"

            if st.session_state['compare_mode'] == "Standard View":
                df_R = df[df['company_location'] == primary];
                name_R = f"{primary} (Comp)";
                color_R = "#1E88E5"
            else:
                sec = st.session_state['secondary_country']
                if sec:
                    t_col = "employee_residence" if "Employees" in st.session_state[
                        'compare_mode'] else "company_location"
                    df_R = df[df[t_col] == sec];
                    name_R = f"{sec}";
                    color_R = "#9c27b0"
                else:
                    df_R = pd.DataFrame();
                    name_R = "Select Country...";
                    color_R = "#9c27b0"

            # Render
            cL, cR = st.columns(2)
            with cL:
                st.subheader(name_L)
                g = create_graphs(df_L, name_L, color_L)
                if g:
                    for k in g: st.plotly_chart(g[k], width="stretch")
            with cR:
                if not df_R.empty:
                    st.subheader(name_R)
                    g = create_graphs(df_R, name_R, color_R)
                    if g:
                        for k in g: st.plotly_chart(g[k], width="stretch")
                else:
                    st.info("Select a second country from the map.")

            st.divider()
            if not df_L.empty and (not df_R.empty or st.session_state['compare_mode'] == "Standard View"):
                st.plotly_chart(create_comparison_line_chart(df_L, name_L, color_L, df_R, name_R, color_R),
                                width="stretch")

    # -----------------------------------
    # MODE 2: SINGLE VIEWS (FIXED LAYOUT)
    # -----------------------------------
    else:
        location_col = "employee_residence" if view_mode == "Employee Residence" else "company_location"
        graph_color = "#EF553B" if view_mode == "Employee Residence" else "#1E88E5"
        mode_label = "Global Employees" if view_mode == "Employee Residence" else "Global Companies"

        col_map, col_graphs = st.columns([2, 3])

        with col_map:
            st.subheader(f"Total Count by {view_mode}")
            map_data = df.groupby(location_col).size().reset_index(name='total_count')
            fig_map = px.choropleth(
                map_data, locations=location_col, locationmode='country names', color="total_count",
                color_continuous_scale=px.colors.sequential.Reds, range_color=[0, GLOBAL_MAX_COUNT],
                custom_data=[location_col], projection="natural earth"
            )
            fig_map.update_geos(showland=True, landcolor="#f0f0f0", showcountries=True, countrycolor="white")
            fig_map.update_layout(height=600, margin={"r": 0, "t": 0, "l": 0, "b": 0})

            selection = st.plotly_chart(fig_map, on_select="rerun", width="stretch")

        selected_country = None
        if isinstance(selection, dict) and selection.get("selection") and selection["selection"].get("points"):
            selected_country = selection["selection"]["points"][0]["customdata"][0]

        with col_graphs:
            target_df = pd.DataFrame()
            target_name = ""

            if selected_country:
                target_name = f"📊 {selected_country}"
                target_df = df[df[location_col] == selected_country]
            else:
                target_name = f"🌐 {mode_label} (Default)"
                target_df = df
                if view_mode == "Employee Residence":
                    selected_country = "Global Emp"
                else:
                    selected_country = "Global Comp"

            st.header(target_name)

            g = create_graphs(target_df, selected_country, graph_color)

            if g:
                r1_c1, r1_c2 = st.columns(2)
                r2_c1, r2_c2 = st.columns(2)

                with r1_c1:
                    st.plotly_chart(g['top_roles'], width="stretch")
                with r1_c2:
                    st.plotly_chart(g['top_countries'], width="stretch")
                with r2_c1:
                    st.plotly_chart(g['scatter'], width="stretch")
                with r2_c2:
                    st.plotly_chart(g['pay_ladder'], width="stretch")