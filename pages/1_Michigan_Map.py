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
    if f["id"].startswith("26")
]

county_index = pd.DataFrame({
    "fips": [f["id"] for f in mi_features],
    "County": [f["properties"]["NAME"] for f in mi_features]
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
    paper_bgcolor='grey',
    plot_bgcolor='grey',
    height=650
)

st.plotly_chart(fig, use_container_width=True)
# =====================================================
# COUNTY TABLE (SYNCED WITH MAP)
# =====================================================

st.markdown("<h3 style='text-align:center;'>County Distribution Table</h3>", unsafe_allow_html=True)

# -------------------------
# PREP TABLE DATA
# -------------------------
table = aligned.copy()

# Share of total
total = table['Graduated'].sum()

if total > 0:
    table['Share of Total'] = (table['Graduated'] / total * 100).round(2)
else:
    table['Share of Total'] = 0

# Rename columns
table = table.rename(columns={
    'fips': 'CountyFips',
    'County': 'County Name'
})

table = table[['CountyFips', 'County Name', 'Graduated', 'Share of Total']]

# Sort
table = table.sort_values('Graduated', ascending=False).reset_index(drop=True)

# -------------------------
# PAGINATION SETTINGS
# -------------------------
rows_per_page = 10
total_rows = len(table)
total_pages = max(1, (total_rows - 1) // rows_per_page + 1)

# Page selector
page = st.number_input(
    "Page",
    min_value=1,
    max_value=total_pages,
    value=1,
    step=1
)

# -------------------------
# SLICE DATA
# -------------------------
start = (page - 1) * rows_per_page
end = start + rows_per_page

page_data = table.iloc[start:end]

# -------------------------
# DISPLAY TABLE
# -------------------------
st.dataframe(
    page_data,
    use_container_width=True
)

