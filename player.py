from dataclasses import dataclass
import pandas as pd
from typing import Optional, List, Any, Dict
from nba_api.stats.static.players import find_players_by_full_name


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
                return 0
            else:
                return player_results[0]["id"]
