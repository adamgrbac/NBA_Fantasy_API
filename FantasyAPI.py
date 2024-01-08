import requests
import pandas as pd
import numpy as np
import Authenticator
import xml.etree.ElementTree as ET
from player import Player
from typing import List


# REFACTOR:
#   Make this an abstract class to account for other fantasy services
class FantasyAPI:
    def __init__(self, league_id: int, season: int, authenticator: Authenticator, week:int=None):
        self.league_id = league_id
        self.access_token = authenticator.access_token
        self.PREFIX = "default:"
        self.XMLNS = {"default": "http://fantasysports.yahooapis.com/fantasy/v2/base.rng"}
        self.season = season
        self.week = week
        self.players = self.get_players()

    def get_game_key(self) -> str:
        res = requests.get(f"https://fantasysports.yahooapis.com/fantasy/v2/games;game_codes=nba;seasons={self.season}",
                           headers={"Authorization": f"Bearer {self.access_token}"})
        root = ET.fromstring(res.content.decode('utf8'))

        return root.find(f"{self.PREFIX}games", self.XMLNS).find(f"{self.PREFIX}game", self.XMLNS).find(f"{self.PREFIX}game_key", self.XMLNS).text
        
    def get_current_week(self, game_key: str) -> int:
        if self.week:
            return self.week

        res = requests.get(f'https://fantasysports.yahooapis.com/fantasy/v2/league/{game_key}.l.{self.league_id}',
                           headers={"Authorization": f"Bearer {self.access_token}"})
        root = ET.fromstring(res.content.decode('utf8'))

        return int(root.find(f"{self.PREFIX}league", self.XMLNS).find(f"{self.PREFIX}current_week", self.XMLNS).text) - 1
        
    def get_scoreboard(self, game_key, week: int) -> str:
        res = requests.get(f'https://fantasysports.yahooapis.com/fantasy/v2/league/{game_key}.l.{self.league_id}/scoreboard?week={str(week)}',
                           headers={"Authorization": f"Bearer {self.access_token}"})
        root = ET.fromstring(res.content.decode('utf8'))

        return root.find(f"{self.PREFIX}league", self.XMLNS).find(f"{self.PREFIX}scoreboard", self.XMLNS)

    def get_players(self) -> List[Player]:
        empty = False
        start = 0
        players = []
        game_key = self.get_game_key()
        while not empty:
            res = requests.get(f'https://fantasysports.yahooapis.com/fantasy/v2/league/{game_key}.l.{self.league_id}/players;start={start}/ownership',
                               headers={"Authorization": f"Bearer {self.access_token}"})
            root = ET.fromstring(res.content.decode('utf8'))
            xml_players = root.find(f"{self.PREFIX}league", self.XMLNS).find(f"{self.PREFIX}players", self.XMLNS)
            if len(xml_players) == 0:
                empty = True
            else:
                for xml_player in xml_players:
                    name_xml = xml_player.find(f"{self.PREFIX}name", self.XMLNS)
                    ownership_xml = xml_player.find(f"{self.PREFIX}ownership", self.XMLNS)
                    name_dict = {item.tag.replace("{" + self.XMLNS["default"] + "}", ""): item.text for item in name_xml}
                    ownership_dict = {item.tag.replace("{" + self.XMLNS["default"] + "}", ""): item.text for item in ownership_xml}
                    player_dict = {item.tag.replace("{" + self.XMLNS["default"] + "}", ""): item.text for item in xml_player if item.tag.replace("{" + self.XMLNS["default"] + "}", "") not in ["name", "ownership"]}
                    for k, v in name_dict.items():
                        player_dict[k] = v
                    for k, v in ownership_dict.items():
                        player_dict[k] = v
                    players.append(Player(player_dict["player_key"],
                                          player_dict["first"],
                                          player_dict["last"],
                                          player_dict["editorial_team_full_name"],
                                          player_dict["editorial_team_abbr"],
                                          player_dict["uniform_number"],
                                          player_dict["display_position"],
                                          player_dict.get("status", ""),
                                          player_dict["ownership_type"],
                                          player_dict.get("owner_team_key", ""),
                                          player_dict.get("owner_team_name", "")))

                start += len(xml_players)

        return players




