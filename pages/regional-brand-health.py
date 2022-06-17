import streamlit as st
import pandas as pd
import numpy as np
import s3fs
import json
import time
import plotly.express as px
import plotly.graph_objects as go

QUERY_CACHE_TTL =  600 #10 mins

# Create connection object.
# `anon=False` means not anonymous, i.e. it uses access keys to pull data.
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=QUERY_CACHE_TTL)
def read_file(filename):
    return pd.read_csv(filename)

df = read_file("s3://safegraph-places-outgoing/streamlit-demos/spend_brand_msa_mom_yoy_apr2022.csv.gz")

# LOAD GEOJSON FILE
with open("data/MSA_boundaries_v2_fixed_wkt.geojson") as response:
    geo = json.load(response)

# Sidebar 

st.sidebar.markdown(
""" 
# Regional Brand Health
### In which markets are brands performing the best vs last year?

""")

brands = df[['brands','msa_name']].groupby('brands').count().sort_values('msa_name',ascending=False).index.unique()
brand_option = st.sidebar.selectbox('Select a brand', brands)
df_brand = df.loc[df['brands']==brand_option]
# filter outliers
df_brand = df_brand.loc[df['median_yoy_change']<=300]

st.sidebar.markdown(
"""
Created using the following columns from
SafeGraph Spend (see [Docs](https://docs.safegraph.com/docs/spend)):
- `spend_pct_change_vs_prev_month`
- `spend_pct_change_vs_prev_year`

*App reads in from s3.*

"""
)

###
st.markdown("**Median Store YoY Spend Growth in Apr 2022 by MSA** (%): *(Takes ~60 seconds, be patient :sweat_smile:)*")

start = time.time()

with st.spinner('Plotting data for all MSAs...'):
    # Geographic Map
    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geo,
            locations=df_brand.msa_number,
            featureidkey="properties.GEOID",
            z=df_brand.median_yoy_change,
            text=df_brand.msa_name,
            colorscale="RdBu",
            zmin=-100,
            zmax=100,
            marker_opacity=0.9,
            marker_line_width=0.5,
        )
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3,
        mapbox_center = {"lat": 37.0902, "lon": -95.7129}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig)

end = time.time()
elapsed = end - start
st.markdown(f"*Plotting took {elapsed} seconds.*")

# Raw data
st.markdown('**Data used for plotting above**')
st.dataframe(df_brand)

### Appendix

# # Convert to geojson ahead of time
# from shapely import wkt
# import geopandas as gpd
# df = pd.read_csv("data/MSA_boundaries_v2_fixed_wkt.csv")
# df = df.loc[df['LSAD']=='M1']
# df['geometry'] = df['geometry'].astype(str).apply(wkt.loads)
# gpd_to_map = (
#   gpd.GeoDataFrame(df, geometry = 'geometry', crs = 'EPSG:4326')
# )
# gpd_to_map.to_file("data/MSA_boundaries_v2_fixed_wkt.geojson", driver="GeoJSON")  