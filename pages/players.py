import dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback
import pandas as pd
import numpy as np

DISPLAY_COLUMNS = [
    "SEASON_YEAR",
    "GAME_DATE",
    "player_first_name",
    "player_last_name",
    "position",
    "TEAM_NAME",
    "WL",
    "MIN",
    "PTS",
    "FGM",
    "FGA",
    "FG_PCT",
    "FG3M",
    "FG3A",
    "FG3_PCT",
    "FTM",
    "FTA",
    "FT_PCT",
    "OREB",
    "DREB",
    "REB",
    "AST",
    "TOV",
    "STL",
    "BLK",
    "BLKA",
    "PF",
    "PFD",
    "PLUS_MINUS",
    "NBA_FANTASY_PTS",
    "owner_name",
    "ownership_type"
]

F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv")

DENORM = (F_GAMELOGS.merge(D_PLAYER, on="PLAYER_ID", how="inner", suffixes=["","_d"])
                    .merge(D_GAME, on="GAME_ID", how="inner", suffixes=["","_d"])
                    .merge(D_TEAM, on="TEAM_ID", how="inner", suffixes=["","_d"]))
                    
DENORM = DENORM[DISPLAY_COLUMNS]
    
dash.register_page(__name__)

def layout():

    F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
    D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
    D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
    D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv")
    
    DENORM = (F_GAMELOGS.merge(D_PLAYER, on="PLAYER_ID", how="inner", suffixes=["","_d"])
                        .merge(D_GAME, on="GAME_ID", how="inner", suffixes=["","_d"])
                        .merge(D_TEAM, on="TEAM_ID", how="inner", suffixes=["","_d"]))
                        
    DENORM = DENORM[DISPLAY_COLUMNS]
    
    return html.Div(
        children=[
            html.Div(children=[
                html.H1(children="NBA Fantasy Analytics"),
                html.P(
                    children="Analyze NBA Player stats"
                    " from up-to-date gamelogs"
                    " for the 2022-23 season"
                )
            ],
            id="header_div"),
            html.Div(children=[
                html.H2(children="Filters"),
                html.H5(children="NBA Team"),
                dcc.Dropdown(
                    id="team_dropdown",
                    options=[
                        {"label": team, "value": team}
                        for team in np.sort(DENORM.TEAM_NAME.unique())
                    ],
                    value="",
                    clearable=True,
                    className="dropdown"
                ),
                html.H5(children="Fantasy Team"),
                dcc.Dropdown(
                    id="fantasy_team_dropdown",
                    options=[
                        {"label": team, "value": team}
                        for team in np.sort(DENORM.apply(lambda row: row["ownership_type"] if pd.isnull(row["owner_name"]) else row["owner_name"], axis=1).unique())
                    ],
                    value="",
                    clearable=True,
                    className="dropdown"
                ),
                html.H5(children="Player"),
                dcc.Dropdown(
                    id="player_dropdown",
                    options=[
                        {"label": player_name, "value": player_name}
                        for player_name in np.sort(DENORM.apply(lambda row: f"{row.player_first_name} {row.player_last_name}",axis=1).unique())
                    ],
                    value="",
                    clearable=True,
                    className="dropdown"
                ),
            ],
            id="filter_div",
            style={
                "position": "absolute",
                "width": "25%",
                "padding": "10px 10px"
            }),
            html.Div(children=[
                dash_table.DataTable(
                    DENORM.to_dict('records'),
                    [{"name": i, "id": i} for i in DENORM.columns],
                    id='tbl',
                    style_cell={
                        "font-size": 10
                    }
                )
            ],
            id="gamelog_tbl",
            style={
                "margin-left": "25%",
                "margin-right": "0%",
                "padding": "10px 10px"
            })            
        ]
    )

@callback(
    [Output("tbl","data"),
    Output("team_dropdown","options"),
    Output("player_dropdown","options"),
    Output("fantasy_team_dropdown","options")],
    [Input("team_dropdown","value"),
    Input("player_dropdown","value"),
    Input("fantasy_team_dropdown","value")]
)
def update_data(team_name, player_name, fantasy_team_name):

    print(team_name, player_name, fantasy_team_name)
                       
    if team_name == "" or team_name is None:
        D_TEAM_filtered = D_TEAM
    else:
        D_TEAM_filtered = D_TEAM.loc[D_TEAM.TEAM_NAME == team_name, :]
        
    if player_name == "" or player_name is None:
        D_PLAYER_filtered = D_PLAYER
    else:
        D_PLAYER_filtered = D_PLAYER.loc[D_PLAYER.apply(lambda row: f"{row.player_first_name} {row.player_last_name}",axis=1) == player_name, :]

    if fantasy_team_name == "" or fantasy_team_name is None:
        D_PLAYER_filtered = D_PLAYER_filtered
    elif fantasy_team_name in ("freeagents", "waivers"):
        D_PLAYER_filtered = D_PLAYER_filtered.loc[D_PLAYER_filtered.ownership_type == fantasy_team_name, :]
    else:
        D_PLAYER_filtered = D_PLAYER_filtered.loc[D_PLAYER_filtered.owner_name == fantasy_team_name, :]
    
    DENORM_filtered = (F_GAMELOGS.merge(D_PLAYER_filtered, on="PLAYER_ID", how="inner", suffixes=["","_d"])
                                 .merge(D_GAME, on="GAME_ID", how="inner", suffixes=["","_d"])
                                 .merge(D_TEAM_filtered, on="TEAM_ID", how="inner", suffixes=["","_d"]))
                                 
    DENORM_filtered = DENORM_filtered[DISPLAY_COLUMNS]
                                 
    team_options = [
        {"label": team, "value": team}
        for team in np.sort(DENORM_filtered.TEAM_NAME.unique())
    ]
    
    player_options = [
        {"label": player_name, "value": player_name}
        for player_name in np.sort(DENORM_filtered.apply(lambda row: f"{row.player_first_name} {row.player_last_name}",axis=1).unique())
    ]
    
    fantasy_team_options = [
        {"label": team, "value": team}
        for team in np.sort(DENORM_filtered.apply(lambda row: row["ownership_type"] if pd.isnull(row["owner_name"]) else row["owner_name"],axis=1).unique())
    ]
    
    return [DENORM_filtered[DENORM_filtered.columns].to_dict("records"),
            team_options,
            player_options,
            fantasy_team_options]
