import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
from dateutil.relativedelta import relativedelta
from dash.dependencies import Input, Output , State
from utils import get_index_name
from formulas import priip_rts1 , priip_rts2
from datetime import date
import pandas as pd
import numpy as np


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

index_options = [{'label': 'SX5E', 'value': 'SX5E'},
                   {'label': 'SXXP', 'value': 'SXXP'},
                   {'label': 'SPX', 'value': 'SPX'},
               ]

df = pd.read_excel('data.xlsx',sheet_name='SXXP',parse_dates=True,index_col='date')
df['date_str'] = df.index
df['date_str'] = df['date_str'].apply(lambda x : pd.to_datetime(x).strftime('%Y-%m-%d'))

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date_str'],y=df['close']))

#fig = px.line(df, x="date_str", y="close", title=get_index_name('SXXP',index_options),labels={'date_str':'T','close':'Close'})

app.layout = html.Div([
    html.H1('Priips 2.0'),
    html.Div([
        html.Div([
            html.Div([
            html.H5('Select Index / Fund:')],style={'width':'80%'}),
            html.Div([
            dcc.Dropdown(
            id='drop_down_index',
            options=index_options,
            value='SXXP',
            optionHeight=20,
        )],style={'align':'left','height':50})],style={'columnCount': 2}),
        html.Div([
            html.H5('Select RHP Range (year)'),
            dcc.RangeSlider(
                id='rhp-slider',
                min=1,
                max=11,
                value=[1,5],
                marks={str(x): str(x) for x in np.arange(1,11,1)},
                step=1),
            ],style={'columnCount': 2})],style={'columnCount':1}),
    html.Div([html.Br(),
              html.Br(),
              html.Hr(),]),
    html.Div([
        html.Div([
        dcc.Checklist(
            id = 'priip_version',
            options=[
                {'label': 'Priips 1.0', 'value': 'V1'},
                {'label': 'Priips 2.0', 'value': 'V2'},
            ],
            value=['V1', 'V2']
        ),
        html.Button(id='submit-button-state', n_clicks=0, children='Calculate'),
    ],style={'columnCount':1}),
        html.Div([
        dcc.Checklist(
            id = 'scenario_list',
            options=[
                {'label': 'Favourable Scenario', 'value': 'fav'},
                {'label': 'Moderate Scenario', 'value': 'mod'},
                {'label': 'Unfavourable Scenario', 'value': 'unfav'},
                {'label': 'Stress Scenario', 'value': 'stress'},
            ],
            value=['mod']
        ),

    ],style={'columnCount': 1})],style={'columnCount':2}),
    html.Div([
        dcc.Graph(
            id='price_chart',
            figure=fig),
        html.Div([
        html.H5('Calculation Date:'),
        dcc.Input(
            id = 'date_picker',
            type='text',
            value='20200101',
        )
        ],style={'columnCount':2,'display': 'inline-block'})]),
])

@app.callback(
    Output('price_chart', 'figure'),
    Input('drop_down_index', 'value'),
    Input('submit-button-state', 'n_clicks'),
    State('scenario_list','value'),
    State('priip_version','value'),
    State('rhp-slider','value'),
    State('date_picker','value'))
def update_figure(selected_index,n_clicks,scenarios,priip_version,rhp_range,date_graph):
    print('scenarios',scenarios)
    print('priip_version',priip_version)
    print('rhp_range',rhp_range)
    print(date_graph)
    calcdate = pd.to_datetime(date_graph)

    # reading the data
    df = pd.read_excel('data.xlsx',sheet_name=selected_index,parse_dates=True,index_col='date')
    df['date_str'] = df.index
    df['date_str'] = df['date_str'].apply(lambda x : pd.to_datetime(x).strftime('%Y-%m-%d'))

    idx = df.index<=calcdate
    spot= df.loc[idx,'close'].values[-1]

    # calculate priips
    calc_rt1 = priip_rts1(df[['close']],rhp_range=np.arange(min(rhp_range),max(rhp_range)),horizon=2,calcdate=calcdate)
    calc_rt2 = priip_rts2(df[['close']],rhp_range=np.arange(min(rhp_range),max(rhp_range)),calcdate=calcdate)
    calc_rt1 = pd.DataFrame(calc_rt1)
    print(calc_rt1)
    calc_rt1['rhp'] = calc_rt1['rhp'].apply(lambda x: calcdate + relativedelta(years=x))
    calc_rt1['rhp_str'] = calc_rt1['rhp'].apply(lambda x : pd.to_datetime(x).strftime('%Y-%m-%d'))
    calc_rt1['mod'] = spot*(calc_rt1['mod']+1)
    calc_rt1['fav'] = spot*(calc_rt1['fav']+1)
    calc_rt1['unfav'] = spot*(calc_rt1['unfav']+1)

    calc_rt2 = pd.DataFrame(calc_rt2)
    calc_rt2['rhp'] = calc_rt2['rhp'].apply(lambda x: calcdate + relativedelta(years=x))
    calc_rt2['rhp_str'] = calc_rt2['rhp'].apply(lambda x : pd.to_datetime(x).strftime('%Y-%m-%d'))
    calc_rt2['mod'] = spot*(calc_rt2['mod']+1)
    calc_rt2['fav'] = spot*(calc_rt2['fav']+1)
    calc_rt2['unfav'] = spot*(calc_rt2['unfav']+1)

    #fig = px.line(df, x="date_str", y="close",
    #              title=get_index_name(selected_index,index_options),
    #              labels={'date_str':'T','close':'Close'})
    #fig.update_layout(transition_duration=500)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date_str'],
                            y=df['close'],
                            name=''))

    fig.add_trace(go.Scatter(x=calc_rt1['rhp_str'],
                            y=calc_rt1['mod'],
                            name='Moderate (1.0)'))
    fig.add_trace(go.Scatter(x=calc_rt1['rhp_str'],
                             y=calc_rt1['fav'],
                             name='Favourable (1.0)'))
    fig.add_trace(go.Scatter(x=calc_rt1['rhp_str'],
                             y=calc_rt1['unfav'],
                             name='Unfavourable (1.0)'))

    fig.add_trace(go.Scatter(x=calc_rt2['rhp_str'],
                             y=calc_rt2['mod'],
                             name='Moderate (2.0)'))
    fig.add_trace(go.Scatter(x=calc_rt2['rhp_str'],
                             y=calc_rt2['fav'],
                             name='Favourable (2.0)'))
    fig.add_trace(go.Scatter(x=calc_rt2['rhp_str'],
                             y=calc_rt2['unfav'],
                             name='Unfavourable (2.0)'))

    fig.update_layout(title=selected_index)

    return fig



if __name__ == '__main__':
    app.run_server(debug=True)