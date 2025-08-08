import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import io
import base64
import plotly.express as px
import plotly.graph_objects as go
import os

app = dash.Dash(__name__)
server = app.server

# Default file
DEFAULT_FILE = 'sample_trendlines.xlsx'

def load_default_data():
    if os.path.exists(DEFAULT_FILE):
        df = pd.read_excel(DEFAULT_FILE)
        return df
    return pd.DataFrame()

df = load_default_data()
measurement_options = [{'label': name, 'value': name} for name in set(col.split()[-1] for col in load_default_data().columns if col != 'time')]
historical_range_options = [{'label': 'Standard Deviation', 'value': 'Standard Deviation'}]

app.layout = html.Div([
    html.H2("Historical Range Calculation Tool", style={'textAlign': 'center'}),

    html.Div([
        # Left Column
        html.Div([
            dcc.Graph(id='data-plot', style={'height': '500px'})
        ], style={'width': '80%', 'padding': '10px'}),

        # Right Column
            html.Div([
            html.H4("Select a Measurement"),
            dcc.Dropdown(
                id='measurement-selector',
                options=measurement_options,
                value=None,
                placeholder="Select a Measurement"
            ),
            html.Div(id='columns-output'),
            html.H4("Select a Historical Range Calculation"),
            dcc.Dropdown(
                id='historical-range-selector',
                options=historical_range_options,
                value=None,
                placeholder="Select a Historical Range Calculation"
            )
        ], style={'width': '20%', 'padding': '10px'})
    ], style={'display': 'flex', 'flexDirection': 'row'}),
])

@app.callback(
    Output('columns-output', 'children'),
    Output('data-plot', 'figure'),
    Input('measurement-selector', 'value'),
    Input('historical-range-selector', 'value')
)
def update_graph_and_columns(selected_measurement, selected_range_calculation):
    if selected_measurement is None:
        return "No selection.", {}

    # Filter columns that end with the selected measurement
    matching_columns = [col for col in df.columns if col.endswith(selected_measurement)]

    # If no matching columns found, return empty graph
    if not matching_columns:
        return "No matching columns found.", {}

    # Melt df - not necessary because we're using just one measurement set but could be helpful in future
    melted_df = df[['time'] + matching_columns].melt(id_vars='time', var_name='Run', value_name='Value')

    fig = px.scatter(melted_df, x='time', y='Value', color='Run', title=f"{selected_measurement} Trends")

    if selected_range_calculation == "Standard Deviation":
        fig.add_trace(go.Scatter(x=df['time'], y=df['Run A Titer'], mode='lines', name='Historical Range: Standard Deviation'))

    return html.Ul([html.Li(col) for col in matching_columns]), fig

if __name__ == '__main__':
    app.run(debug=True)
