import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import os
from flask_restful import Resource, Api
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from api.ledger import new_ledger
from psycopg2.errors import UniqueViolation
import plotly.io as pio

UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {"csv"}
IS_PROD = os.getenv("env") == "prod"

server = Flask(__name__)
server.secret_key = os.getenv("secret_key")
server.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app = Dash(
    server=server,
    use_pages=True,
    pages_folder="frontend/pages",
    assets_folder="frontend/assets",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
api = Api(server)

pio.templates.default = "plotly_white"


def serve_layout():
    return html.Div(
        [
            html.H1("pokernow tracker", style={"marginBottom": "30px"}),
            dash.page_container,
        ],
        style={"padding": "30px"},
    )


app.layout = serve_layout


@server.route("/uploadledger", methods=["POST"])
def upload_ledger():
    def allowed_file(filename):
        if "." not in filename:
            return False
        [name, extenstion] = filename.rsplit(".", 1)
        return (
            name.find("ledger_") == 0
            and len(name) == 32
            and extenstion.lower() in ALLOWED_EXTENSIONS
        )

    if "file" not in request.files:
        return "no file"
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(server.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        try:
            with open(filepath) as f:
                return "success: %s" % new_ledger(filename, f.read())
        except UniqueViolation:
            return "duplicate key"
    return "failure"


if __name__ == "__main__":
    server.run(debug=not IS_PROD, threaded=True)
