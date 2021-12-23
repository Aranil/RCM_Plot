# Script for displaying graphs of SAR parameters from a database in a streamlit web app #

import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# connection to db
try:
    db = sqlite3.connect(
        'C:/Users/Markus Adam/Studium/GEO419/students_db_sql_queries/students_db_sql_queries/RCM_work.db')
    cursor = db.cursor()
    print("Successfully Connected to SQLite Database")
except sqlite3.Error as error:
    print("Error while connecting to Database", error)

# set page layout
st.set_page_config(layout="wide")

# create title and description
st.title('Radar Crop Monitor APP')
st.markdown('Display SAR Parameters for Crop Monitoring')
st.markdown("Please select the main and dependent filter first")
st.markdown("Please note that displaying the data may take some time")
st.markdown('#')

# create titles for data filters
st.sidebar.title("Filters")
st.sidebar.markdown("#")
st.sidebar.header('Main Filters')

# load values from specific table columns for value selection (filters) by user
aoi_names = pd.read_sql_query('select distinct aoi from areaofinterest;', db)
years = pd.read_sql_query("select distinct year from areaofinterest;", db)
crop_types = pd.read_sql_query("select distinct crop_type from croplegend;", db)
products = pd.read_sql_query("select distinct product from s1fieldstatistic;", db)
acq_types = pd.read_sql_query("select distinct acquisition from s1fieldstatistic;", db)
parameter = pd.read_sql_query("select distinct polarization from s1fieldstatistic;", db)
stats = pd.read_sql_query("select distinct statistic from s1fieldstatistic;", db)
fid = pd.read_sql_query("select distinct fid from areaofinterest;", db)

# get single value selections from user
aoi_selection = st.sidebar.selectbox("Select AOI", aoi_names)
year_selection = st.sidebar.selectbox("Select Year", years)
crop_selection = st.sidebar.selectbox("Select Crop Type", crop_types)
stat_selection = st.sidebar.selectbox("Select Statistic", stats)

st.sidebar.markdown('#')
st.sidebar.header('Dependent Filters')

# get list of multiselections from user
acq_selection = tuple(st.sidebar.multiselect("Select Acquisition Mode", acq_types))
product_selection = tuple(st.sidebar.multiselect("Select Product", products))
param_selection = tuple(st.sidebar.multiselect("Select Parameter", parameter))
fid_selection = tuple(st.sidebar.multiselect("Select FID", fid))

# list of multiselections
dependent_selections = [acq_selection, product_selection, param_selection, fid_selection]


# function to add placeholder to multiselection tuple if len == 1 (prevents syntax error)


def placeholders(multiselections):
    if len(multiselections) == 1:
        multiselections = multiselections + ("placeholder",)
        return multiselections
    else:
        return multiselections


# apply placeholder function
acq_selection = placeholders(acq_selection)
param_selection = placeholders(param_selection)
product_selection = placeholders(product_selection)
fid_selection = placeholders(fid_selection)

# define sql body
sql = f"""SELECT 
    round(s1.value, 2) as value, 
    s1.mask_label, 
    s1.unit, 
    s1.aoi, 
    s1.datetime, 
    strftime('%Y-%m-%d', s1.datetime) as date,
    strftime('%H:%M:%S', s1.datetime) as time,
    s1.polarization as parameter, 
    s1.acquisition, 
    s1.product,
    area.fid, 
    area.year, 
    area.sl_nr, 
    area.crop_type_code, 
    area.crop_type,
    area.field_geom
    FROM s1fieldstatistic as s1
    INNER JOIN (SELECT 
    areaofinterest.fid, 
    areaofinterest.year, 
    areaofinterest.aoi,
    areaofinterest.sl_nr, 
    areaofinterest.crop_type_code, 
    crop.crop_type,
    areaofinterest.field_geom
    FROM areaofinterest
    INNER JOIN croplegend as crop 
    ON (crop.crop_type_code = areaofinterest.crop_type_code)) area
    ON (s1.mask_label = area.fid AND strftime('%Y', s1.datetime)=area.year AND s1.aoi = area.aoi)
    WHERE 
    s1.aoi="{aoi_selection}"
    AND area.crop_type="{crop_selection}"
    AND area.year="{year_selection}"
    AND s1.product IN {repr(product_selection)}
    AND s1.acquisition IN {repr(acq_selection)}
    AND s1.polarization IN {repr(param_selection)}
    AND area.fid IN {repr(fid_selection)}
    AND s1.statistic = "{stat_selection}"
    ORDER BY s1.mask_label, s1.datetime  ASC; """

# load table as df with sql query
records = pd.read_sql(sql, db)

# print warning if invalid filter combination (with no data) is selected
if records.empty and all(len(x) == 1 for x in dependent_selections):
    st.warning("No data is available with this filter combination. Please select other filter combinations")

