import dash
from dash import dcc, html, Input, Output, callback, State, MATCH
import dash_bootstrap_components as dbc
import hashlib
from api.ledger import new_ledger
from api.players import get_unresolved_players, UnresolvedPlayer
import json

PASSWORD_SHA512_HASH = "e09ae4f8c4448c14043ccd599af1285655960e2d200aa3e24f6b3d3626eefc3469c0faf0cd5688bee373f7251148f18a158905ed74cff7461248a8531255750e"

dash.register_page(__name__, path="/admin")

password_input = dbc.Row(
    [
        dbc.Col(
            dbc.Input(
                id="password_input", placeholder="Admin password", type="password"
            )
        ),
        dbc.Col(dbc.Button("Submit", color="primary", id="password_submit")),
    ]
)

wrong_password = html.B("Wrong password")

authed_content = html.Div(
    [
        html.H3("Upload new ledger (.csv)"),
        dcc.Upload(
            id="ledger_upload",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "50%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
        ),
        html.Div(
            [
                html.H3("Add or Merge Players", style={"marginBottom": "0"}),
                dbc.Button(
                    "Refresh",
                    color="secondary",
                    id="unresolved_players_refresh",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "20px"},
                ),
            ],
            style={"flexDirection": "row", "display": "flex", "marginBottom": "20px"},
        ),
        html.Div(id="unresolved_players"),
        dcc.Store(id="unresolved_players_store"),
    ]
)

layout = html.Div(
    [
        html.H2("Admin page"),
        password_input,
        html.Div(id="root"),
        dcc.ConfirmDialog(id="error_dialog"),
    ]
)


@callback(
    Output(component_id="root", component_property="children"),
    Output(component_id="password_input", component_property="style"),
    Output(component_id="password_submit", component_property="style"),
    State(component_id="password_input", component_property="value"),
    Input(component_id="password_submit", component_property="n_clicks"),
)
def on_password_submit(password, submit_n_clicks):
    if password is None:
        return html.Div(id="authed_content"), {"display": "none"}, {"display": "none"}
    if hashlib.sha512(password.encode()).hexdigest() == PASSWORD_SHA512_HASH:
        return html.Div(id="authed_content"), {"display": "none"}, {"display": "none"}
    return wrong_password, {}, {}


@callback(
    Output(component_id="authed_content", component_property="children"),
    Input(component_id="root", component_property="children"),
)
def update_authed_content(a):
    return authed_content


@callback(
    Output(component_id="error_dialog", component_property="displayed"),
    Output(component_id="error_dialog", component_property="message"),
    Input(component_id="ledger_upload", component_property="contents"),
    State(component_id="ledger_upload", component_property="filename"),
)
def on_ledger_upload(contents, filename):
    if contents is not None:
        try:
            new_ledger(filename, contents)
            return False, ""
        except Exception as error:
            return True, str(error)
    return False, ""


@callback(
    Output(component_id="unresolved_players_store", component_property="data"),
    Input(component_id="unresolved_players_refresh", component_property="n_clicks"),
)
def on_unresolved_players_refresh(n_clicks):
    return json.dumps([x.to_json() for x in get_unresolved_players()])


@callback(
    Output(component_id="unresolved_players", component_property="children"),
    Input(component_id="unresolved_players_store", component_property="data"),
)
def update_unresolved_players(data):
    if data is None:
        return []
    unresolved_players_dicts = json.loads(data)
    unresolved_players = [
        UnresolvedPlayer.from_json(x) for x in unresolved_players_dicts
    ]
    return [
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.B(", ".join(x.pokernow_names))),
                        dbc.Col(
                            dbc.Button(
                                "Create new player",
                                id={"type": "create_new_player_button", "index": i},
                            )
                        ),
                        dbc.Col(
                            dbc.Button("Merge with a player", id="merge_player_%s" % i)
                        ),
                    ]
                ),
                html.Hr(),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Create a new player")),
                        dbc.ModalBody(id="create_new_player_model_content"),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Cancel", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id={"type": "create_new_player_model", "index": i},
                    size="lg",
                    is_open=False,
                    centered=True,
                ),
            ]
        )
        for i, x in enumerate(unresolved_players)
    ]


@callback(
    Output(
        component_id={"type": "create_new_player_modal", "index": MATCH},
        component_property="is_open",
    ),
    Input(
        component_id={"type": "create_new_player_button", "index": MATCH},
        component_property="n_clicks",
    ),
    State(
        component_id={"type": "create_new_player_button", "index": MATCH},
        component_property="id",
    ),
)
def update_create_new_player_model(n_clicks, id):
    return True
