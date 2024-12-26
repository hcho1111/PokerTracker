from api.common import create_connection
from typing import List
import json

NEW_PLAYER_DEFAULT_FIRST_NAME = "New"
NEW_PLAYER_DEFAULT_LAST_NAME = "Player"


# Player that is either new (needs name to be updated) or needs merging with an existing player.
class UnpublishedPlayer:
    player_id: int
    pokernow_names: List[str]
    merge_suggestion_player_id: str
    merge_suggestion_name: str

    def __init__(
        self,
        player_id: int,
        pokernow_names: List[str],
        merge_suggestion_player_id: str,
        merge_suggestion_name: str,
    ):
        self.player_id = player_id
        self.pokernow_names = pokernow_names
        self.merge_suggestion_player_id = merge_suggestion_player_id
        self.merge_suggestion_name = merge_suggestion_name

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return UnpublishedPlayer(**data)


def get_published_players():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT firstname,lastname,id FROM players WHERE published='1' ORDER BY firstname"
        )
        return cursor.fetchall()


def get_unpublished_players():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM players WHERE published='0'")
        unpublished_players = []
        for player_id_row in cursor.fetchall():
            player_id = player_id_row[0]
            cursor.execute(
                "SELECT pokernow_name FROM pokernowaliases WHERE player_id='%s'"
                % (player_id)
            )
            pokernow_names = [x[0] for x in cursor.fetchall()]
            suggested_player_id, suggested_pokernow_name = _find_suggestion(
                cursor, pokernow_names
            )
            unpublished_players.append(
                UnpublishedPlayer(
                    player_id,
                    pokernow_names,
                    suggested_player_id,
                    suggested_pokernow_name,
                )
            )
        return unpublished_players


def publish_player(player_id: int, first_name: str, last_name: str, venmo: str):
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE players SET firstname = '%s', lastname ='%s', venmo = '%s', published = '1' WHERE id = '%s'"
            % (first_name, last_name, venmo, player_id)
        )


def merge_player(player_id_to_merge, player_id):
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE pokernowaliases SET player_id='%s' WHERE player_id='%s'"
            % (player_id, player_id_to_merge)
        )
        cursor.execute(
            "UPDATE ledgerrows SET player_id='%s' WHERE player_id='%s'"
            % (player_id, player_id_to_merge)
        )
        cursor.execute("DELETE FROM players WHERE id='%s'" % player_id_to_merge)


def _find_suggestion(cursor, pokernow_names: List[str]) -> (str, str):
    if len(pokernow_names) == 0:
        return None, None
    cursor.execute(
        "SELECT players.id,firstname,lastname FROM players JOIN pokernowaliases ON players.id=player_id WHERE pokernow_name IN (%s) AND published='1'"
        % ",".join(["'" + x + "'" for x in pokernow_names]),
    )
    result = cursor.fetchone()
    if result is None:
        return None, None
    player_id, firstname, lastname = result
    return player_id, " ".join([firstname, lastname])


def _get_player_id_by_poker_now_id(cursor, poker_now_id: str) -> int:
    cursor.execute(
        "SELECT player_id FROM pokernowaliases WHERE pokernow_id = '%s'"
        % (poker_now_id)
    )
    result = cursor.fetchone()
    return None if result is None else result[0]


def _create_player(
    cursor,
    poker_now_id,
    poker_now_name,
    first_name=NEW_PLAYER_DEFAULT_FIRST_NAME,
    last_name=NEW_PLAYER_DEFAULT_LAST_NAME,
) -> str:
    cursor.execute(
        "INSERT INTO players (firstname,lastname) VALUES ('%s', '%s') RETURNING id"
        % (first_name, last_name)
    )
    player_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO pokernowaliases (player_id,pokernow_id,pokernow_name) VALUES ('%s','%s','%s') ON CONFLICT ON CONSTRAINT unique_rows DO NOTHING"
        % (player_id, poker_now_id, poker_now_name)
    )
    return player_id
