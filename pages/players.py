import dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date, time

def datatable_column_def(cols):
    output = []
    for col in cols:
        if col in ["SEASON_YEAR","GAME_DATE","player_first_name","player_last_name","position","TEAM_NAME","WL","owner_name","ownership_type"]:
            output.append({"name": col, "id": col})
        elif "PCT" in col:
            output.append({"name": col, "id": col, "type": "numeric", "format": {"specifier": ".2%"}})
        else:
            output.append({"name": col, "id": col, "type": "numeric", "format": {"specifier": ".2f"}})
    return output

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

DISPLAY_AGG_COLUMNS = [
    "player_first_name",
    "player_last_name",
    "MIN",
    "FG_PCT",
    "FT_PCT",
    "FG3M",
    "PTS",
    "REB",
    "AST",
    "TOV",
    "STL",
    "BLK",
    "NBA_FANTASY_PTS"
]
    
F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv") 
    
dash.register_page(__name__)

def layout():
    global F_GAMELOGS
    global D_PLAYER
    global D_GAME
    global D_TEAM
    global DENORM
    
    F_GAMELOGS = pd.read_csv("./data/nba/F_GAMELOGS.csv")
    D_PLAYER = pd.read_csv("./data/nba/D_PLAYER.csv")
    D_GAME = pd.read_csv("./data/nba/D_GAME.csv")
    D_TEAM = pd.read_csv("./data/nba/D_TEAM.csv")
    
    DENORM = (F_GAMELOGS.merge(D_PLAYER, on="PLAYER_ID", how="inner", suffixes=["","_d"])
                        .merge(D_GAME, on="GAME_ID", how="inner", suffixes=["","_d"])
                        .merge(D_TEAM, on="TEAM_ID", how="inner", suffixes=["","_d"]))
                        
    DENORM = DENORM[DISPLAY_COLUMNS]
    
    PLAYER_AGG = (DENORM.groupby(["player_first_name", "player_last_name"])
                        .agg({"MIN": "mean",
                              "FGM": "sum",
                              "FGA": "sum",
                              "FTM": "sum",
                              "FTA": "sum",
                              "FG3M": "mean",
                              "PTS": "mean",
                              "REB": "mean",
                              "AST": "mean",
                              "STL": "mean",
                              "BLK": "mean",
                              "TOV": "mean",
                              "NBA_FANTASY_PTS": "mean"})
                        .reset_index())
                        
    PLAYER_AGG["FG_PCT"] = PLAYER_AGG.apply(lambda row: 0 if row["FGA"] == 0 else row["FGM"]/row["FGA"], axis=1)
    PLAYER_AGG["FT_PCT"] = PLAYER_AGG.apply(lambda row: 0 if row["FTA"] == 0 else row["FTM"]/row["FTA"], axis=1)
    
    PLAYER_AGG = PLAYER_AGG[DISPLAY_AGG_COLUMNS]
    
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
                html.H5(children="Gamelog Window (Last n Days)"),
                dcc.Dropdown(
                    id="window_dropdown",
                    options=[
                        {"label": i, "value": i}
                        for i in range(1,31)
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
                html.Div(children=[
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.FGM.agg('sum')/DENORM.FGA.agg('sum'):.2%}",
                            id="avg_fg"
                        ),
                        html.H6(
                            children="FG Percentage"
                        )
                    ],
                    style={"flex": 1}
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.FTM.agg('sum')/DENORM.FTA.agg('sum'):.2%}",
                            id="avg_ft"
                        ),
                        html.H6(
                            children="FT Percentage"
                        )
                    ],
                    style={"flex": 1}
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.FG3M.agg('mean'):.2f}",
                            id="avg_3pm"
                        ),
                        html.H6(
                            children="3PM per Game"
                        )
                    ],
                    style={"flex": 1}                
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.PTS.agg('mean'):.2f}",
                            id="avg_pts"
                        ),
                        html.H6(
                            children="PTS per Game"
                        )
                    ],
                    style={"flex": 1}
                    )                    
                ],
                style={"display": "flex", "text-align": "center"},
                id="agg_stats_row_1"),
                html.Div(children=[
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.REB.agg('mean'):.2f}",
                            id="avg_reb"
                        ),
                        html.H6(
                            children="REB per Game"
                        )
                    ],
                    style={"flex": 1}                
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.AST.agg('mean'):.2f}",
                            id="avg_ast"
                        ),
                        html.H6(
                            children="AST per Game"
                        )
                    ],
                    style={"flex": 1}                
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.STL.agg('mean'):.2f}",
                            id="avg_stl"
                        ),
                        html.H6(
                            children="STL per Game"
                        )
                    ],
                    style={"flex": 1}
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.BLK.agg('mean'):.2f}",
                            id="avg_blk"
                        ),
                        html.H6(
                            children="BLK per Game"
                        )
                    ],
                    style={"flex": 1}
                    ),
                    html.Div(children=[
                        html.H3(
                            children=f"{DENORM.TOV.agg('mean'):.2f}",
                            id="avg_tov"
                        ),
                        html.H6(
                            children="TOV per Game"
                        )
                    ],
                    style={"flex": 1}
                    )
                ],
                style={"display": "flex", "text-align": "center"},
                id="agg_stats_row_2"),
                html.Div(children=[
                    html.H5(
                        children="Player-level Average Stats"                    
                    ),
                    dash_table.DataTable(
                        PLAYER_AGG.to_dict('records'),
                        columns=datatable_column_def(DISPLAY_AGG_COLUMNS),
                        id='player_tbl',
                        style_cell={
                            "font-size": 10
                        },
                        page_size=20,
                    ),
                    html.H5(
                        children="Individual Gamelogs"                    
                    ),
                    dash_table.DataTable(
                        DENORM.to_dict('records'),
                        columns=datatable_column_def(DISPLAY_COLUMNS),
                        id='tbl',
                        style_cell={
                            "font-size": 10
                        },
                        page_size=20
                    )
                ])
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
    [Output("tbl", "data"),
    Output("player_tbl", "data"),
    Output("team_dropdown", "options"),
    Output("player_dropdown", "options"),
    Output("fantasy_team_dropdown", "options"),
    Output("avg_pts", "children"),
    Output("avg_reb", "children"),
    Output("avg_ast", "children"),
    Output("avg_fg", "children"),
    Output("avg_ft", "children"),
    Output("avg_3pm", "children"),
    Output("avg_stl", "children"),
    Output("avg_blk", "children"),
    Output("avg_tov", "children")],
    [Input("team_dropdown", "value"),
    Input("player_dropdown", "value"),
    Input("fantasy_team_dropdown", "value"),
    Input("window_dropdown", "value")]
)
def update_data(team_name, player_name, fantasy_team_name, window):
                       
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
        
    if window == "" or window is None:
        D_GAME_filtered = D_GAME
    else:
        D_GAME_filtered = D_GAME.loc[pd.to_datetime(D_GAME.GAME_DATE, format='%Y-%m-%dT%H:%M:%S') >= datetime.combine(date.today(), time()) - timedelta(days=window), :]
    
    DENORM_filtered = (F_GAMELOGS.merge(D_PLAYER_filtered, on="PLAYER_ID", how="inner", suffixes=["","_d"])
                                 .merge(D_GAME_filtered, on="GAME_ID", how="inner", suffixes=["","_d"])
                                 .merge(D_TEAM_filtered, on="TEAM_ID", how="inner", suffixes=["","_d"]))
                                 
    DENORM_filtered = DENORM_filtered[DISPLAY_COLUMNS]
    
    PLAYER_AGG = (DENORM_filtered.groupby(["player_first_name", "player_last_name"])
                                 .agg({"MIN": "mean",
                                       "FGM": "sum",
                                       "FGA": "sum",
                                       "FTM": "sum",
                                       "FTA": "sum",
                                       "FG3M": "mean",
                                       "PTS": "mean",
                                       "REB": "mean",
                                       "AST": "mean",
                                       "STL": "mean",
                                       "BLK": "mean",
                                       "TOV": "mean",
                                       "NBA_FANTASY_PTS": "mean"})
                                 .reset_index())
                                
    PLAYER_AGG["FG_PCT"] = PLAYER_AGG.apply(lambda row: 0 if row["FGA"] == 0 else row["FGM"]/row["FGA"], axis=1)
    PLAYER_AGG["FT_PCT"] = PLAYER_AGG.apply(lambda row: 0 if row["FTA"] == 0 else row["FTM"]/row["FTA"], axis=1)
                                 
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
            PLAYER_AGG[DISPLAY_AGG_COLUMNS].to_dict("records"),
            team_options,
            player_options,
            fantasy_team_options,
            f"{DENORM_filtered.PTS.agg('mean'):.2f}",
            f"{DENORM_filtered.REB.agg('mean'):.2f}",
            f"{DENORM_filtered.AST.agg('mean'):.2f}",
            f"{DENORM_filtered.FGM.agg('sum')/DENORM_filtered.FGA.agg('sum'):.2%}",
            f"{DENORM_filtered.FTM.agg('sum')/DENORM_filtered.FTA.agg('sum'):.2%}",
            f"{DENORM_filtered.FG3M.agg('mean'):.2f}",
            f"{DENORM_filtered.STL.agg('mean'):.2f}",
            f"{DENORM_filtered.BLK.agg('mean'):.2f}",
            f"{DENORM_filtered.TOV.agg('mean'):.2f}"]
