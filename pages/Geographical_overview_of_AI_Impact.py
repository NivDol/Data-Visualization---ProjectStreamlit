import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
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
        df = pd.read_csv("database_ai_job_final.csv")
        df['is_same_location'] = (df['employee_residence'] == df['company_location']).astype(int)
        return df
    except FileNotFoundError:
        return pd.DataFrame()


df = load_data()
experience_col = 'years_experience'

if not df.empty:
    global_exp_avg = df.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
    max_emp_count = df.groupby('employee_residence').size().max()
    max_comp_count = df.groupby('company_location').size().max()
    # Unified scale for both Single Views
    GLOBAL_MAX_COUNT = max(max_emp_count, max_comp_count)
else:
    GLOBAL_MAX_COUNT = 100
    global_exp_avg = pd.DataFrame()


def create_graphs(data, title_suffix, color_main):
    graphs = {}
    if data.empty: return graphs

    # G1: Top 5 Roles
    top_5 = data['job_title'].value_counts().head(5).reset_index()
    fig1 = px.bar(top_5, x='job_title', y='count')
    fig1.update_traces(marker_color=color_main)
    fig1.update_layout(
        height=350, margin=dict(t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", title=dict(text=f"Top Roles ({title_suffix})", font=dict(size=20)),
        font=dict(size=16)
    )
    graphs['top_roles'] = fig1

    # G2: In-State vs Out-of-State
    loc_dist = data['is_same_location'].value_counts().reset_index()
    loc_dist.columns = ['is_same', 'count']
    total_count = loc_dist['count'].sum()
    loc_dist['percentage'] = (loc_dist['count'] / total_count * 100).round(1) if total_count > 0 else 0
    loc_dist['Location Type'] = loc_dist['is_same'].map({1: 'In-State (Domestic)', 0: 'Out-of-State (Int\'l)'})

    chart_title = f"Talent Source ({title_suffix})" if "Emp" in title_suffix else f"Work Location ({title_suffix})"
    fig2 = px.bar(loc_dist, x='count', y='Location Type', color='Location Type', text='percentage',
                  orientation='h',
                  color_discrete_map={'In-State (Domestic)': color_main, 'Out-of-State (Int\'l)': '#B0BEC5'})
    fig2.update_traces(texttemplate='%{text}%', textposition='outside')
    fig2.update_layout(height=350, margin=dict(t=40, b=20, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", title=dict(text=chart_title, font=dict(size=20)),
                       showlegend=False, font=dict(size=16))
    graphs['top_countries'] = fig2
    return graphs


def create_comparison_line_chart(df_left, name_left, color_left, df_right, name_right, color_right):
    fig = go.Figure()
    all_values = []
    if not df.empty:
        global_vals = global_exp_avg['salary_usd'].dropna().tolist()
        all_values.extend(global_vals)
        fig.add_trace(go.Scatter(x=global_exp_avg[experience_col], y=global_exp_avg['salary_usd'],
                                 mode='lines', line=dict(color='grey', dash='dot', width=2), name='Global Average'))
    for d, n, c in [(df_left, name_left, color_left), (df_right, name_right, color_right)]:
        if not d.empty:
            exp = d.groupby(experience_col)['salary_usd'].mean().sort_index().reset_index()
            all_values.extend(exp['salary_usd'].dropna().tolist())
            fig.add_trace(go.Scatter(x=exp[experience_col], y=exp['salary_usd'], mode='lines+markers',
                                     line=dict(color=c, width=3), name=n))
    if all_values:
        y_min, y_max = min(all_values) * 0.8, max(all_values) * 1.05
        clean_step = math.ceil(((y_max - y_min) / 5) / 5000) * 5000
        fig.update_yaxes(range=[y_min, y_max], autorange=False, tick0=0, dtick=clean_step, tickformat='$,.0f')
    fig.update_layout(height=350, title=dict(text="💸 Salary Comparison", font=dict(size=20)),
                      font=dict(size=16), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


# ---------------------------------------------------------
# 4. APP LAYOUT
# ---------------------------------------------------------
st.title("🌍 Global AI Adoption Landscape")

if df.empty:
    st.error("Data file 'database_ai_job_final.csv' not found.")
else:
    # --- CONTROLS ROW (Restored Button Names) ---
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

    # Dynamic Global List Logic
    if st.session_state['show_global_top10']:
        if view_mode == "Comparator":
            emp_counts = df['employee_residence'].value_counts()
            comp_counts = df['company_location'].value_counts()
            total_activity = emp_counts.add(comp_counts, fill_value=0).sort_values(ascending=False).head(
                10).reset_index()
            total_activity.columns = ['Country', 'Total Activity (Emp + Comp)']
            st.info("Top 10 Countries by Combined Activity")
            st.dataframe(total_activity, use_container_width=True, hide_index=True)
        else:
            col = 'employee_residence' if view_mode == "Employee Residence" else 'company_location'
            top_10 = df[col].value_counts().head(10).reset_index()
            top_10.columns = ['Country', 'Count']
            st.info(f"Top 10 Countries by {view_mode}")
            st.dataframe(top_10, use_container_width=True, hide_index=True)

    # --- MODE 1: COMPARATOR ---
    if view_mode == "Comparator":
        emp_countries = set(df['employee_residence'].unique())
        comp_countries = set(df['company_location'].unique())
        all_countries = list(emp_countries.union(comp_countries))
        map_data = pd.DataFrame({'country': all_countries})
        map_data['category'] = map_data['country'].apply(
            lambda c: "Both (Employees & Companies)" if c in emp_countries and c in comp_countries else (
                "Employees Only" if c in emp_countries else "Companies Only"))

        fig_map = px.choropleth(map_data, locations="country", locationmode='country names', color="category",
                                color_discrete_map={"Employees Only": "#FFD700", "Companies Only": "#1E88E5",
                                                    "Both (Employees & Companies)": "#00CC96"},
                                custom_data=["country"], projection="natural earth")
        fig_map.update_geos(showcountries=True, countrycolor="white", showland=True, landcolor="#f0f0f0")
        fig_map.update_layout(height=450, margin={"r": 0, "t": 0, "l": 0, "b": 0})
        selection = st.plotly_chart(fig_map, on_select="rerun", use_container_width=True)

        if selection.get("selection") and selection["selection"].get("points"):
            clicked = selection["selection"]["points"][0]["customdata"][0]
            if clicked == st.session_state['primary_country']:
                reset_app()
                st.rerun()
            elif st.session_state['primary_country'] is None or st.session_state['compare_mode'] == "Standard View":
                st.session_state['primary_country'] = clicked
            else:
                st.session_state['secondary_country'] = clicked

        st.divider()
        if st.session_state['primary_country'] is None:
            # Default Global Views
            col_L, col_R = st.columns(2)
            with col_L:
                st.subheader("Global Employees")
                g = create_graphs(df, "Global Emp", "#EF553B")
                st.plotly_chart(g['top_roles'], use_container_width=True)
                st.plotly_chart(g['top_countries'], use_container_width=True)
            with col_R:
                st.subheader("Global Companies")
                g = create_graphs(df, "Global Comp", "#1E88E5")
                st.plotly_chart(g['top_roles'], use_container_width=True)
                st.plotly_chart(g['top_countries'], use_container_width=True)
        else:
            primary = st.session_state['primary_country']
            st.subheader(f"📍 Analyzing: {primary}")
            mode = st.radio("Mode:", ["Standard View", "Compare Employees", "Compare Companies"], horizontal=True,
                            index=["Standard View", "Compare Employees", "Compare Companies"].index(
                                st.session_state['compare_mode']))
            if mode != st.session_state['compare_mode']:
                st.session_state['compare_mode'] = mode
                st.session_state['secondary_country'] = None
                st.rerun()

            df_L = df[df['company_location' if mode == "Compare Companies" else 'employee_residence'] == primary]
            name_L = f"{primary} ({'Comp' if 'Companies' in mode else 'Emp'})"
            color_L = "#1E88E5" if "Comp" in name_L else "#EF553B"

            if mode == "Standard View":
                df_R, name_R, color_R = df[df['company_location'] == primary], f"{primary} (Comp)", "#1E88E5"
            else:
                sec = st.session_state['secondary_country']
                t_col = "employee_residence" if "Employees" in mode else "company_location"
                df_R, name_R, color_R = (df[df[t_col] == sec], f"{sec}", "#9c27b0") if sec else (
                pd.DataFrame(), "Select Country...", "#9c27b0")

            colL, colR = st.columns(2)
            with colL:
                st.subheader(name_L)
                for g in create_graphs(df_L, name_L, color_L).values(): st.plotly_chart(g, use_container_width=True)
            with colR:
                if not df_R.empty:
                    st.subheader(name_R)
                    for g in create_graphs(df_R, name_R, color_R).values(): st.plotly_chart(g, use_container_width=True)
                else:
                    st.info("Select a second country from the map.")

            st.divider()
            if not df_L.empty and (not df_R.empty or mode == "Standard View"):
                st.plotly_chart(create_comparison_line_chart(df_L, name_L, color_L, df_R, name_R, color_R),
                                use_container_width=True)

    # --- MODE 2 & 3: SINGLE VIEW ---
    else:
        loc_col = "employee_residence" if view_mode == "Employee Residence" else "company_location"
        g_color = "#EF553B" if view_mode == "Employee Residence" else "#1E88E5"
        scale_colors = px.colors.sequential.Reds if view_mode == "Employee Residence" else px.colors.sequential.Blues

        col_map, col_graphs = st.columns([2, 3])
        with col_map:
            st.subheader(f"Total Count by {view_mode}")
            map_df = df.groupby(loc_col).size().reset_index(name='count')
            fig_map = px.choropleth(map_df, locations=loc_col, locationmode='country names', color="count",
                                    color_continuous_scale=scale_colors, range_color=[0, GLOBAL_MAX_COUNT],
                                    # Unified Scale
                                    projection="natural earth", custom_data=[loc_col])
            fig_map.update_geos(showcountries=True, countrycolor="white", showland=True, landcolor="#f0f0f0")
            fig_map.update_layout(height=600, margin={"r": 0, "t": 0, "l": 0, "b": 0})
            sel = st.plotly_chart(fig_map, on_select="rerun", use_container_width=True)

        selected = sel["selection"]["points"][0]["customdata"][0] if sel.get("selection") and sel["selection"].get(
            "points") else None

        with col_graphs:
            target_df = df[df[loc_col] == selected] if selected else df
            line_name = f"{selected} ({'Emp' if view_mode == 'Employee Residence' else 'Comp'})" if selected else (
                "Global Emp" if view_mode == "Employee Residence" else "Global Comp")

            st.header(f"📊 {selected if selected else 'Global ' + view_mode}")
            graphs = create_graphs(target_df, selected or line_name, g_color)
            r1c1, r1c2 = st.columns(2)
            with r1c1: st.plotly_chart(graphs['top_roles'], use_container_width=True)
            with r1c2: st.plotly_chart(graphs['top_countries'], use_container_width=True)
            st.divider()
            st.plotly_chart(create_comparison_line_chart(target_df, line_name, g_color, pd.DataFrame(), "", ""),
                            use_container_width=True)