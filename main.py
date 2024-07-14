import datetime as dt
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
from functions.cust_plotly_charts import (plot_crime_area_map,
                                          plot_timeseries,
                                          plot_heatmap_monthly,
                                          plot_heatmap_daily,
                                          plot_heatmap_weekday,
                                          plot_heatmap_hourly,
                                          plot_tree_map)

###############################################################################################################################

# PAGE CONFIGURATION
# (should always be the first thing to be called)

st.set_page_config(
    page_title='LA crime dashboard',
    # page_icon=None,
    layout='wide',
    initial_sidebar_state='auto'
)

###############################################################################################################################

# LOADING DATA

@st.cache_data
def get_dfs():
    df = pd.read_parquet('./data/crime_df_prep.parquet')
        
    LAPDD_map = gpd.read_file('./data/LAPD_Division_5473900632728154452.geojson')
    LAPDD_map['APREC'] = LAPDD_map['APREC'].str.title().replace(
        to_replace=['77Th Street', 'North Hollywood', 'West Los Angeles'],
        value=['77th Street', 'N Hollywood', 'West LA']
    )
    
    return (df, LAPDD_map)

def get_merged_geopandas_df(
    df,
    df_geometry,
    date_min='2020-01-01',
    date_max='2024-06-24',
    age_min=0,
    age_max=120,
    type_list=None,
    place_list=None,
    vict_sex_list=None,
    vict_ethn_list=None,
):
    
    if (date_min != '2020-01-01') or (date_max != '2024-06-24'):
        # Converto to timeseries df.
        df = df.set_index(['datetime occ']).sort_index()
        # Convert back to normal df.
        df = df.loc[date_min : date_max].reset_index()
    
    if (len(type_list) > 1) or (type_list[0] != 'All'):
        mask_type = df['crm cd desc'].isin(type_list)
    else:
        mask_type  = pd.Series([True] * df.shape[0])

    if (len(place_list) > 1) or (place_list[0] != 'All'):
        mask_place = df['premis desc'].isin(place_list)
    else:
        mask_place = pd.Series([True] * df.shape[0])

    if (len(vict_sex_list) > 1) or (vict_sex_list[0] != 'All'):
        mask_sex = df['vict sex'].isin(vict_sex_list)
    else:
        mask_sex = pd.Series([True] * df.shape[0])

    if (len(vict_ethn_list) > 1) or (vict_ethn_list[0] != 'All'):
        mask_ethn = df['vict descent'].isin(vict_ethn_list)
    else:
        mask_ethn = pd.Series([True] * df.shape[0])
        
    if (age_min != 0) or (age_max != 120):
        mask_age_range = df['vict age'].between(age_min, age_max)
    else:
        mask_age_range = pd.Series([True] * df.shape[0])

    df_filtered = df[mask_type & mask_place & mask_sex & mask_ethn & mask_age_range]
    
    crime_area = df_filtered.groupby('area name')\
                            .size()\
                            .reset_index(name='count')
    
    crime_area['perc_count'] = crime_area['count'].transform(lambda x: np.round((x / x.sum()) * 100, 2))

    divison_no_data = list(set(df['area name'].unique()) - set(crime_area['area name'].unique()))
    if len(divison_no_data) > 0:
        df_divison_no_data = pd.DataFrame(columns=crime_area.columns)
        for i, divison in enumerate(divison_no_data):
            df_divison_no_data.loc[i] = [divison, 0, 0.]
        df_all_divison = pd.concat([crime_area, df_divison_no_data], axis=0).reset_index(drop=True)
        df_final = df_all_divison
    else:
        df_final = crime_area

    # Convert to geopandas df.
    gdf = gpd.GeoDataFrame(
        data=df_final.merge(df_geometry, left_on='area name', right_on='APREC').sort_values('PREC'),
        geometry='geometry'
    )
    return (df_filtered, gdf)

df, LAPDD_map = get_dfs()

###############################################################################################################################

