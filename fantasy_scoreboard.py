from Authenticator import Authenticator
from FantasyAPI import FantasyAPI
from typing import Dict, Tuple, List
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import os
import csv
import datetime
import json
import time

def scoreboard_to_dict(scoreboard: str, prefix: str, xmlns: str) -> Dict:
    
    # Get Matchups from scoreboard
    matchups = scoreboard.find(prefix+"matchups", xmlns)

    data = {}

    # Loop through each matchup to pull team stats for the week
    for matchup in matchups:

        # Get the teams involved in the matchup
        teams = matchup.find(prefix+"teams", xmlns)

        # Loop through the teams
        for team in teams:
            tmp = {}

            # Find name
            tmp["name"] = team.find(prefix+"name", xmlns).text
            tmp["team_stats"] = team.find(prefix+"team_stats", xmlns).text
            tmp["gp"] = int(team.find(prefix+"team_remaining_games", xmlns).find(prefix+"total", xmlns).find(prefix+"completed_games", xmlns).text)
            
            stats = team.find(prefix+"team_stats", xmlns).find(prefix+"stats", xmlns)

            for stat in stats:
                # Find stat_id
                stat_id = int(stat.find(prefix+"stat_id", xmlns).text)
                if stat_map[stat_id] in ("fgma","ftma"):
                    tmp[stat_map[stat_id]] = stat.find(prefix+"value", xmlns).text
                else:
                    tmp[stat_map[stat_id]] = float(stat.find(prefix+"value", xmlns).text)

            data[team.find(prefix+"team_id", xmlns).text] = tmp
    
    return data
    
        
def calc_whatifs(data: Dict) -> Tuple[List, List, List, List]:
    # What If?
    what_if_win = []
    what_if_cats = []
    what_if_win_pg = []
    what_if_cats_pg = []

    for team in data.values():
        temp = [team["name"].encode('ascii','ignore').decode('ascii')]
        temp2 = [team["name"].encode('ascii','ignore').decode('ascii')]
        temp_pg = [team["name"].encode('ascii','ignore').decode('ascii')]
        temp2_pg = [team["name"].encode('ascii','ignore').decode('ascii')]
        score = 0
        score_pg = 0
        for opp in data.values():
            # Calculate Win / Loss
            win = ((team["fgp"] > opp["fgp"]) + 
                   (team["ftp"] > opp["ftp"]) + 
                   (team["tpm"] > opp["tpm"]) + 
                   (team["pts"] > opp["pts"]) + 
                   (team["reb"] > opp["reb"]) + 
                   (team["ast"] > opp["ast"]) + 
                   (team["st"] > opp["st"]) + 
                   (team["blk"] > opp["blk"]) + 
                   (team["to"] < opp["to"]))
            lose = ((team["fgp"] < opp["fgp"]) + 
                    (team["ftp"] < opp["ftp"]) + 
                    (team["tpm"] < opp["tpm"]) + 
                    (team["pts"] < opp["pts"]) + 
                    (team["reb"] < opp["reb"]) + 
                    (team["ast"] < opp["ast"]) + 
                    (team["st"] < opp["st"]) + 
                    (team["blk"] < opp["blk"]) + 
                    (team["to"] > opp["to"]))
            
            # Calculate PG Win / Loss
            win_pg = ((team["fgp"] > opp["fgp"]) +
                      (team["ftp"] > opp["ftp"]) +
                      (team["tpm"]/team["gp"] > opp["tpm"]/opp["gp"]) +
                      (team["pts"]/team["gp"] > opp["pts"]/opp["gp"]) +
                      (team["reb"]/team["gp"] > opp["reb"]/opp["gp"]) +
                      (team["ast"]/team["gp"] > opp["ast"]/opp["gp"]) +
                      (team["st"]/team["gp"] > opp["st"]/opp["gp"]) +
                      (team["blk"]/team["gp"] > opp["blk"]/opp["gp"]) +
                      (team["to"]/team["gp"] < opp["to"]/opp["gp"]))
            lose_pg = ((team["fgp"] < opp["fgp"]) +
                       (team["ftp"] < opp["ftp"]) +
                       (team["tpm"]/team["gp"] < opp["tpm"]/opp["gp"]) +
                       (team["pts"]/team["gp"] < opp["pts"]/opp["gp"]) +
                       (team["reb"]/team["gp"] < opp["reb"]/opp["gp"]) +
                       (team["ast"]/team["gp"] < opp["ast"]/opp["gp"]) +
                       (team["st"]/team["gp"] < opp["st"]/opp["gp"]) +
                       (team["blk"]/team["gp"] < opp["blk"]/opp["gp"]) +
                       (team["to"]/team["gp"] > opp["to"]/opp["gp"]))
            
            # Calculate Score
            if win > lose:
                temp.append(1)
                score = score + 1
            elif win < lose:
                temp.append(-1)
                score = score - 1
            else:
                temp.append(0)
            temp2.append(f"{win}={lose}={(9-win-lose)}")
            
            # Calculate PG Score
            if win_pg > lose_pg:
                temp_pg.append(1)
                score_pg += 1
            elif win_pg < lose_pg:
                temp_pg.append(-1)
                score_pg -= 1
            else:
                temp_pg.append(0)
            temp2_pg.append(f"{win_pg}={lose_pg}={(9-win_pg-lose_pg)}")
        
        temp.append(score)
        temp_pg.append(score_pg)
        
        what_if_win.append(temp)
        what_if_cats.append(temp2)
        what_if_win_pg.append(temp_pg)
        what_if_cats_pg.append(temp2_pg)
        
    sort_order = sorted(range(len(what_if_win)), key=lambda k: what_if_win[k][-1],reverse=True)
    sort_order_pg = sorted(range(len(what_if_win_pg)), key=lambda k: what_if_win_pg[k][-1],reverse=True)
    
    # Sort rows
    what_if_win = [what_if_win[i] for i in sort_order]
    what_if_cats = [what_if_cats[i] for i in sort_order]
    what_if_win_pg = [what_if_win_pg[i] for i in sort_order_pg]
    what_if_cats_pg = [what_if_cats_pg[i] for i in sort_order_pg]

    # Sort columns
    for i,team in enumerate(what_if_win):
        tmp = [team[0]]
        for stat in [team[1:-1][i] for i in sort_order]:
            tmp.append(stat)
        tmp.append(team[-1])
        what_if_win[i] = tmp

    for i,team in enumerate(what_if_cats):
        tmp = [team[0]]
        for stat in [team[1:][i] for i in sort_order]:
            tmp.append(stat)
        what_if_cats[i] = tmp
        
    for i,team in enumerate(what_if_win_pg):
        tmp = [team[0]]
        for stat in [team[1:-1][i] for i in sort_order_pg]:
            tmp.append(stat)
        tmp.append(team[-1])
        what_if_win_pg[i] = tmp

    for i,team in enumerate(what_if_cats_pg):
        tmp = [team[0]]
        for stat in [team[1:][i] for i in sort_order_pg]:
            tmp.append(stat)
        what_if_cats_pg[i] = tmp
        
    return (what_if_win, what_if_cats, what_if_win_pg, what_if_cats_pg, sort_order, sort_order_pg)
    
