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
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server

app.layout = html.Div(
    [
        html.H1("casino pokernow"),
        html.Div(
            [
                html.Div(dcc.Link(f"{page['name']}", href=page["relative_path"]))
                for page in dash.page_registry.values()
            ]
        ),
        dash.page_container,
    ]
)


if __name__ == "__main__":
    app.run(debug=not IS_PROD)
