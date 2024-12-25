from api.common import create_connection
from typing import List
import json

NEW_PLAYER_DEFAULT_FIRST_NAME = "New"
NEW_PLAYER_DEFAULT_LAST_NAME = "Player"


# Player that is either new (needs name to be updated) or needs merging with an existing player.
class UnresolvedPlayer:
    player_id: int
    # pokernow_names: List[str]
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
        return UnresolvedPlayer(**data)


def get_unresolved_players():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM players WHERE firstname='%s' and lastname='%s'"
            % (NEW_PLAYER_DEFAULT_FIRST_NAME, NEW_PLAYER_DEFAULT_LAST_NAME)
        )
        unresolved_players = []
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
            unresolved_players.append(
                UnresolvedPlayer(
                    player_id,
                    pokernow_names,
                    suggested_player_id,
                    suggested_pokernow_name,
                )
            )
        return unresolved_players


def _find_suggestion(cursor, pokernow_names: List[str]) -> (str, str):
    if len(pokernow_names) == 0:
        return None, None
    cursor.execute(
        "SELECT players.id,pokernow_name FROM players JOIN pokernowaliases ON players.id=player_id WHERE pokernow_name IN (%s)"
        % ",".join(["'" + x + "'" for x in pokernow_names]),
    )
    result = cursor.fetchone()
    if result is None:
        return None, None
    player_id, pokernow_name = result
    return player_id, pokernow_name


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