# define expander box for time slider and trendline selection
expander = st.expander("Time and Trendline Filter")

# create sliders for time frame selection (start and end date of time series plots)
# convert datetime string column to datetime
records["datetime"] = pd.to_datetime(records["datetime"])
records["datetime"] = pd.to_datetime(records['datetime']).apply(lambda x: x.date())

# get earliest and latest date from df as boundaries for slider
start_date = records["datetime"].min()
end_date = records["datetime"].max()

# define slider values from user selection and filter df based on these values
try:
    expander.subheader("Select date range")
    slider_1, slider_2 = expander.slider('', value=(start_date, end_date), format="DD.MM.YY")
    records = records[(records['datetime'] > slider_1) & (records['datetime'] < slider_2)]
except KeyError:
    expander.warning("Please select values for each filter")

# get earliest and latest date again from now date-filtered df
start_date = records["datetime"].min()
end_date = records["datetime"].max()

# make button for selection of trend line type
expander.markdown("#")
expander.subheader("Please select statistic trendline for the graphs")
stat_button = expander.radio("", ("LOESS", "Rolling Mean"))
st.markdown("#")

# filter df by polarisation/value for different plots
vv_records = records[records["parameter"] == "VV"]
vh_records = records[records["parameter"] == "VH"]
ndvi_records = records[records["parameter"] == "NDVI"]

# set df column by which points are colored
selection = alt.selection_multi(fields=['acquisition'], bind='legend')

# set domain containing earliest and latest date of dataset, used as boundaries for x-axis of charts
domain_pd = pd.to_datetime([start_date, end_date]).astype(int) / 10 ** 6

# VV polarization charts
vv_chart = alt.Chart(vv_records).mark_circle().encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter', titleFontSize=22)),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="VV Polarization", width=1000, height=500)
vv_loess = alt.Chart(vv_records).encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter', titleFontSize=22))).transform_filter(selection).\
    transform_loess("datetime", "value").mark_line(color="black")
vv_mean = alt.Chart(vv_records).mark_line(color="black").transform_filter(selection).\
    transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

# VH polarization charts
vh_chart = alt.Chart(vh_records).mark_circle().encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter', titleFontSize=22)),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="VH Polarization", width=1000, height=500)
vh_loess = alt.Chart(vh_records).encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter', titleFontSize=22))).transform_filter(selection).\
    transform_loess("datetime", "value").mark_line(color="black")
vh_mean = alt.Chart(vh_records).mark_line(color="black").transform_filter(selection).\
    transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

# NDVI charts
ndvi_chart = alt.Chart(ndvi_records).mark_circle().encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='NDVI Value', titleFontSize=22)),
    color=alt.condition(selection, "acquisition", alt.value("lightgray")),
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))).add_selection(selection).\
    properties(title="NDVI", width=1000, height=500)
ndvi_loess = alt.Chart(ndvi_records).encode(
    x=alt.X("datetime:T", axis=alt.Axis(title='Date', titleFontSize=22), scale=alt.Scale(domain=list(domain_pd))),
    y=alt.Y("value", axis=alt.Axis(title='Backscatter', titleFontSize=22))).transform_filter(selection).\
    transform_loess("datetime", "value").mark_line(color="black")
ndvi_mean = alt.Chart(ndvi_records).mark_line(color="black").transform_filter(selection).\
    transform_window(rolling_mean="mean(value)", frame=[-5, 5]).encode(x='datetime:T', y='rolling_mean:Q')

# set trend line type in charts based on user selection
if stat_button == "LOESS":
    vv_chart = vv_chart + vv_loess
    vh_chart = vh_chart + vh_loess
    ndvi_chart = ndvi_chart + ndvi_loess

elif stat_button == "Rolling Mean":
    vv_chart = vv_chart + vv_mean
    vh_chart = vh_chart + vh_mean
    ndvi_chart = ndvi_chart + ndvi_mean

# define list of charts to be displayed, based on user selection and data availability
chart_list = []
if records["parameter"].str.contains("VV").any() and "VV" in param_selection:
    chart_list.append(vv_chart)
if records["parameter"].str.contains("VH").any() and "VH" in param_selection:
    chart_list.append(vh_chart)
if records["parameter"].str.contains("NDVI").any() and "NDVI" in param_selection:
    chart_list.append(ndvi_chart)

# display charts from list
for chart in chart_list:
    st.altair_chart(chart.configure_title(fontSize=28).configure_legend(titleFontSize=20, labelFontSize=18))

# print data source and contributors
st.markdown("#")
st.markdown("Data Source: ESA Copernicus-Data")
st.markdown("Contributors: Markus Adam, Laura Walder")

# close connection to db
cursor.close()
db.close()
