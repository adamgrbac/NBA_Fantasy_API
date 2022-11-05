from Authenticator import Authenticator
from FantasyAPI import FantasyAPI

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import os
import csv
import datetime
import json
import time

# App authentication params
client_id = os.getenv("YAHOO_CLIENT_ID")
client_secret = os.getenv("YAHOO_CLIENT_SECRET")
league_id = '81070'
season_year = 2022
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
    f.write(REFRESH_TOKEN)

print("Setting up Fantasy API...")
yahoo_fantasy = FantasyAPI(league_id, season_year, authenticator)

# Get game ID
game_key = yahoo_fantasy.get_game_key()

# Get current week
current_week = yahoo_fantasy.get_current_week(game_key)

# Parse XML to get scoreboard
scoreboard = yahoo_fantasy.get_scoreboard(game_key, current_week)

# Get Matchups from scoreboard
matchups = scoreboard.find(prefix+"matchups", xmlns)

data = []

print(f"Assembling stats for week {current_week}...")

# Loop through each matchup to pull team stats for the week
for matchup in matchups:

    # Get the teams involved in the matchup
    teams = matchup.find(prefix+"teams", xmlns)

    # Loop through the teams
    for team in teams:
        tmp = {}

        # Find name
        tmp["name"] = team.find(prefix+"name", xmlns).text
        tmp["team_id"] = team.find(prefix+"team_id", xmlns).text
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

        data.append(tmp)

# Create folder for week's stats if it doesn't existt
os.makedirs(os.path.dirname("./data/fantasy/week_"+str(current_week)+"/"), exist_ok=True)

# What If?

what_if_win = []
what_if_cats = []

for team in data:
	temp = [team["name"].encode('ascii','ignore').decode('ascii')]
	temp2 = [team["name"].encode('ascii','ignore').decode('ascii')]
	score = 0
	for opp in data:
		win = (team["fgp"] > opp["fgp"]) + (team["ftp"] > opp["ftp"]) + (team["tpm"] > opp["tpm"]) + (team["pts"] > opp["pts"]) + (team["reb"] > opp["reb"]) + (team["ast"] > opp["ast"]) + (team["st"] > opp["st"]) + (team["blk"] > opp["blk"]) + (team["to"] < opp["to"])
		lose = (team["fgp"] < opp["fgp"]) + (team["ftp"] < opp["ftp"]) + (team["tpm"] < opp["tpm"]) + (team["pts"] < opp["pts"]) + (team["reb"] < opp["reb"]) + (team["ast"] < opp["ast"]) + (team["st"] < opp["st"]) + (team["blk"] < opp["blk"]) + (team["to"] > opp["to"])
		if win > lose:
			temp.append(1)
			score = score + 1
		elif win < lose:
			temp.append(-1)
			score = score - 1
		else:
			temp.append(0)
		temp2.append(str(win)+"="+str(lose)+"="+str(9-win-lose))
	temp.append(score)
	what_if_win.append(temp)
	what_if_cats.append(temp2)


# Sort WhatIf_WL by Overall Score
sort_order = sorted(range(len(what_if_win)), key=lambda k: what_if_win[k][-1],reverse=True)

# Sort rows
what_if_win = [what_if_win[i] for i in sort_order]
what_if_cats = [what_if_cats[i] for i in sort_order]

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

# Write What If Analytics to csvs

with open("./data/fantasy/week_"+str(current_week)+"/4_WhatIf_WL.csv","w") as f:
    # Header
    f.write("team,")
    f.write(",".join([row[0] for row in what_if_win]))
    f.write(",score\n")
    
    # Rows
    for row in what_if_win:
        f.write(",".join(str(x) for x in row)+"\n")

with open("./data/fantasy/week_"+str(current_week)+"/3_WhatIf_Cats.csv","w") as f:
    # Header
    f.write("team,")
    f.write(",".join([row[0] for row in what_if_cats]))
    f.write("\n")
    
    # Rows
    for row in what_if_cats:
        f.write(",".join(str(x) for x in row)+"\n")
        
# Write weekly results to csv
with open("./data/fantasy/week_"+str(current_week)+"/1_Results.csv","w") as f:
    f.write("name,fgma,fgp,ftma,ftp,tpm,pts,reb,ast,st,blk,to,gp\n")
    for team in [data[i] for i in sort_order]:
        f.write(team["name"].encode('ascii','ignore').decode('ascii')+","+team["fgma"]+","+str(team["fgp"])+","+str(team["ftma"])+","+str(team["ftp"])+","+str(team["tpm"])+","+str(team["pts"])+","+str(team["reb"])+","+str(team["ast"])+","+str(team["st"])+","+str(team["blk"])+","+str(team["to"])+","+str(team["gp"])+"\n")

