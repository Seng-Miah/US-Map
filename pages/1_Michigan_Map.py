import streamlit as st
import pandas as pd
import plotly.express as px
import json

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
# LOAD COUNTY GEOJSON (WITH NAMES)
# =====================================================
import requests

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    response = requests.get(url)
    return response.json()

geojson = load_geojson()

# Extract Michigan counties only
mi_features = [
    f for f in geojson["features"]
    if f["properties"]["GEOID"].startswith("26")
]

county_index = pd.DataFrame({
    "fips": [f["properties"]["GEOID"] for f in mi_features],
    "County": [f["properties"]["name"] for f in mi_features]
})

# Build full county index
county_index = pd.DataFrame({
    "fips": [f["id"] for f in mi_features],
    "County": [f["properties"]["NAME"] for f in mi_features]
})

# =====================================================
# FILTER MICHIGAN DATA
# =====================================================
mi_df = df[df['stfip'] == '26']

# =====================================================
# DROPDOWN
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
# 🔥 ALIGN WITH FULL COUNTY LIST
# =====================================================
aligned = county_index.merge(
    county_df,
    on='fips',
    how='left'
)

aligned['Graduated'] = aligned['Graduated'].fillna(0)

# =====================================================
# UI
# =====================================================
st.markdown("<h2 style='text-align:center;'>Michigan County Distribution</h2>", unsafe_allow_html=True)

# =====================================================
# MAP
# =====================================================
fig = px.choropleth(
    aligned,
    geojson={"type": "FeatureCollection", "features": mi_features},
    locations='fips',
    color='Graduated',
    color_continuous_scale='Blues',
)

fig.update_traces(
    customdata=aligned[['County']],
    hovertemplate="<b>%{customdata[0]}</b><br>Graduated: %{z:,}<extra></extra>"
)

fig.update_geos(fitbounds="locations", visible=False)

fig.update_layout(
    paper_bgcolor='lightgrey',
    plot_bgcolor='lightgrey',
    height=650
)

st.plotly_chart(fig, use_container_width=True)

