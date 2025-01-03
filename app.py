import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
IS_PROD = os.getenv("env") == "prod"

app = Dash(
    __name__,
    use_pages=True,
    pages_folder="frontend/pages",
    assets_folder="frontend/assets",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server


def serve_layout():
    return html.Div(
        [
            html.H1("pokernow tracker", style={"marginBottom": "30px"}),
            dash.page_container,
        ],
        style={"padding": "30px"},
    )


app.layout = serve_layout

if __name__ == "__main__":
    app.run(debug=not IS_PROD)