def calc_mvp(data: Dict, sort_order: List, stat_keys: Dict) -> Dict:
    mvp = {}
    w = [1, 1, 3, 1, 2, 2, 3, 3, 2]

    for team in [list(data.values())[i] for i in sort_order]:
        team_stats = [float(team[key]) for key in stat_keys]
        team_stats = np.multiply(team_stats,[1000,1000,1,1,1,1,1,1,-1])
        mvp[team["name"].encode('ascii','ignore').decode('ascii')] = [0,0,0,0,0,0,0,0,0]
        for opp in data.values():
            if team["name"].encode('ascii','ignore').decode('ascii') == opp["name"].encode('ascii','ignore').decode('ascii') :
                continue
            opp_stats = [float(opp[key]) for key in stat_keys]
            opp_stats = np.multiply(opp_stats,[1000,1000,1,1,1,1,1,1,-1])
            diffs = [0,0,0,0,0,0,0,0,0]
            w_diffs = [0,0,0,0,0,0,0,0,0]
            for cat in range(len(stat_keys)):
                diffs[cat] = (team_stats[cat] - opp_stats[cat])
                w_diffs[cat] = diffs[cat]*w[cat]
            WL = np.sign(diffs)
            while sum(WL) < 1:    
                min_value = max([x for x in w_diffs if x <= 0])
                min_key = w_diffs.index(min_value)
                if -diffs[min_key] > mvp[team["name"].encode('ascii','ignore').decode('ascii')][min_key]:
                    mvp[team["name"].encode('ascii','ignore').decode('ascii')][min_key] = round(-diffs[min_key] + 1,1)
                WL[min_key] = 1
                w_diffs[min_key] = 1
    
    return mvp

