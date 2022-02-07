import csv
import pandas
from nba_api.stats.endpoints.playergamelogs import PlayerGameLogs


class NBAStats:

    # REFACTOR:
    #   Accept a dictionary (mapping) instead of a file to make more generic
    def __init__(self, lookup_file: str, season: str):
        with open(lookup_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            self.id_lookup = {fantasy_player_id: int(float(0 if nba_player_id == "" else nba_player_id)) for fantasy_player_id, _, _, nba_player_id in reader}

        self.gamelogs = self.get_all_gamelogs(season)

    def get_player_id(self, fantasy_player_id: str) -> int:
        return self.id_lookup.get(fantasy_player_id, 0)

    @staticmethod
    def get_all_gamelogs(season: str) -> pandas.DataFrame:
        return PlayerGameLogs(season_nullable=season).get_data_frames()[0]

    def get_gamelogs(self, player_id: int) -> pandas.DataFrame:
        return self.gamelogs[self.gamelogs["PLAYER_ID"] == player_id]
