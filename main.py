from Authenticator import Authenticator
from FantasyAPI import FantasyAPI
from NBAStats import NBAStats
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def main():
    print("Setting up stats...")
    stats = NBAStats("all_players.csv", "2021-22")

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

    print("Setting up Fantasy API...")
    yahoo_fantasy = FantasyAPI(32905, authenticator, stats)

    # Write new REFRESH_TOKEN to file for future use.
    with open("REFRESH_TOKEN", "w") as f:
        f.write(authenticator.refresh_token)

    print("Getting fantasy players...")
    players = yahoo_fantasy.get_players()

    my_players = filter(lambda x: x.owner_name == "What're you doing stepBrogdon?", players)
    healthy_free_agents = list(filter(lambda x: x.ownership_type == "freeagents" and x.status == "", players))

    agg_stats = pd.concat([player.agg_stats(30) for player in players])
    agg_stats["TOV_mean"] = -1*agg_stats["TOV_mean"]

    agg_cols = ["FGP_mean",
                "FTP_mean",
                "PTS_mean",
                "REB_mean",
                "AST_mean",
                "FG3M_mean",
                "BLK_mean",
                "STL_mean",
                "TOV_mean"]

    # Normalise 30-day averages
    for col in agg_cols:
        agg_stats[col+"_norm"] = (agg_stats[col] - agg_stats[col].mean()) / agg_stats[col].std()

    agg_stats["score"] = agg_stats[[col for col in agg_stats.columns if "_norm" in col]].sum(axis=1)
    print(agg_stats.sort_values(by="score", axis=0, ascending=False))

    quit()

    weights = [1, 1, 1, 1, 1, 1, 0, 0, 0]

    # Calculate Free Agent Scores
    print("Calculating free agent scores...")
    free_agent_scores = []

    for free_agent in healthy_free_agents:
        free_agent_scores.append((free_agent, free_agent.compute_score(weights=weights)))

    # Compare Team Scores to Free Agent Scores
    for player in my_players:
        player_score = player.compute_score(weights=weights)
        print(f"{player.player_first_name} {player.player_last_name}: {player_score}")
        for free_agent, free_agent_score in free_agent_scores:
            if free_agent_score > player_score > 0:
                print(f"\t{free_agent.player_first_name} {free_agent.player_last_name}: {free_agent_score}")


if __name__ == "__main__":
    main()
