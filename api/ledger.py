import base64
import io
import logging
from typing import List
import pandas as pd
from api.players import _get_player_id_by_poker_now_id, _create_player
from api.common import create_connection
from numpy import nan
from datetime import date, timedelta


def new_ledger_from_bytes(filename: str, csv_raw: str):
    content_type, content_string = csv_raw.split(",")
    csv_decoded = base64.b64decode(content_string).decode("utf-8")
    return new_ledger(filename, csv_decoded)


# Create a new ledger from a CSV file.
# Returns: the new ledger's ID, and a list of players with their verified match, or a suggested match based on user name
def new_ledger(filename: str, csv: str):
    ledger_id = _get_ledger_id(filename)
    df = pd.read_csv(io.StringIO(csv))
    session_start = str(pd.to_datetime(df["session_start_at"]).min())

    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO ledgers (pokernow_ledger_id,session_start_at) VALUES ('%s','%s')"
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
                row["net"],
            )
    return ledger_id


def get_leaderboard(by_date="2020-01-01", to_date=date.today() + timedelta(days=100)):
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
                SELECT firstname,lastname,SUM(net) as total_net, COUNT(DISTINCT(pokernow_ledger_id)),players.id
                FROM ledgerrows
                INNER JOIN players
                    ON players.id = ledgerrows.player_id and is_ledger_published(pokernow_ledger_id)
                WHERE ledgerrows.session_start > '%s'::date AND ledgerrows.session_start < '%s'::date
                GROUP BY firstname, lastname, players.id
                ORDER BY total_net DESC;
            """
            % (by_date, to_date)
        )
        leaderboard = cursor.fetchall()
        cursor.execute(
            """
                SELECT count(*), min(session_start_at), max(session_start_at) FROM ledgers
                WHERE is_ledger_published(pokernow_ledger_id) AND session_start_at > '%s'::date AND session_start_at < '%s'::date
            """
            % (by_date, to_date)
        )
        n_ledgers, start_date, stop_date = cursor.fetchone()
        return leaderboard, n_ledgers, start_date, stop_date


def get_recent_ledgers():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
                SELECT pokernow_ledger_id, session_start_at,
                    winner.first_names as winner_first_names, winner.last_names as winner_last_names, winner.net as winner_net,
                    fish.first_names as fish_first_names, fish.last_names as fish_last_names, fish.net as fish_net,
                    paid_out
                FROM ledgers,
                LATERAL get_ledger_winner(pokernow_ledger_id) winner, 
                LATERAL get_ledger_fish(pokernow_ledger_id) fish
                WHERE is_ledger_published(pokernow_ledger_id)
                ORDER BY session_start_at DESC
                LIMIT 15;
            """
        )
        return cursor.fetchall()


def get_unpaid_ledgers_count():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT count(*), min(session_start_at), max(session_start_at) FROM ledgers WHERE paid_out='0' AND is_ledger_published(pokernow_ledger_id)"
        )
        return cursor.fetchone()


def get_unpaid_ledgers_ids():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT string_agg(pokernow_ledger_id, ',') FROM ledgers WHERE paid_out='0' AND is_ledger_published(pokernow_ledger_id)"
        )
        return cursor.fetchone()


def mark_unpaid_ledgers_as_paid():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE ledgers SET paid_out='1' WHERE paid_out='0' AND is_ledger_published(pokernow_ledger_id)"
        )


def get_payout_report(ledger_ids: List[str]):
    with create_connection() as connection:
        cursor = connection.cursor()
        ledger_ids_string = ",".join(["'%s'" % x for x in ledger_ids])
        cursor.execute(
            """
                SELECT pokernow_ledger_id, session_start_at, player_id, net, firstname, lastname
                FROM ledgers,
                LATERAL get_ledger_net(pokernow_ledger_id) ledger_net
                WHERE pokernow_ledger_id IN (%s)
                GROUP BY pokernow_ledger_id, player_id, net, firstname, lastname
                ORDER BY session_start_at;
            """
            % (ledger_ids_string)
        )
        data = cursor.fetchall()

        cursor.execute(
            """
                SELECT player_id, firstname, lastname, sum(net), venmo
                FROM ledgerrows
                INNER JOIN players ON players.id = player_id
                WHERE pokernow_ledger_id IN (%s)
                GROUP BY player_id, firstname, lastname, venmo
                ORDER BY sum DESC;
            """
            % (ledger_ids_string)
        )
        leaderboard_rows = cursor.fetchall()

        # Create sorted list of (ledger_id, start_dates)
        ledger_columns = []

        # Create mapping of ledger_ids to player_id to net
        ledger_table = {}

        for row in data:
            ledger_id, date, player_id, net, firstname, lastname = row
            if ledger_id not in ledger_table:
                ledger_table[ledger_id] = {}
            if player_id not in ledger_table[ledger_id]:
                ledger_table[ledger_id][player_id] = {}
            ledger_table[ledger_id][player_id] = net

            if not ledger_columns or ledger_columns[-1][0] != ledger_id:
                ledger_columns.append((ledger_id, date))

        return leaderboard_rows, ledger_columns, ledger_table


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
    net: int,
):
    parsed_session_start = (
        ("'" + str(session_start) + "'") if (str(session_start) != "nan") else "NULL"
    )
    cursor.execute(
        "INSERT INTO ledgerrows (pokernow_ledger_id,player_id,session_start,buy_in,net) VALUES ('%s','%s',%s,'%s','%s')"
        % (pokernow_ledger_id, player_id, parsed_session_start, buy_in, net)
    )


def get_net_over_time_data():
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT CONCAT(players.firstname, ' ', players.lastname) as name, f.date, f.RunningTotal
            FROM players,
            LATERAL get_cum_sum(players.id) f
            ORDER BY f.date
        """
        )
        return cursor.fetchall()


def get_cum_sums(player_ids):
    with create_connection() as connection:
        cursor = connection.cursor()
        result = []
        for player_id in player_ids:
            cursor.execute(
                """
                SELECT * FROM get_cum_sum(%s)
                """
                % player_id
            )
            result.append(cursor.fetchall())
        return result
