import streamlit as st
import pandas as pd
import numpy as np
import s3fs
import plotly.express as px

QUERY_CACHE_TTL =  600 #10 mins

# Create connection object.
# `anon=False` means not anonymous, i.e. it uses access keys to pull data.
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=QUERY_CACHE_TTL)
def read_file(filename):
    return pd.read_csv(filename)

df = read_file("s3://safegraph-places-outgoing/demos/spend_cross_shopping_w_online.csv.gz")
df.sort_values('raw_num_customers',ascending=False,inplace=True)
df.set_index('placekey',inplace=True)

# Sidebar 

st.sidebar.markdown(
""" 
# Competitive Intel by Market
### In Which Markets is IKEA outperforming the competition?
"""
)

msas = df[['msa_name','location_name']].groupby('msa_name').count().sort_values('location_name',ascending=False).index.unique()
msa_option = st.sidebar.selectbox('Select a market', msas)
df_msa = df.loc[df['msa_name']==msa_option]

competitor_brands = st.sidebar.multiselect(
     'Select competitor brands',
     df_msa.columns[14:],
     ["Amazon", "Target", "The Home Depot", "Lowe's", "Crate and Barrel","Ashley Furniture HomeStore"])

st.sidebar.markdown(
"""
Created using the following columns from
SafeGraph Spend (see [Docs](https://docs.safegraph.com/docs/spend#cross-shopping-columns)):
- `related_cross_shopping_` `physical_brands_pct` 
- `related_cross_shopping_` `online_merchants_pct` 
- `related_cross_shopping_` `same_category_brands_pct` 

*App reads in from s3.*
"""
)

# Main app body
verb = 'are' if len(df_msa)>1 else 'is'
plural = 's' if len(df_msa)>1 else ''
st.markdown(f"There {verb} **{len(df_msa)}** IKEA location{plural} with Spend data in **{msa_option}**.")

# Data transofmrations
df_msa = df_msa.rename({"LATITUDE":"lat","LONGITUDE":"lon"},axis='columns')
df_msa_for_plot = df_msa[['msa_name','latitude','longitude','street_address','city','state','zip_code','raw_num_customers']+competitor_brands].fillna(0)
weighted_avg_by_brand = {}
for comp in competitor_brands:
    weighted_avg_by_brand[comp] = \
        [(df_msa_for_plot['raw_num_customers'] * df_msa_for_plot[comp] / df_msa_for_plot['raw_num_customers'].sum()).sum()]

#Show bar chart
df_bar = pd.DataFrame.from_dict(weighted_avg_by_brand,orient='index',columns=['cross_shopping_pct'])\
           .sort_values('cross_shopping_pct')
df_bar.reset_index(inplace=True)
df_bar.rename(columns={'index':''},inplace=True)
fig = px.bar(df_bar, x="cross_shopping_pct", y="", orientation='h',
             title="Average customer share by competitor brand",)
st.plotly_chart(fig, use_container_width=True)
# st.write(df_bar)

# Show map
st.map(df_msa,zoom=9)

# Raw data
st.markdown('**Data used for plotting above**')
st.write(df_msa_for_plot)
