import dash
from dash import Dash, dash_table, dcc, html, Input, Output, callback
import pandas as pd
import numpy as np
from pathlib import Path

dash.register_page(__name__)

def layout():

    data_path = Path("./data/fantasy/")
    weeks = [week.name for week in data_path.iterdir()]
    max_week = max([week.split('_')[1] for week in weeks])

    results = pd.read_csv(f"./data/fantasy/week_{max_week}/1_Results.csv")
    cat_winners = pd.read_csv(f"./data/fantasy/week_{max_week}/2_Cat_Winners.csv")
    what_if_cats = pd.read_csv(f"./data/fantasy/week_{max_week}/3_WhatIf_Cats.csv")
    what_if_wl = pd.read_csv(f"./data/fantasy/week_{max_week}/4_WhatIf_WL.csv")
    mvp = pd.read_csv(f"./data/fantasy/week_{max_week}/MVP.csv")

    return html.Div(
        children=[
            html.H1(children="NBA Fantasy Stats",),
            html.P(
                children="Select Fantasy Week"
            ),
            dcc.Dropdown(
                id="week_dropdown",
                options=[
                    {"label": week, "value": week}
                    for week in weeks
                ],
                value=f"week_{max_week}",
                clearable=False,
                className="dropdown"
            ),
            html.Br(),
            html.Div(children=[
                html.H2(children="Results",),
                dash_table.DataTable(
                    results.to_dict('records'),
                    [{"name": i, "id": i} for i in results.columns],
                    id='tbl_results',
                    style_cell={
                        "textAlign": "center"
                    }           

                ),
            ],
            style={
                "width": "50%"
            }),
            html.Br(),
            html.Div(children=[
                html.H2(children="Cat Winners",),
                dash_table.DataTable(
                    cat_winners.to_dict('records'),
                    [{"name": i, "id": i} for i in cat_winners.columns],
                    id='tbl_cat_winners',
                    style_cell={
                        "textAlign": "center"
                    }
                )
            ],
            style={
                "width": "50%"
            }),
            html.Br(),
            html.Div(children=[
                html.H2(children="What If Win/Lose",),
                dash_table.DataTable(
                    what_if_wl.to_dict('records'),
                    [{"name": i, "id": i} for i in what_if_wl.columns],
                    id='tbl_what_if_wl',
                    tooltip_header={
                        col: col for col in what_if_cats.columns
                    },
                    style_header={
                        "overflow": "hidden",
                        "maxWidth": 50
                    },
                    style_cell={
                        "font-size": 10,
                        "textAlign": "center"
                    },
                    style_data_conditional=
                        [{
                            "if": {
                                "column_id": col,
                                "filter_query": f"{{{col}}} = 1"                            
                            },
                            "backgroundColor": "aquamarine",
                            "color": "darkgreen"
                        } for col in what_if_wl.columns if col not in ["team","score"]]+
                        [{
                            "if": {
                                "column_id": col,
                                "filter_query": f"{{{col}}} = 0"                            
                            },
                            "backgroundColor": "khaki",
                            "color": "goldenrod"
                        } for col in what_if_wl.columns if col not in ["team","score"]]+
                        [{
                            "if": {
                                "column_id": col,
                                "filter_query": f"{{{col}}} = -1"                            
                            },
                            "backgroundColor": "salmon",
                            "color": "firebrick"
                        } for col in what_if_wl.columns if col not in ["team","score"]]
                )
            ],
            style={
                "width": "50%"
            }),
            html.Br(),
            html.Div(children=[
                html.H2(children="What If Cats",),
                dash_table.DataTable(
                    what_if_cats.to_dict('records'),
                    [{"name": i, "id": i} for i in what_if_cats.columns],
                    id='tbl_what_if_cats',
                    tooltip_header={
                        col: col for col in what_if_cats.columns
                    },
                    style_header={
                        "overflow": "hidden",
                        "maxWidth": 50,
                    },
                    style_cell={
                        "font-size": 10,
                        "textAlign": "center"
                    }
                )
            ],
            style={
                "width": "50%",
            }),
            html.Br(),
            html.Div(children=[
                html.H2(children="Minimum Victory Path (MVP)",),
                dash_table.DataTable(
                    mvp.to_dict('records'),
                    [{"name": i, "id": i} for i in mvp.columns],
                    id='tbl_mvp',
                    style_header={
                        "overflow": "hidden",
                        "maxWidth": 50,
                    },
                    style_cell={
                        "textAlign": "center"
                    }
                )
            ],
            style={
                "width": "50%",
            }),
        ]
    )

@callback(
    [Output("tbl_results", "data"),
    Output("tbl_results", "columns"),
    Output("tbl_cat_winners", "data"),
    Output("tbl_cat_winners", "columns"),
    Output("tbl_what_if_cats", "data"),
    Output("tbl_what_if_cats", "columns"),
    Output("tbl_what_if_wl", "data"),
    Output("tbl_what_if_wl", "columns"),
    Output("tbl_mvp", "data"),
    Output("tbl_mvp", "columns"),
    Output("tbl_what_if_wl", "style_data_conditional")],
    [Input("week_dropdown", "value")]
)
def load_stats_week(week_num: str):
    results = pd.read_csv(f"./data/fantasy/{week_num}/1_Results.csv")
    cat_winners = pd.read_csv(f"./data/fantasy/{week_num}/2_Cat_Winners.csv")
    what_if_cats = pd.read_csv(f"./data/fantasy/{week_num}/3_WhatIf_Cats.csv")
    what_if_wl = pd.read_csv(f"./data/fantasy/{week_num}/4_WhatIf_WL.csv")
    mvp = pd.read_csv(f"./data/fantasy/{week_num}/MVP.csv")
    
    WIWL_style_cond = (
        [{
            "if": {
                "column_id": col,
                "filter_query": f"{{{col}}} = 1"                            
            },
            "backgroundColor": "aquamarine",
            "color": "darkgreen"
        } for col in what_if_wl.columns if col not in ["team","score"]]+
        [{
            "if": {
                "column_id": col,
                "filter_query": f"{{{col}}} = 0"                            
            },
            "backgroundColor": "khaki",
            "color": "goldenrod"
        } for col in what_if_wl.columns if col not in ["team","score"]]+
        [{
            "if": {
                "column_id": col,
                "filter_query": f"{{{col}}} = -1"                            
            },
            "backgroundColor": "salmon",
            "color": "firebrick"
        } for col in what_if_wl.columns if col not in ["team","score"]]
    )
    
    return (results.to_dict("records"),
            [{"name": i, "id": i} for i in results.columns],
            cat_winners.to_dict("records"),
            [{"name": i, "id": i} for i in cat_winners.columns],
            what_if_cats.to_dict("records"),
            [{"name": i, "id": i} for i in what_if_cats.columns],
            what_if_wl.to_dict("records"),
            [{"name": i, "id": i} for i in what_if_wl.columns],
            mvp.to_dict("records"),
            [{"name": i, "id": i} for i in mvp.columns],
            WIWL_style_cond)
            