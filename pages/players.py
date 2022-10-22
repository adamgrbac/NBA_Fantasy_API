import dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback
import pandas as pd
import numpy as np

F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv")
    
dash.register_page(__name__)

def layout():

    F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
    D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
    D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
    D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv")
    
    return html.Div(
        children=[
            html.H1(children="NBA Fantasy Analytics",),
            html.P(
                children="Analyze NBA Player stats"
                " from up-to-date gamelogs"
                " for the 2022-23 season",
            ),
            dcc.Dropdown(
                id="team_dropdown",
                options=[
                    {"label": team, "value": team}
                    for team in np.sort(D_TEAM.TEAM_NAME)
                ],
                value="",
                clearable=True,
                className="dropdown"
            ),
            dash_table.DataTable(
                F_GAMELOGS.to_dict('records'),
                [{"name": i, "id": i} for i in F_GAMELOGS.columns],
                id='tbl'
            ),
        ]
    )

@callback(
    [Output("tbl","data")],
    [Input("team_dropdown","value")]
)
def update_data(team_name):
    if team_name == "" or team_name is None:
        D_TEAM_filtered = D_TEAM
    else:
        D_TEAM_filtered = D_TEAM.loc[D_TEAM.TEAM_NAME == team_name, :]
    
    F_GAMELOGS_filtered = pd.merge(F_GAMELOGS, D_TEAM_filtered, on="TEAM_ID", how="inner")
    
    return [F_GAMELOGS_filtered[F_GAMELOGS.columns].to_dict("records")]
