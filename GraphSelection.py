import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import io
import base64
import plotly.express as px
import os

app = dash.Dash(__name__)
server = app.server

# Default file
DEFAULT_FILE = 'sample_measurements.xlsx'

def load_default_data():
    if os.path.exists(DEFAULT_FILE):
        df = pd.read_excel(DEFAULT_FILE)
        return df
    return pd.DataFrame()

app.layout = html.Div([
    html.H2("Excel Plot & Export Tool", style={'textAlign': 'center'}),

    html.Div([
        # Left Column
        html.Div([
            dcc.Graph(id='data-plot', style={'height': '500px'})
        ], style={'width': '50%', 'padding': '10px'}),

        # Right Column
            html.Div([
                dcc.Upload(
            id='upload-data',
            children=html.Div(('Select Excel File')),
            style={
                'width': '90%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '10px auto'
            },
            multiple=False
            ),
            html.H4("Data Preview"),
            dash_table.DataTable(
                id='data-table',
                style_table={
                    'height': '500px',
                    'overflowY': 'scroll',
                    'overflowX': 'auto',
                    #'border': '1px solid #ccc'
                },
                style_cell={'textAlign': 'left'},
                style_data_conditional=[], #This highlights selected data
            ),
            html.Br(),
            html.Button("Download Selected Data", id="download-btn", n_clicks=0),
            dcc.Download(id="download-selected"),
        ], style={'width': '50%', 'padding': '10px'})
    ], style={'display': 'flex', 'flexDirection': 'row'}),

    dcc.Store(id='stored-data'),
    dcc.Store(id='selected-data')
])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))
            return df
        else:
            return None
    except Exception as e:
        print("Error reading file:", e)
        return None

@app.callback(
    Output('stored-data', 'data'),
    Output('data-plot', 'figure'),
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Output('download-btn', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=False
)
def update_output(contents, filename):
    # Load from upload or use default
    if contents:
        df = parse_contents(contents, filename)
    else:
        df = load_default_data()

    if df is None or df.empty or len(df.columns) < 2:
        fig = px.scatter(title="Invalid or empty Excel file.")
        return None, fig, [], [], {'display': 'none'}

    #fig = px.scatter(df, x=df.columns[0], y=df.columns[1], title="Select data by dragging a box")
    fig = px.scatter(df, x=df.columns[0], y=df.columns[1:], title="Select data by dragging a box")
    fig.update_layout(dragmode='select', legend_title_text='trend')

    columns = [{"name": col, "id": col} for col in df.columns]
    return df.to_dict('records'), fig, columns, df.to_dict('records'), {'display': 'block', 'margin': '10px auto'}

@app.callback(
    Output('selected-data', 'data'),
    Output('data-table', 'style_data_conditional'),
    Input('data-plot', 'selectedData'),
    State('stored-data', 'data'),
)
def highlight_selected(selectedData, all_data):
    if not selectedData or not all_data:
        return None, []

    df = pd.DataFrame(all_data)
    selected_indices = [point['pointIndex'] for point in selectedData['points']]
    selected_df = df.iloc[selected_indices]

    highlight = [{
        'if': {'row_index': i},
        'backgroundColor': '#D2F3FF',
        'fontWeight': 'bold'
    } for i in selected_indices]

    return selected_df.to_dict('records'), highlight

@app.callback(
    Output('download-selected', 'data'),
    Input('download-btn', 'n_clicks'),
    State('selected-data', 'data'),
    prevent_initial_call=True
)
def download_selected(n_clicks, selected_data):
    if not selected_data:
        return dash.no_update

    df = pd.DataFrame(selected_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Selected Data')
    output.seek(0)

    return dcc.send_bytes(output.read(), filename="selected_data.xlsx")

if __name__ == '__main__':
    app.run(debug=True)