def output_files(dirname: str, data: Dict, what_if_win: List, what_if_cats: List, what_if_win_pg: List, what_if_cats_pg: List, mvp: Dict, stat_keys: List) -> None:
    # Write weekly results to csv
    with open(dirname+"/1_Results.csv","w") as f:
        f.write("name,fgma,fgp,ftma,ftp,tpm,pts,reb,ast,st,blk,to,gp\n")
        for team in [list(data.values())[i] for i in sort_order]:
            f.write(team["name"].encode('ascii','ignore').decode('ascii')+","+
                    team["fgma"]+","+
                    str(team["fgp"])+","+
                    str(team["ftma"])+","+
                    str(team["ftp"])+","+
                    str(team["tpm"])+","+
                    str(team["pts"])+","+
                    str(team["reb"])+","+
                    str(team["ast"])+","+
                    str(team["st"])+","+
                    str(team["blk"])+","+
                    str(team["to"])+","+
                    str(team["gp"])+"\n")

    # Write Cat Winners to csv
    with open(dirname+"/2_Cat_Winners.csv","w") as f:
        f.write("stat,winner,val\n")

        cat_winners = {}

        for key in stat_keys:
            val = -999999
            cat_winners[key] = {}
            for team in data.values():
                if key == "to":
                    if -team[key] > val:
                        val = -team[key]
                        cat_winners[key]["team"] = team["name"].encode('ascii','ignore').decode('ascii')
                        cat_winners[key]["val"] = -val
                    elif -team[key] == val:
                        val = -team[key]
                        cat_winners[key]["team"] += " | "+team["name"].encode('ascii','ignore').decode('ascii')
                        cat_winners[key]["val"] = -val
                else:
                    if team[key] > val:
                        val = team[key]
                        cat_winners[key]["team"] = team["name"].encode('ascii','ignore').decode('ascii')
                        cat_winners[key]["val"] = val
                    elif team[key] == val:
                        val = team[key]
                        cat_winners[key]["team"] += " | "+team["name"].encode('ascii','ignore').decode('ascii')
                        cat_winners[key]["val"] = val
            f.write(key+","+cat_winners[key]["team"].encode('ascii','ignore').decode('ascii')+","+str(cat_winners[key]["val"])+"\n")

    # Write What If Analytics to csvs
    with open(dirname+"/3_WhatIf_Cats.csv","w") as f:
        # Header
        f.write("team,")
        f.write(",".join([row[0] for row in what_if_cats]))
        f.write("\n")
        
        # Rows
        for row in what_if_cats:
            f.write(",".join(str(x) for x in row)+"\n")
            
    with open(dirname+"/4_WhatIf_WL.csv","w") as f:
        # Header
        f.write("team,")
        f.write(",".join([row[0] for row in what_if_win]))
        f.write(",score\n")
        
        # Rows
        for row in what_if_win:
            f.write(",".join(str(x) for x in row)+"\n")

    with open(dirname+"/5_WhatIf_Cats_pg.csv","w") as f:
        f.write("team,")
        f.write(",".join([row[0] for row in what_if_cats_pg]))
        f.write("\n")
        for row in what_if_cats_pg:
            f.write(",".join(str(x) for x in row)+"\n")
            
    with open(dirname+"/6_WhatIf_WL_pg.csv","w") as f:
        f.write("team,")
        f.write(",".join([row[0] for row in what_if_win_pg]))
        f.write(",score\n")
        for row in what_if_win_pg:
            f.write(",".join(str(x) for x in row)+"\n")
            

    with open(dirname+"/MVP.csv","w") as f:
        f.write("team")
        for cat in stat_keys:
            f.write(","+cat)
        f.write("\n")
        for key,team in mvp.items():
            f.write(key+","+",".join(str(x) for x in np.divide(team,[1000,1000,1,1,1,1,1,1,-1]))+"\n")


