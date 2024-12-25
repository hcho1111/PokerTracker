import os
import psycopg2

_DB_USER = os.getenv("user")
_DB_PASSWORD = os.getenv("password")
_DB_HOST = os.getenv("host")
_DB_PORT = os.getenv("port")
_DB_NAME = os.getenv("dbname")


def create_connection():
    return psycopg2.connect(
        user=_DB_USER,
        password=_DB_PASSWORD,
        host=_DB_HOST,
        port=_DB_PORT,
        dbname=_DB_NAME,
    )