# SIDDEBAR WIDGETS

with st.sidebar:
    st.caption("""
    - Author: Hao Qi
    - GitHub: https://github.com/Haoqi9
    """)
    # Info section.
    st.write("<h1 style='text-align: center;'>Information</h1>", unsafe_allow_html=True)
    st.write("""
    This dashboard contains **3 tabs**:
    - 🌐 **LA map**. Displays the relative crime incidence for each of the 21 geographical divisions in Los Angeles. Hover over the map to see the absolute count data.
    
    - 🔍 **LAPD Division analysis**. Displays a detailed analysis for all or individual geographical divisions: evolution over time, seasonality, and crime type breakdown.
    
    - 📊 **Data**. Displays the filtered datafrane/table.
    """)
    
    ########## INPUT WIDGETS 1 ##########
    # Place input widgets in a form.
    with st.form('input form'):
        # Subtitle.
        st.write("<h1 style='text-align: center;'>Filters</h1>", unsafe_allow_html=True)
        # User helper info.
        st.write("""
        Note for **multiple selection box**:
        - Options for each input variable are listed **from the most to the least crime incidence**.
        - Choose only '**All**' to select all options for an input variable.
        - No input selection box shoud be empty.
        """)

        date_range = st.slider(
            label=':green-background[**Select date interval:**]',
            min_value=dt.date(2020, 1, 1),
            max_value=dt.date(2024, 6, 24),
            value=(dt.date(2020, 1, 1), dt.date(2024, 6, 24))
        )
        type_list = st.multiselect(
            label=':green-background[**Choose crime(s):**]',
            placeholder='Choose option(s) - Default is All',
            options=['All'] + list(df['crm cd desc'].value_counts().index),
            default='All',
            help=f"Total options: {df['crm cd desc'].nunique()}."
        )
        place_list = st.multiselect(
            label=':green-background[**Choose crime location(s):**]',
            placeholder='Choose option(s) - Default is All',
            options=['All'] + list(df['premis desc'].value_counts().index),
            default='All',
            help=f"Total options: {df['premis desc'].nunique()}."
        )
        vict_sex_list = st.multiselect(
            label=':green-background[**Choose victim sex(s):**]',
            placeholder='Choose option(s) - Default is All',
            options=['All'] + list(df['vict sex'].value_counts().index),
            default='All',
            help=f"Total options: {df['vict sex'].nunique()}."
        )
        vict_ethn_list = st.multiselect(
            label=':green-background[**Choose victim ethnicity(s):**]',
            placeholder='Choose option(s) - Default is All',
            options=['All'] + list(df['vict descent'].value_counts().index),
            default='All',
            help=f"Total options: {df['vict descent'].nunique()}."
        )
        vict_age = st.slider(
            label=':green-background[**Select victim age interval:**]',
            min_value=0,
            max_value=120,
            value=(0, 120)
        )
        
        st.write('')
        
        submitted = st.form_submit_button()

###############################################################################################################################

# BODY

# Title
st.markdown(
    "<h1 style='text-align: center;'>Crime Incidence in Los Angeles</h1>"
    "<h3 style='text-align: center;'><b><a href='https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8/about_data' target='_blank'>Data</a> from January 2020 to June 24, 2024</b></h3>",
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["🌐 LA map", "🔍 LAPD Division analysis", "📊 Data"])
with tab1:
    ######### INTERNAL CALCULATIONS 1 ##########
    df_filtered, gdf = get_merged_geopandas_df(
        df=df,
        df_geometry=LAPDD_map,
        date_min=date_range[0],
        date_max=date_range[1],
        age_min=vict_age[0],
        age_max=vict_age[1],
        type_list=type_list,
        place_list=place_list,
        vict_sex_list=vict_sex_list,
        vict_ethn_list=vict_ethn_list,
    )

    ######### PLOTING 2 ##########
    map_html = plot_crime_area_map(gdf)
    
    # plot title.
    st.write('')
    st.write("<h3 style='text-align: center;'>Relative Crime Incidence by LA Police Department Divisions (LAPDD)</h3>", unsafe_allow_html=True)
    html(map_html, width=1800, height=1000)

