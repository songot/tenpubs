# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html

sys.path.insert(1, 'executium/python-sdk/src')
sys.path.insert(2, 'executium/python-sdk/examples')

# Include config and class
from config import key, secret
from Class import ApiAccess

def scrape_news(date):
    # Declare your key and secret
    obj = ApiAccess(key, secret)
    # Declare endpoint
    endpoint = 'public/trending-news-data'
    # Parameters required
    payload = {'date': date}
    result = obj.send(endpoint, payload, dict())
    returned_data = result['returned']['data']
    return returned_data

def create_basedf(returned_data):
    # Create column names for data frame and insert them into head list
    head = ['id', 'source']
    chunk = returned_data[0]['price_impact_3600s']['data']
    pair_keys = list(chunk.keys())
    price_keys = list(chunk['btcusdt'].keys())[2:]
    for pa in pair_keys:
        for pr in price_keys:
            head.append(pa+pr)
    # Create dictionary for extracted data
    frame = dict()
    # Extract ids of articles
    frame['id'] = np.array([])
    for d in returned_data:
        # Some price impact data is missed
        if type(d['price_impact_3600s']['data']) == dict:
            frame['id'] = np.append(frame['id'], d['id'])
    # Extract sources of articles
    frame['source'] = np.array([])
    for d in returned_data:
        # Some price impact data is missed
        chunk = d['price_impact_3600s']['data']
        if type(chunk) == dict:
            frame['source'] = np.append(frame['source'], d['source'])
    # Extract hour price impact of articles
    for pa in pair_keys:
        for pr in price_keys:
            papr = pa+pr
            frame[papr] = np.array([])
            for d in returned_data:
                # Some price impact data is missed
                chunk = d['price_impact_3600s']['data']
                if type(chunk) == dict:
                    if 'before' in chunk[pa].keys():
                        val = float(chunk[pa][pr])
                        frame[papr] = np.append(frame[papr], val)
                    else:
                        # Fill missed data with null values 
                        # to get the same lengths for each 
                        # column
                        frame[papr] = np.append(frame[papr], None)
    # Create pandas DataFrame
    df = pd.DataFrame(frame, columns = head)
    # Drop rows containing any null value
    df.dropna(axis=0, inplace=True)
    # Reset index of data frame after drop
    df.reset_index(drop=True, inplace=True)
    # Set dtype float64 for all columns except id and source
    df2 = df.iloc[:, 2:].astype(float, copy=False)
    df.iloc[:, 2:] = df2
    # Set parameters for price impact calculations
    prics = len(head) - 2
    ipair = 0
    lochead = ['id', 'source']
    # Calculate price impact percentage for each available pair
    for i in range(2,prics,3):
        idf = df.iloc[:, i:i+3]
        impactname = pair_keys[ipair]+'priceimpact'
        diffname = pair_keys[ipair]+'difference'
        # Function for price impact
        df[impactname] = 100*abs(idf.iloc[:,2])/idf.iloc[:,0]
        lochead.append(diffname)
        lochead.append(impactname)
        ipair+=1
    # Form new data frame with price impact columns
    basedf = df.loc[:,lochead]
    return basedf

def return_core(basedf, pair):
    # Group data by publications, aggregate articles' ids, price difference
    # and impact related to chosen pair, then sort publications by their 
    # impact on price in descending order
    core = basedf.groupby('source', sort=False)
    core = core.agg({'id':'count', pair + 'difference':'mean',\
                     pair + 'priceimpact':'mean'})
    core = core.sort_values(by=pair+'priceimpact', ascending=False)
    # Present source as column, then change columns' names
    core.reset_index(inplace=True)
    core.columns = ['Publication', 'Number of articles',\
                    'Change', 'Price Impact, %']
    return core

def pub_chart(core):
    # Choose top 10 influential publications
    diamond = core[0:10]
    diamond = diamond.sort_values(by='Price Impact, %', ascending=True)
    diamond.reset_index(drop=True,inplace=True)
    # Create chart with mined data
    figChart = go.Figure(
        data=[go.Scatter(
            x=diamond['Publication'], y=diamond['Price Impact, %'],
            mode='markers+text', marker=dict(
                colorscale=['rgba(255, 83, 73, 0.8)',\
                            'rgba(0, 204, 102, 0.8)'],
                color=diamond['Change'],
                size=42+4.2*diamond['Number of articles'], showscale=True,
                colorbar=dict(title="Change")),
            text=diamond['Number of articles'])],
        layout=go.Layout(
            xaxis=dict(showgrid=True), yaxis=dict(
                title_text="Price Impact, %", showgrid=True)))
    figChart.add_annotation(
        x=9, y=diamond['Price Impact, %'][9], xref="x", yref="y",
        text="Number<br>of<br>articles", showarrow=True,
        font=dict(
                family="Arial",
                size=14,
                color="black"),
        align="center", arrowhead=3, arrowsize=1, arrowwidth=0.5,
        arrowcolor="black", ax=20, ay=70, bordercolor="black",\
        borderwidth=0.5, borderpad=4, bgcolor="#fffffe", opacity=0.8)
    figChart.update_layout(
        title='Top 10 publications impacted on price',
        font={'family':'Arial','size':14}, autosize=True)
    return figChart

def pub_list(core):
    tab = core[0:10]
    figList = go.Figure(
        data=[go.Table(
            header=dict(
                values=tab.columns, line_color='darkslategray',
                fill_color='rgba(220, 224, 222, 0.8)', align='center'),
            cells=dict(
                values=[tab['Publication'], tab['Number of articles'],
                    round(tab['Change'],8), 
                    round(tab['Price Impact, %'],2)],
                line_color='lightgrey',
                fill_color='rgba(255, 255, 255, 0.8)',
                align='center'))],
        layout=go.Layout(
            title='List of publications',
            font={'family':'Arial','size':14}, autosize=True))
    return figList

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# assume you have a "wide-form" data frame with no index
# see https://plotly.com/python/wide-form/ for more options
app.layout = html.Div(children=[
    html.H1(children='Trending news project'), 
    html.Div(children='''Choose date and currency'''),
    dcc.DatePickerSingle(
        id='my-date-picker-single',
        date = '2020-07-04'),
    dcc.Dropdown(
        id='pair-dropdown',
        options=[
            {'label': 'BTCUSD', 'value': 'btcusdt'},
            {'label': 'ETHUSD', 'value': 'ethusdt'},
            {'label': 'ADAUSD', 'value': 'adausdt'},
            {'label': 'XRPUSD', 'value': 'xrpusdt'},
            {'label': 'ETHBTC', 'value': 'ethbtc'},
            {'label': 'ADABTC', 'value': 'adabtc'},
            {'label': 'XRPBTC', 'value': 'xrpbtc'}],
        value='btcusdt'),
    dcc.Graph(id='example-graph'),
    dcc.Graph(id='example-list')])

def run_dash():
    app.run_server(debug=True)

@app.callback(
    [dash.dependencies.Output('example-graph', 'figure'),
     dash.dependencies.Output('example-list', 'figure')],
    [dash.dependencies.Input('my-date-picker-single', 'date'),
     dash.dependencies.Input('pair-dropdown', 'value')])
def update_data(date, value):
    returned_data = scrape_news(date)
    basedf = create_basedf(returned_data)
    pair = value
    core = return_core(basedf, pair)
    return [pub_chart(core), pub_list(core)]

if __name__ == '__main__':
    run_dash()
