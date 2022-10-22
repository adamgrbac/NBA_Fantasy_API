import pandas
from datetime import datetime, timedelta, date
from nba_api.stats.endpoints.playergamelogs import PlayerGameLogs
from typing import Optional, Dict


class NBAStats:

    def __init__(self, lookup: Dict[int, int], season: str):
        self.id_lookup = lookup
        self.gamelogs = self.get_all_gamelogs(season)

    def get_player_id(self, fantasy_player_id: str) -> int:
        return self.id_lookup.get(fantasy_player_id, 0)

    @staticmethod
    def get_all_gamelogs(season: str) -> pandas.DataFrame:
        return PlayerGameLogs(season_nullable=season).get_data_frames()[0]

    def get_player_gamelogs(self, fantasy_player_id: int, window: Optional[int]=None) -> pandas.DataFrame:
        if window:
            return self.gamelogs[(self.gamelogs["PLAYER_ID"] == self.get_player_id(fantasy_player_id)) & (self.gamelogs["GAME_DATE"] > (date.today() - timedelta(days=window)))]
        else:
            return self.gamelogs[self.gamelogs["PLAYER_ID"] == self.get_player_id(fantasy_player_id)]
