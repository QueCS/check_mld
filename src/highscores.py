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


class Hapi(et.Element):
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
        Retrieve the API server ID.

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
        Retrieve the API server community.

        Returns if success:
            str: e.g. 'fr'

        Returns if failure:
            NoneType: None
        """
        id = self.server_id()
        community = re.search(r"([a-zA-Z]+)", id)[0]
        return community

    def server_number(self) -> int:
        """
        Retrieve the API server number.

        Returns if success:
            int: e.g. 123

        Returns if failure:
            NoneType: None
        """
        id = self.server_id()
        number = re.search(r"([0-9]+)", id)[0]
        return int(number)

    def player_ids(self) -> list:
        """
        Retrieve the API player IDs.

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

    def player_scores(self) -> list:
        """
        Retrieve the API player scores.

        Raises:
            KeyError: If the attribute 'score' does not exist.

        Returns if success:
            list of int: e.g. [123456789, 456789, 789]

        Returns if failure:
            NoneType: None
        """
        scores = []
        try:
            for player in self.findall("player"):
                scores.append(int(player.attrib["score"]))
        except KeyError as error:
            key_error_to_none(error)
        return scores

    def player_ranks(self) -> list:
        """
        Retrieve the API player ranks.

        Raises:
            KeyError: If the attribute 'position' does not exist.

        Returns if success:
            list of int: e.g. [1, 12, 123]

        Returns if failure:
            NoneType: None
        """
        ranks = []
        try:
            for player in self.findall("player"):
                ranks.append(int(player.attrib["position"]))
        except KeyError as error:
            key_error_to_none(error)
        return ranks

    def player_data(self):
        """
        Retrieve the API players.

        Raises:
            KeyError: If the attribute 'player' does not exist.

        Returns if success:
            list of int: e.g. [123456, 456789, 789123]

        Returns if failure:
            NoneType: None
        """
        players = {}
        try:
            for player in self.findall("player"):
                players[player.attrib["id"]] = {
                    "rank": int(player.attrib["position"]),
                    "score": int(player.attrib["score"]),
                }
        except KeyError as error:
            key_error_to_none(error)
        return players

    def data_dict(self) -> dict:
        """
        Creates a dictionnary containing timestamp, players, player ranks and player scores.

        Returns:
            dict
        """
        data = {}
        data["server"] = self.server_id()
        data["timestamp"] = self.timestamp()
        data.update(self.player_data())
        return data

    def json_export(self, outfile_path: str):
        """
        Export a JSON file containg the API timestamp, players, player ranks and player scores.

        Returns:
            NoneType: None
        """
        data = self.data_dict()
        with open(f"{outfile_path}", "w+") as outfile:
            json.dump(data, outfile)


class MHapi(Hapi):
    def player_ships(self) -> list:
        """
        Retrieve the API player ship count.

        Raises:
            KeyError: If the attribute 'player' does not exist.

        Returns if success:
            list of int: e.g. [1, 123, 123456, 123456789]

        Returns if failure:
            NoneType: None
        """
        ships = []
        try:
            for player in self.findall("player"):
                if "ships" in player.attrib:
                    ships.append(int(player.attrib["ships"]))
                else:
                    ships.append(int(0))
        except KeyError as error:
            key_error_to_none(error)
        return ships

    def player_data(self):
        """
        Retrieve all player data from the API.

        Raises:
            KeyError: If the attribute 'player' does not exist.

        Returns if success:
            list of int: e.g. [123456, 456789, 789123]

        Returns if failure:
            NoneType: None
        """
        players = {}
        try:
            for player in self.findall("player"):
                if "ships" in player.attrib:
                    ships = int(player.attrib["ships"])
                else:
                    ships = int(0)
                players[player.attrib["id"]] = {
                    "rank": int(player.attrib["position"]),
                    "score": int(player.attrib["score"]),
                    "ships": ships,
                }
        except KeyError as error:
            key_error_to_none(error)
        return players


def get_highscore_api(
    server: int,
    community: str,
    hs_category: int,
    hs_type: int,
    max_attempts: int = 6,
    attempt_sleep: int = 10,
) -> Hapi:
    """
    Retrieve the whole XML tree of the highscore API.

    Args:
        server (int): Server ID.

        community (str): Community ID.

        hs_category (int): Highscore category.
            - 1: Player
            - 2: Alliance

        hs_type (str): Highscore type.
            - 0: General
            - 1: Economy
            - 2: Technology
            - 3: Military
            - 4: Military lost
            - 5: Military build
            - 6: Military destroyed
            - 7: Honor
            - 8: Lifeforms
            - 9: Lifeforms economy
            - 10: Lifeforms technology
            - 11: Lifeforms discovery

        max_attempts (int): The number of time the function will try to reach the API.

        attempt_sleep (int): The amount of time (in seconds) the function will wait before trying to reach the API again after a previous failure.

    Raises:
        HTTPError: If there is an error during the request.

    Returns if success:
        Hapi(et.Element): The whole XML document as a tree.

    Returns if failure:
        NoneType: None
    """

    api_url = f"https://s{server}-{community}.ogame.gameforge.com/api/highscore.xml?category={hs_category}&type={hs_type}"

    attempt = 1

    while attempt < max_attempts:
        try:
            response = requests.get(api_url, allow_redirects=False, timeout=10)
        except requests.exceptions.RequestException as error:
            logging.warning(
                f"Calling get_highscore_api(): RequestException: {error}. Trying again in {attempt_sleep}s ({attempt}/{max_attempts}"
            )
            time.sleep(attempt_sleep)
            attempt += 1
            continue
        if response.status_code == 200:
            xml_tree = et.fromstring(response.content)
            if hs_type == 3:
                tree = MHapi(xml_tree.tag, xml_tree.attrib, **xml_tree.attrib)
            else:
                tree = Hapi(xml_tree.tag, xml_tree.attrib, **xml_tree.attrib)
            tree.extend(list(xml_tree))
            return tree
        else:
            logging.warning(
                f"Calling get_highscore_api(): HTTP error: {response.status_code}. Trying again in {attempt_sleep}s ({attempt}/{max_attempts})"
            )
            time.sleep(attempt_sleep)
            attempt += 1
    logging.error(
        f"Reached maximum attempts limit ({max_attempts}). Unable to obtain XML tree."
    )
    return None
