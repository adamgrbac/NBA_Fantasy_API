import dash
from dash import Dash, dash_table, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div(
    children=[
        html.Div([
            dbc.Nav([
                dbc.NavLink(
                    f"{page['name']}", href=page["relative_path"]
                ) for i, page in enumerate(dash.page_registry.values())# if page["name"] != "Players"
            ]) 
        ]),
        html.Div([
            dash.page_container
        ])
    ]
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=True)
