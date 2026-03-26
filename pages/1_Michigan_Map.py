import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    df = pd.read_csv("gvsudegree_clean.csv", low_memory=False)

    df['Graduated'] = pd.to_numeric(df['Graduated'], errors='coerce').fillna(0)

    df['stfip'] = (
        pd.to_numeric(df['stfip'], errors='coerce')
        .fillna(0).astype(int).astype(str).str.zfill(2)
    )

    df['fips'] = (
        pd.to_numeric(df['fips'], errors='coerce')
        .fillna(0).astype(int).astype(str).str.zfill(5)
    )

    return df

df = load_data()

# =====================================================
# FILTER MICHIGAN
# =====================================================
mi_df = df[df['stfip'] == '26']

# =====================================================
# DROPDOWN (MAJOR)
# =====================================================
majors = ['All'] + sorted(mi_df['Major'].dropna().unique())
selected_major = st.selectbox("Select Major", majors)

if selected_major == 'All':
    dff = mi_df.copy()
else:
    dff = mi_df[mi_df['Major'] == selected_major]

# =====================================================
# AGGREGATE
# =====================================================
county_df = dff.groupby('fips', as_index=False)['Graduated'].sum()

# =====================================================
# UI
# =====================================================
st.markdown("<h2 style='text-align:center;'>Michigan County Distribution</h2>", unsafe_allow_html=True)

# =====================================================
# MAP
# =====================================================
fig = px.choropleth(
    county_df,
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations='fips',
    color='Graduated',
    color_continuous_scale='Blues',
    scope='usa'
)

fig.update_geos(fitbounds="locations", visible=False)

fig.update_layout(
    paper_bgcolor='lightgrey',
    plot_bgcolor='lightgrey',
    height=650
)

st.plotly_chart(fig, use_container_width=True)
