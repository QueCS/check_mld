import requests
import xml.etree.ElementTree as et
import logging
import time
import re
import json


def key_error_to_none(err):
    logging.error(
        f"Calling Papi.timestamp(): attribute {err} not found in Hapi XML tree."
    )
    return None


class Papi(et.Element):
    def timestamp(self) -> int:
        """
        Retrieve the API last update Unix Epoch timestamp.

        Raises:
            KeyError: If the attribute 'timestamp' does not exist.

        Returns if success:
            int: Epoch Unix timestamp

        Returns if failure:
            NoneType: None
        """
        try:
            timestamp = self.attrib["timestamp"]
        except KeyError as error:
            key_error_to_none(error)
        return int(timestamp)

    def server_id(self) -> int:
        """
        Retrieve the server ID from the API.

        Raises:
            KeyError: If the attribute 'serverId' does not exist.

        Returns if success:
            str: e.g. 'fr123'

        Returns if failure:
            NoneType: None
        """
        try:
            server_id = self.attrib["serverId"]
        except KeyError as error:
            key_error_to_none(error)
        return str(server_id)

    def server_community(self) -> str:
        """
        Retrieve the server community from the API.

        Returns if success:
            str: e.g. 'fr'
        """
        id = self.server_id()
        community = re.search(r"([a-zA-Z]+)", id)[0]
        return community

    def server_number(self) -> int:
        """
        Retrieve the API server number.

        Returns if success:
            int: e.g. 123
        """
        id = self.server_id()
        number = re.search(r"([0-9]+)", id)[0]
        return int(number)

    def player_ids(self) -> list:
        """
        Retrieve the player IDs from the API.

        Raises:
            KeyError: If the attribute 'id' does not exist.

        Returns if success:
            list of str: e.g. ['123456', '456789', '789123']

        Returns if failure:
            NoneType: None
        """
        ids = []
        try:
            for player in self.findall("player"):
                ids.append(player.attrib["id"])
        except KeyError as error:
            key_error_to_none(error)
        return ids

    def player_names(self) -> list:
        """
        Retrieve the player names from the API.

        Raises:
            KeyError: If the attributes 'player' or 'name' do not exist.

        Returns if success:
            list of str: e.g. ['abc', 'abcdef', 'abcdefghi']

        Returns if failure:
            NoneType: None
        """
        names = []
        try:
            for player in self.findall("player"):
                names.append(player.attrib["name"])
        except KeyError as error:
            key_error_to_none(error)
        return names

    def player_status(self) -> list:
        """
        Retrieve the players status from the API.

        Raises:
            KeyError: If the attribute 'player' or 'status' do not exist.

        Returns if success:
            list of str: e.g. ['vI', 'I', 'Act', 'Act', 'vi']
            a: player is an administrator
            Act: player is active
            b: player is banned
            i: player is inactive (7d < i < 35d)
            I: player is Inactive (I > 35d)
            o: player is an outlaw
            v: player is in vacation mode

        Returns if failure:
            NoneType: None
        """
        names = []
        try:
            for player in self.findall("player"):
                if "status" in player.attrib:
                    names.append(player.attrib["status"])
                else:
                    names.append("Act")
        except KeyError as error:
            key_error_to_none(error)
        return names

    def player_alliance(self) -> list:
        """
        Retrieve the players alliance IDs from the API.

        Raises:
            KeyError: If the attribute 'player' does not exist.

        Returns if success:
            list of str: e.g. ['501459', '501369', 'None']
            'ID': player has an alliance
            'None': player has no alliance

        Returns if failure:
            NoneType: None
        """
        alliances = []
        try:
            for player in self.findall("player"):
                if "alliance" in player.attrib:
                    alliances.append(player.attrib["alliance"])
                else:
                    alliances.append("None")
        except KeyError as error:
            key_error_to_none(error)
        return alliances

    def player_data(self) -> dict:
        """
        Retrieve all player data from the API.

        Raises:
            KeyError: If the attribute 'player' does not exist.

        Returns if success:
            dict

        Returns if failure:
            NoneType: None
        """
        players = {}
        try:
            for player in self.findall("player"):
                if "status" in player.attrib:
                    status = player.attrib["status"]
                else:
                    status = "Act"
                if "alliance" in player.attrib:
                    alliance = player.attrib["alliance"]
                else:
                    alliance = "None"
                players[player.attrib["id"]] = {
                    "name": player.attrib["name"],
                    "status": status,
                    "alliance": alliance,
                }
        except KeyError as error:
            key_error_to_none(error)
        return players

    def json_export(self, outfile_path: str):
        """
        Export a JSON file containg the API timestamp, player IDs, names, status and alliances.

        Returns:
            NoneType: None
        """
        data = {}
        data["server"] = self.server_id()
        data["timestamp"] = self.timestamp()
        data.update(self.player_data())
        with open(f"{outfile_path}", "w+") as outfile:
            json.dump(data, outfile)

    def name_from_id(self, player_id: str) -> str:
        """
        Returns the name of a player using its ID.

        Returns if success:
            str

        Returns if failure:
            NoneType
        """
        data = self.player_data()
        if data is None:
            return None
        try:
            return str(data[player_id]["name"])
        except KeyError:
            return None

    def id_from_name(self, player_name: str) -> str:
        """
        Returns the ID of a player using its name.

        Returns if success:
            str

        Returns if failure:
            NoneType
        """
        data = self.player_data()
        if data is None:
            return None
        try:
            for key in data.keys():
                if data[key]["name"] == player_name:
                    return str(key)
        except KeyError:
            return None


def get_players_api(
    server: int,
    community: str,
    max_attempts: int = 6,
    attempt_sleep: int = 10,
) -> Papi:
    """
    Retrieve the whole XML tree of the players API.

    Args:
        server (int): Server ID.

        community (str): Community ID.

        max_attempts (int): The number of time the function will try to reach the API.

        attempt_sleep (int): The amount of time (in seconds) the function will wait before trying to reach the API again after a previous failure.

    Raises:
        HTTPError: If there is an error during the request.

    Returns if success:
        Papi(et.Element): The whole XML document as a tree.

    Returns if failure:
        NoneType: None
    """

    api_url = f"https://s{server}-{community}.ogame.gameforge.com/api/players.xml"

    attempt = 1

    while attempt < max_attempts:
        try:
            response = requests.get(api_url, allow_redirects=False, timeout=5)
        except requests.exceptions.RequestException as error:
            logging.warning(
                f"Calling get_players_api(): RequestException: {error}. Trying again in {attempt_sleep}s ({attempt}/{max_attempts}"
            )
            time.sleep(attempt_sleep)
            attempt += 1
            continue
        if response.status_code == 200:
            xml_tree = et.fromstring(response.content)
            tree = Papi(xml_tree.tag, xml_tree.attrib, **xml_tree.attrib)
            tree.extend(list(xml_tree))
            return tree
        else:
            logging.warning(
                f"Calling get_players_api(): HTTP error: {response.status_code}. Trying again in {attempt_sleep}s ({attempt}/{max_attempts})"
            )
            time.sleep(attempt_sleep)
            attempt += 1
    logging.error(
        f"Reached maximum attempts limit ({max_attempts}). Unable to obtain XML tree."
    )
    return None
