import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/5d1ea79569ed194d432e56108a04d188/raw/a9f9e8076b837d541398e999dcbac2b2826a81f8/gdp-life-exp-2007.csv')

fig = px.scatter(df, x="gdp per capita", y="life expectancy",
                 size="population", color="continent", hover_name="country",
                 log_x=True, size_max=60)

app.layout = html.Div([
    html.Label('Select Index / Fund'),
    dcc.Dropdown(
        id='drop_down_index',
        options=[
            {'label': 'Dow Jones Euro Stoxx 50', 'value': 'SX5E'},
            {'label': 'Dow Jones Euro Stoxx 600', 'value': 'SXXP'},
            {'label': 'S&P 500', 'value': 'SPX'},
        ],
        value='SXXP'
    ),
    dcc.Graph(
        id='price_chart',
        figure=fig
    )
])

@app.callback(
    Output('price_chart', 'figure'),
    Input('drop_down_index', 'value'))
def update_figure(selected_index):
    df = pd.read_excel('data.xlsx',sheet_name=selected_index,parse_dates=True,index_col='date')
    print(df.head())
    df['date_str'] = df.index
    df['date_str'] = df['date_str'].apply(lambda x : pd.to_datetime(x).strftime('%Y-%m-%d'))
    print(df.head())
    fig = px.line(df, x="date_str", y="close",
                  title=selected_index,
                  labels={'date_str':'T','close':'Close'})
    fig.update_layout(transition_duration=500)
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)