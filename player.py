from dataclasses import dataclass
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Any
from nba_api.stats.static.players import find_players_by_full_name


def safe_value(x):
    if len(x.values) == 0:
        return 0
    else:
        return x.values[0]


@dataclass
class Player:
    fantasy_player_id: str
    player_first_name: str
    player_last_name: str
    team_name: str
    team_abbr: str
    uniform_nbr: int
    position: str
    status: str
    ownership_type: str
    owner_id: str
    owner_name: str
    nba_player_id: Optional[int] = None
    game_log: Optional[pd.DataFrame] = None

    def get_nba_player_id(self):
        try:
            player_results = find_players_by_full_name(f"{self.player_first_name} {self.player_last_name}")
            if len(player_results) == 0:
                raise(Exception("Player Not Found!"))
            return player_results[0]["id"]
        except Exception as e:
            player_results = find_players_by_full_name(
                f"{self.player_first_name.replace('.', '')} {self.player_last_name}")
            if len(player_results) == 0:
                print(self)
                quit()
            else:
                return player_results[0]["id"]

    def agg_stats(self, window: int = 7):
        full_columns = ["PLAYER_ID",
                        "PLAYER_NAME",
                        "GAME_DATE",
                        "WL",
                        "MIN",
                        "FGM",
                        "FGA",
                        "FTM",
                        "FTA",
                        "FG3M",
                        "FG3A",
                        "PTS",
                        "REB",
                        "AST",
                        "STL",
                        "BLK",
                        "TOV"]
        agg_dict = {"GAME_DATE": ["count"],
                    "MIN": ["mean", "std"],
                    "PTS": ["mean", "std"],
                    "FGM": ["sum"],
                    "FGA": ["sum"],
                    "FTM": ["sum"],
                    "FTA": ["sum"],
                    "FG3M": ["mean", "std"],
                    "REB": ["mean", "std"],
                    "AST": ["mean", "std"],
                    "STL": ["mean", "std"],
                    "BLK": ["mean", "std"],
                    "TOV": ["mean", "std"]}
        player_stats = self.game_log[pd.to_datetime(self.game_log.GAME_DATE) > (datetime.today() - timedelta(days=window))][full_columns]
        agg_player_stats = player_stats.groupby(["PLAYER_ID", "PLAYER_NAME"]).agg(agg_dict)
        agg_player_stats.columns = agg_player_stats.columns.to_flat_index()
        agg_player_stats.columns = [col1 + "_" + col2 for col1, col2 in agg_player_stats.columns]
        agg_player_stats["FGP_mean"] = agg_player_stats.apply(
            lambda row: row["FGM_sum"] / row["FGA_sum"] if row["FGA_sum"] > 0 else float('nan'), axis=1)
        agg_player_stats["FTP_mean"] = agg_player_stats.apply(
            lambda row: row["FTM_sum"] / row["FTA_sum"] if row["FTA_sum"] > 0 else float('nan'), axis=1)

        return agg_player_stats

    def compute_score(self, window: int = 7, weights: List[Any] = [1, 1.5, 1.5, 2, 2, 2, -1, 10, 10]) -> float:
        vals = [safe_value(self.agg_stats(window)["PTS_mean"]),
                safe_value(self.agg_stats(window)["REB_mean"]),
                safe_value(self.agg_stats(window)["AST_mean"]),
                safe_value(self.agg_stats(window)["STL_mean"]),
                safe_value(self.agg_stats(window)["BLK_mean"]),
                safe_value(self.agg_stats(window)["FG3M_mean"]),
                safe_value(self.agg_stats(window)["TOV_mean"]),
                safe_value(self.agg_stats(window)["FGM_sum"]) / safe_value(self.agg_stats(window)["FGA_sum"]) if safe_value(self.agg_stats(window)["FGA_sum"]) > 0 else 0,
                safe_value(self.agg_stats(window)["FTM_sum"]) / safe_value(self.agg_stats(window)["FTA_sum"]) if safe_value(self.agg_stats(window)["FTA_sum"]) > 0 else 0]

        return sum([a*b for a, b in zip(vals, weights)])
