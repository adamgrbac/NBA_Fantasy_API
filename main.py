from Authenticator import Authenticator
from FantasyAPI import FantasyAPI
from NBAStats import NBAStats
import csv
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REFRESH_ID = False
LOOKUP_FILE = "./data/nba/all_players.csv"

def main():

    # Set up Yahoo authentication
    try:
        with open("REFRESH_TOKEN", "r") as f:
            refresh_token = f.readline()
    except FileNotFoundError:
        print("No refresh token!")
        refresh_token = None

    print("Setting up authenticator...")
    authenticator = Authenticator(client_id=os.getenv('YAHOO_CLIENT_ID'),
                                  client_secret=os.getenv('YAHOO_CLIENT_SECRET'),
                                  refresh_token=refresh_token,
                                  auth_url="https://api.login.yahoo.com/oauth2/request_auth",
                                  access_token_url="https://api.login.yahoo.com/oauth2/get_token")
                                  
    # Write new REFRESH_TOKEN to file for future use.
    with open("REFRESH_TOKEN", "w") as f:
        f.write(authenticator.refresh_token)

    print("Setting up Fantasy API...")
    yahoo_fantasy = FantasyAPI(81070, 2022, authenticator)
    
    if REFRESH_ID:
        player_lookup = []
        for player in yahoo_fantasy.players:
            player.nba_player_id = player.get_nba_player_id()
            player_lookup.append({"fantasy_player_id": player.fantasy_player_id,
                                  "player_first_name": player.player_first_name,
                                  "player_last_name": player.player_last_name,
                                  "nba_player_id": int(player.nba_player_id)})
        df_player_lookup = pd.DataFrame(player_lookup)
        df_player_lookup.to_csv(LOOKUP_FILE, index=False)
        
    with open(LOOKUP_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        id_lookup = {fantasy_player_id: int(float(0 if nba_player_id == "" else nba_player_id)) for fantasy_player_id, _, _, nba_player_id in reader}
     
    # Get NBA Stats
    print("Setting up stats...")
    stats = NBAStats(id_lookup, "2022-23")
    
    # Set NBA Player IDs based on lookup
    for player in yahoo_fantasy.players:
        player.nba_player_id = id_lookup.get(player.fantasy_player_id,0)
        
    # D_PLAYER
    player_df = pd.DataFrame(yahoo_fantasy.players)
    player_df["PLAYER_ID"] = player_df["nba_player_id"]
    player_df_cols = ["PLAYER_ID"]+[col for col in list(player_df.columns) if col not in ["PLAYER_ID", "nba_player_id"]]
    player_df[player_df_cols].to_csv("./data/nba/D_PLAYER.csv", index=False)

    # D_TEAM
    stats.gamelogs[["TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME"]].drop_duplicates().to_csv("./data/nba/D_TEAM.csv", index=False)    

    # D_GAME
    stats.gamelogs[["GAME_ID", "GAME_DATE"]].drop_duplicates().to_csv("./data/nba/D_GAME.csv", index=False) 
    
    # F_GAMELOGS
    F_GAMELOGS_COLS = [col for col in list(stats.gamelogs.columns) if col not in ["TEAM_ABBREVIATION", "TEAM_NAME", "PLAYER_NAME", "NICKNAME", "GAME_DATE", "MATCHUP", "DD2", "TD3", "WNBA_FANTASY_PTS", "VIDEO_AVAILABLE_FLAG"]]
    F_GAMELOGS_COLS = [col for col in F_GAMELOGS_COLS if "RANK" not in col]
    stats.gamelogs[F_GAMELOGS_COLS].to_csv("./data/nba/F_GAMELOGS.csv", index=False)

    my_players = filter(lambda x: x.owner_name == "Should we get a Marvin Bagley?", yahoo_fantasy.players)
    healthy_free_agents = list(filter(lambda x: x.ownership_type == "freeagents" and x.status == "", yahoo_fantasy.players))
    
if __name__ == "__main__":
    main()
