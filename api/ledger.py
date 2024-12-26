import base64
import io
import logging
from typing import List
import pandas as pd
from api.players import _get_player_id_by_poker_now_id, _create_player
from api.common import create_connection
from numpy import nan


# Create a new ledger from a CSV file.
# Returns: the new ledger's ID, and a list of players with their verified match, or a suggested match based on user name
def new_ledger(filename: str, csv_raw: str):
    content_type, content_string = csv_raw.split(",")
    decoded = base64.b64decode(content_string)

    ledger_id = _get_ledger_id(filename)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    session_start = str(pd.to_datetime(df["session_start_at"]).min())

    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO ledgers (pokernow_ledger_id,session_start_at,published) VALUES ('%s','%s','0')"
            % (ledger_id, session_start)
        )

        for index, row in df.iterrows():
            player_id = _get_player_id_by_poker_now_id(cursor, row["player_id"])
            if player_id is None:
                player_id = _create_player(
                    cursor, row["player_id"], row["player_nickname"]
                )
            _create_ledger_row(
                cursor,
                ledger_id,
                player_id,
                row["session_start_at"],
                row["buy_in"],
                row["stack"],
            )
    return ledger_id


def _get_ledger_id(file_name: str):
    # Strip the 'ledger_' prefix
    ledger_id = file_name[7:]
    # Strip any other ' ' shennanagans (ie. ' (1)' from downloading multiple copies)
    ledger_id = ledger_id.split(" ")[0]
    # Strip the file extension '.csv'
    ledger_id = ledger_id.split(".")[0]
    return ledger_id


def _create_ledger_row(
    cursor,
    pokernow_ledger_id: str,
    player_id: str,
    session_start: str,
    buy_in: int,
    stack: int,
):
    parsed_session_start = (
        ("'" + str(session_start) + "'") if (str(session_start) != "nan") else "NULL"
    )
    cursor.execute(
        "INSERT INTO ledgerrows (pokernow_ledger_id,player_id,session_start,buy_in,stack) VALUES ('%s','%s',%s,'%s','%s')"
        % (pokernow_ledger_id, player_id, parsed_session_start, buy_in, stack)
    )
