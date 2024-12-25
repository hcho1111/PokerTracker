import base64
import io
import os
import logging
from typing import List
import psycopg2
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Connect to the database
connection = psycopg2.connect(
    user=USER, password=PASSWORD, host=HOST, port=PORT, dbname=DBNAME
)
connection.set_session(autocommit=True)
cursor = connection.cursor()


class LedgerPlayer:
    # Unique name/ID of the player
    name: str
    # Poker now IDs
    pokerNowIDs: List[str]  # Poker now names
    pokerNowNames: List[str]
    # If populated, this is an unknown player that is new or needs merging
    suggestedNameMatch: str


MOCK_PLACEHOLDER_DB_TO_BE_DELETED = {}


# Create a new ledger from a CSV file.
# Returns: the new ledger's ID, and a list of players with their verified match, or a suggested match based on user name
def new_ledger(filename: str, csv_raw: str) -> (str, List[LedgerPlayer]):
    content_type, content_string = csv_raw.split(",")
    decoded = base64.b64decode(content_string)

    ledger_id = _get_ledger_id(filename)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    session_start = str(pd.to_datetime(df["session_start_at"]).min())

    cursor.execute(
        "INSERT INTO ledgers (pokernow_ledger_id,session_start_at,published) VALUES ('%s','%s','0')"
        % (ledger_id, session_start)
    )

    for index, row in df.iterrows():
        player_id_or_none = _get_player_id_by_poker_now_id(row["player_id"])

    return ledger_id


def _get_ledger_id(file_name: str):
    # Strip the 'ledger_' prefix
    ledger_id = file_name.split("_")[-1]
    # Strip any other ' ' shennanagans (ie. ' (1)' from downloading multiple copies)
    ledger_id = ledger_id.split(" ")[0]
    # Strip the file extension '.csv'
    ledger_id = ledger_id.split(".")[0]
    return ledger_id


def _get_player_id_by_poker_now_id(poker_now_id: str) -> int:
    cursor.execute(
        "SELECT player_id FROM pokernowids WHERE pokernow_id = '%s'"
        % (poker_now_id)
    )
    result = cursor.fetchone()
    return None if result is None else result[0]


# def _create_player(poker_now_id, poker_now_name, first_name="New", last_name="Player") -> int:
#     cursor.execute("INSERT INTO players (firstname,lastname) VALUES ('%s', '%s') RETURNING id" & (first_name, last_name))
#     player_id = cursor.fetchone()[0]
#     cursor.execute("INSERT INTO pokernowids (player_id,pokernow_id) VALUES ('%s','%s')")
