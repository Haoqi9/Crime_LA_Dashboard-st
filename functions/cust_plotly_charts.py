import numpy as np
import plotly.express as px

########## Choropleth Map ##########
def plot_crime_area_map(
    gdf,
    width=1200,
    height=1000
):
    m = gdf.explore(
            column='perc_count',
            cmap='viridis_r',
            tiles='Cartodb Positron',
            tooltip=['PREC', 'area name', 'perc_count', 'count'],
            legend=True,
            tooltip_kwds={'aliases': ['Division code', 'Division name', 'prop_count (%)', 'count']},
            width=width,
            height=height
    )
    return m._repr_html_()

########## Time Series ##########
def plot_timeseries(
    df,
    width=1200,
    height=600,
    title='Crime Incidence in LA (2020-2024)'
):
    fig = px.line(
        data_frame=df,
        x='datetime occ',
        y='smoothed_count',
        hover_data={'count':True},
        template='plotly_white',
        # width=width,
        # height=height,
        title=title
    )

    fig.update_layout(
        title={
            'x': 0.5,  # Centered title
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig   

########## Heatmaps ##########
def plot_heatmap_monthly(
    df,
    width=1000,
    height=700,
    title='Monthly Crime Incidence by Year'
):
    month_orders = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    fig = px.density_heatmap(
        data_frame=df,
        x='year occ',
        y='month occ',
        z='count',
        color_continuous_scale='viridis_r',
        category_orders={'month occ': month_orders},
        template='plotly_white',
        title=title,
        width=width,
        height= height
    )

    fig.update_layout(
        title={
            'x': 0.5, 
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig  

def plot_heatmap_daily(
    df,
    width=1000,
    height=700,
    title='Daily Crime Incident by Month'
):
    day_orders = list(range(1, 31 + 1))

    fig = px.density_heatmap(
        data_frame=df,
        x='month occ',
        y='day occ',
        z='count',
        color_continuous_scale='viridis_r',
        category_orders={'day occ': day_orders},
        template='plotly_white',
        title=title,
        width=width,
        height=height
    )

    fig.update_layout(
        title={
            'x': 0.5,
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig

def plot_heatmap_weekday(
    df,
    width=1000,
    height=700,
    title='Week day Crime Incidence by week'
):
    weekday_orders = [
        'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'
    ]
    week_orders = [str(i) for i in range(1, 54)]

    fig = px.density_heatmap(
        data_frame=df,
        y='weekday occ',
        x='week occ',
        z='count',
        color_continuous_scale='viridis_r',
        category_orders={'weekday occ': weekday_orders, 'week occ': week_orders},
        template='plotly_white',
        title=title,
        width=width,
        height=height,
    )

    fig.update_layout(
        title={
            'x': 0.5,  
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig

def plot_heatmap_hourly(
    df,
    width=1000,
    height=700,
    title='Hourly Crime Incident by Day'
):
    hour_orders = list(range(0, 23 + 1))

    fig = px.density_heatmap(
        data_frame=df,
        y='hour occ',
        x='day occ',
        z='count',
        color_continuous_scale='viridis_r',
        category_orders={'hour occ': hour_orders},
        template='plotly_white',
        title=title,
        width=width,
        height=height,
    )

    fig.update_layout(
        title={
            'x': 0.5,
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig

########## Tree Maps ##########
def plot_tree_map(
    df,
    division='Los Angeles',
    width=1000,
    height=900,
    title='Crime Incidence by Type'
):
    if division != 'Los Angeles':
        path = ['area name', 'crm cd desc']
    else:
        path = [px.Constant("Los Angeles"), 'area name', 'crm cd desc']

    fig = px.treemap(
        data_frame=df,
        path=path,
        values='count',
        color='count',
        hover_data={'perc_count':True, 'count':False},
        color_continuous_scale='viridis_r',
        color_continuous_midpoint=np.median(df['count']),
        range_color=[
            df['count'].min(),
            df['count'].max()
        ],  
        width=width,
        height=height,
        title=title
    )

    fig.update_layout(
        title={
            'x': 0.5,
            'xanchor': 'center',  
            'yanchor': 'top', 
        }
    )
    return fig