# MVP Analysis
 
mvp = {}
stat_keys = ["fgp","ftp","tpm","pts","reb","ast","st","blk","to"]
w = [1, 1, 3, 1, 2, 2, 3, 3, 2]

for team in [data[i] for i in sort_order]:
    team_stats = [float(team[key]) for key in stat_keys]
    team_stats = np.multiply(team_stats,[1000,1000,1,1,1,1,1,1,-1])
    mvp[team["name"].encode('ascii','ignore').decode('ascii')] = [0,0,0,0,0,0,0,0,0]
    for opp in data:
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
                mvp[team["name"].encode('ascii','ignore').decode('ascii')][min_key] = -diffs[min_key] + 1
            WL[min_key] = 1
            w_diffs[min_key] = 1

with open("./data/fantasy/week_"+str(current_week)+"/MVP.csv","w") as f:
    f.write("team")
    for cat in stat_keys:
        f.write(","+cat)
    f.write("\n")
    for key,team in mvp.items():
        f.write(key+","+",".join(str(x) for x in np.divide(team,[1000,1000,1,1,1,1,1,1,-1]))+"\n")

# Cat Winners

with open("./data/fantasy/week_"+str(current_week)+"/2_Cat_Winners.csv","w") as f:
    f.write("stat,winner,val\n")

    cat_winners = {}

    for key in stat_keys:
        val = -999999
        cat_winners[key] = {}
        for team in data:
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

### EXPERIMENTAL

# What If?

what_if_win = []
what_if_cats = []

for team in data:
	temp = [team["name"].encode('ascii','ignore').decode('ascii')]
	temp2 = [team["name"].encode('ascii','ignore').decode('ascii')]
	score = 0
	for opp in data:
		win = (team["fgp"] > opp["fgp"]) +\
              (team["ftp"] > opp["ftp"]) +\
              (team["tpm"]/team["gp"] > opp["tpm"]/opp["gp"]) +\
              (team["pts"]/team["gp"] > opp["pts"]/opp["gp"]) +\
              (team["reb"]/team["gp"] > opp["reb"]/opp["gp"]) +\
              (team["ast"]/team["gp"] > opp["ast"]/opp["gp"]) +\
              (team["st"]/team["gp"] > opp["st"]/opp["gp"]) +\
              (team["blk"]/team["gp"] > opp["blk"]/opp["gp"]) +\
              (team["to"]/team["gp"] < opp["to"]/opp["gp"])
		lose = (team["fgp"] < opp["fgp"]) +\
               (team["ftp"] < opp["ftp"]) +\
               (team["tpm"]/team["gp"] < opp["tpm"]/opp["gp"]) +\
               (team["pts"]/team["gp"] < opp["pts"]/opp["gp"]) +\
               (team["reb"]/team["gp"] < opp["reb"]/opp["gp"]) +\
               (team["ast"]/team["gp"] < opp["ast"]/opp["gp"]) +\
               (team["st"]/team["gp"] < opp["st"]/opp["gp"]) +\
               (team["blk"]/team["gp"] < opp["blk"]/opp["gp"]) +\
               (team["to"]/team["gp"] > opp["to"]/opp["gp"])
		if win > lose:
			temp.append(1)
			score = score + 1
		elif win < lose:
			temp.append(-1)
			score = score - 1
		else:
			temp.append(0)
		temp2.append(str(win)+"="+str(lose)+"="+str(9-win-lose))
	temp.append(score)
	what_if_win.append(temp)
	what_if_cats.append(temp2)

# Sort WhatIf_WL by Overall Score
sort_order = sorted(range(len(what_if_win)), key=lambda k: what_if_win[k][-1],reverse=True)
what_if_win = [what_if_win[i] for i in sort_order]
what_if_cats = [what_if_cats[i] for i in sort_order]

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

# Write What If Analytics to csvs

with open("./data/fantasy/week_"+str(current_week)+"/6_WhatIf_WL_pg.csv","w") as f:
    f.write("team")
    for row in what_if_win:
        f.write(","+row[0])
    f.write(",score\n")
    for row in what_if_win:
        f.write(",".join(str(x) for x in row)+"\n")

with open("./data/fantasy/week_"+str(current_week)+"/5_WhatIf_Cats_pg.csv","w") as f:
    f.write("team")
    for row in what_if_cats:
        f.write(","+row[0])
    f.write("\n")
    for row in what_if_cats:
        f.write(",".join(str(x) for x in row)+"\n")

### END EXPERIMENTAL