with tab2:
    ########## INPUT WIDGETS 2  ##########
    division = st.selectbox(
        label='Select a LAPD Division:',
        placeholder='Choose option(s) - Default is Los Angeles',
        help='LAPD Division stands for **Los Angeles Police Department Division**. The LAPD is organized into various divisions, each responsible for a specific geographic area or specialized function within the city of Los Angeles.',
        options=['Los Angeles'] + df_filtered['area name'].unique().tolist(),
        index=0
    )
    
    ######### INTERNAL CALCULATIONS 2 ##########
    if division != 'Los Angeles':
        mask_division = df_filtered['area name'] == division
        df_filtered = df_filtered.loc[mask_division]
        
    # Time series:
    crime_by_day = df_filtered.set_index('datetime occ')\
                              .resample('D')\
                              .size()\
                              .reset_index(name='count')

    crime_by_day['smoothed_count'] = crime_by_day['count'].rolling(window=7).mean()

    # Heat maps:
    crime_count_datetime = df_filtered.groupby(['year occ', 'month occ', 'week occ',
                                                'day occ', 'weekday occ', 'hour occ'])\
                                      .size()\
                                      .reset_index(name='count')

    month_mapping = {
        '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun',
        '7': 'Jul', '8': 'Aug', '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
    }

    weekday_mapping = {
        '1': 'Mon', '2': 'Tue', '3': 'Wed',
        '4': 'Thu', '5': 'Fri', '6': 'Sat', '7': 'Sun',
    }

    crime_count_datetime[['year occ', 'month occ', 'week occ', 'day occ', 'weekday occ', 'hour occ']] = crime_count_datetime[['year occ', 'month occ', 'week occ', 'day occ', 'weekday occ', 'hour occ']].astype('str')
    crime_count_datetime['month occ'] = crime_count_datetime['month occ'].map(month_mapping)
    crime_count_datetime['weekday occ'] = crime_count_datetime['weekday occ'].map(weekday_mapping)

    # Tree maps:
    crimen_area_tipo = df_filtered.groupby(['area name', 'crm cd desc'])\
                                  .size()\
                                  .reset_index(name='count')

    crimen_area_tipo['perc_count'] = crimen_area_tipo.groupby('area name')\
                                                    ['count']\
                                                    .transform(lambda x: np.round((x / x.sum() * 100), 2))
    
    ######### PLOTING 2 ##########
    timeseries_crime = plot_timeseries(
        df=crime_by_day,
        title=f'Crime Incidence in {division} ({date_range[0].year}-{date_range[1].year})'
    )

    heatmap_crime_monthly = plot_heatmap_monthly(crime_count_datetime)
    heatmap_crime_daily   = plot_heatmap_daily(crime_count_datetime)
    heatmap_crime_weekday = plot_heatmap_weekday(crime_count_datetime)
    heatmap_crime_hourly  = plot_heatmap_hourly(crime_count_datetime)

    treemap_crime = plot_tree_map(
        df=crimen_area_tipo,
        division=division
    )
    
    st.plotly_chart(timeseries_crime, use_container_width=True)
    st.write('___')
    
    col1, col2 = st.columns(2)
    col1.plotly_chart(heatmap_crime_monthly, use_container_width=True)
    col2.plotly_chart(heatmap_crime_daily, use_container_width=True)

    col3, col4 = st.columns(2)
    col3.plotly_chart(heatmap_crime_weekday, use_container_width=True)
    col4.plotly_chart(heatmap_crime_hourly, use_container_width=True)
    st.write('___')

    st.plotly_chart(treemap_crime, use_container_width=True)

with tab3:
    st.write(f"This Dataframe (table) contains **{df_filtered.shape[0]}** rows and **{df_filtered.shape[1]} columns**.")
    st.write(df_filtered)