def agg_season_data(data_list: List) -> Dict:
    season_data  = data_list[-1]

    for data in data_list[:-1]:
        for k, v in data.items():
            season_data[k]["gp"] += v["gp"]
            season_data[k]["fgma"] = f"{int(season_data[k]['fgma'].split('/')[0]) + int(v['fgma'].split('/')[0])}/{int(season_data[k]['fgma'].split('/')[1]) + int(v['fgma'].split('/')[1])}"
            season_data[k]["ftma"] = f"{int(season_data[k]['ftma'].split('/')[0]) + int(v['ftma'].split('/')[0])}/{int(season_data[k]['ftma'].split('/')[1]) + int(v['ftma'].split('/')[1])}"
            season_data[k]["tpm"] += v["tpm"]
            season_data[k]["pts"] += v["pts"]
            season_data[k]["reb"] += v["reb"]
            season_data[k]["ast"] += v["ast"]
            season_data[k]["st"] += v["st"]
            season_data[k]["blk"] += v["blk"]
            season_data[k]["to"] += v["to"]
            
    for k in season_data:
        season_data[k]["fgp"] = round(int(season_data[k]["fgma"].split("/")[0]) / int(season_data[k]["fgma"].split("/")[1]),3)
        season_data[k]["ftp"] = round(int(season_data[k]["ftma"].split("/")[0]) / int(season_data[k]["ftma"].split("/")[1]),3)
    
        for cat in ["gp", "tpm", "pts", "reb", "ast", "st", "blk", "to"]:
            season_data[k][cat] = round(season_data[k][cat] / len(data_list),1)
    
    return season_data
    
    
# App authentication params
client_id = os.getenv("YAHOO_CLIENT_ID")
client_secret = os.getenv("YAHOO_CLIENT_SECRET")
league_id = '39438'
season_year = 2023
stat_keys = ["fgp","ftp","tpm","pts","reb","ast","st","blk","to"]
prefix = "default:"
xmlns = {"default":"http://fantasysports.yahooapis.com/fantasy/v2/base.rng"}
stat_map = {9004003: "fgma",
            5: "fgp",
            9007006: "ftma",
            8: "ftp",
            10: "tpm",
            12: "pts",
            15: "reb",
            16: "ast",
            17: "st",
            18: "blk",
            19: "to"}

# Get refresh token if exists
try:
    with open("REFRESH_TOKEN", encoding="utf-8") as f:
        REFRESH_TOKEN = f.readline()
except Exception:
    REFRESH_TOKEN = None
    
# Create OAuth Service for yahoo paramaters
authenticator = Authenticator(client_id=os.getenv('YAHOO_CLIENT_ID'),
                              client_secret=os.getenv('YAHOO_CLIENT_SECRET'),
                              refresh_token=REFRESH_TOKEN,
                              auth_url="https://api.login.yahoo.com/oauth2/request_auth",
                              access_token_url="https://api.login.yahoo.com/oauth2/get_token")

# Write the latest refresh token
with open("REFRESH_TOKEN", "w", encoding="utf-8") as f:
    f.write(authenticator.refresh_token)

print("Setting up Fantasy API...")
yahoo_fantasy = FantasyAPI(league_id, season_year, authenticator)

# Get game ID
game_key = yahoo_fantasy.get_game_key()

# Get current week
current_week = yahoo_fantasy.get_current_week(game_key)

# Parse XML to get scoreboard
scoreboard = yahoo_fantasy.get_scoreboard(game_key, current_week)

print(f"Assembling stats for week {current_week}...")

data = scoreboard_to_dict(scoreboard, prefix, xmlns)

# Create folder for week's stats if it doesn't existt
os.makedirs(os.path.dirname("./data/fantasy/week_"+str(current_week)+"/"), exist_ok=True)

# What If?
(what_if_win, what_if_cats, what_if_win_pg, what_if_cats_pg, sort_order, sort_order_pg) = calc_whatifs(data)

# MVP Analysis
mvp = calc_mvp(data, sort_order, stat_keys)

# Output files
output_files(f"./data/fantasy/week_{current_week}", data, what_if_win, what_if_cats, what_if_win_pg, what_if_cats_pg, mvp, stat_keys)

# Get season running totals
print(f"Assembling stats for season...")

data_list = []
for week in range(1,current_week+1):
    # Parse XML to get scoreboard
    scoreboard = yahoo_fantasy.get_scoreboard(game_key, week)
    data_list.append(scoreboard_to_dict(scoreboard, prefix, xmlns))
    
season_data = agg_season_data(data_list)

# Create folder for week's stats if it doesn't existt
os.makedirs(os.path.dirname("./data/fantasy/season_avg/"), exist_ok=True)

# What If?
(what_if_win, what_if_cats, what_if_win_pg, what_if_cats_pg, sort_order, sort_order_pg) = calc_whatifs(season_data)

# MVP Analysis
mvp = calc_mvp(season_data, sort_order, stat_keys)

# Output files
output_files(f"./data/fantasy/season_avg", season_data, what_if_win, what_if_cats, what_if_win_pg, what_if_cats_pg, mvp, stat_keys)
