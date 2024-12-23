import base64
import io

import pandas as pd

class LedgerPlayer:
  # Unique name/ID of the player
  name: str
  # Poker now IDs
  pokerNowIDs: str[]
  # Poker now names
  pokerNowNames: str[]
  # If populated, this is an unknown player that is new or needs merging
  suggestedNameMatch: str


MOCK_PLACEHOLDER_DB_TO_BE_DELETED = {

}

# Create a new ledger from a CSV file.
# Returns: the new ledger's ID, and a list of players with their verified match, or a suggested match based on user name
def new_ledger(filename:str, csv_raw: str) -> (str, LedgerPlayer[]):
  content_type, content_string = csv_raw.split(',')
  decoded = base64.b64decode(content_string)

  ledger_id = _get_ledger_id(filename)
  df = pd.read_csv(
      io.StringIO(decoded.decode('utf-8')))

  # TODO: post the ledger to a database



  return 'ledger_id'


def _get_ledger_id(filename: str):
  # Strip the 'ledger_' prefix
  ledger_id = filename.split('_')[-1]
  # Strip any other ' ' shennanagans (ie. ' (1)' from downloading multiple copies)
  ledger_id = ledger_id.split(' ')[0]
  # Strip the file extension '.csv'
  ledger_id = ledger_id.split('.')[0]
  return ledger_id
