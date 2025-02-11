import dash
from dash import dcc, html, Input, Output, callback, State, MATCH, ALL, ctx
import dash_bootstrap_components as dbc
import hashlib
import os
from api.ledger import (
    new_ledger,
    new_ledger_from_bytes,
    get_payout_report,
    get_unpaid_ledgers_count,
    get_unpaid_ledgers_ids,
    mark_unpaid_ledgers_as_paid,
)
from api.players import (
    get_unpublished_players,
    UnpublishedPlayer,
    publish_player,
    get_published_players,
    merge_player,
)
from jobs import ledgers
import json
from dash.exceptions import PreventUpdate

PASSWORD_SHA512_HASH = "e09ae4f8c4448c14043ccd599af1285655960e2d200aa3e24f6b3d3626eefc3469c0faf0cd5688bee373f7251148f18a158905ed74cff7461248a8531255750e"
IS_PROD = os.getenv("env") == "prod"

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


def get_payout_status():
    count, start_date, end_date = get_unpaid_ledgers_count()
    if count == 0:
        return "All paid"
    return "%s unpaid ledger(s), (%s - %s)" % (
        count,
        start_date.strftime("%m/%d/%y"),
        end_date.strftime("%m/%d/%y"),
    )


def get_authed_content():
    return html.Div(
        [
            dbc.Card(
                [
                    html.H3("Upload new ledger (.csv)"),
                    dcc.Upload(
                        id="ledger_upload",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select Files")]
                        ),
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
                    dbc.Label("Pokernow Link"),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    type="url", id="url_field", placeholder="Enter URL"
                                ),
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Submit", color="primary", id="url_field_submit"
                                )
                            ),
                        ],
                        style={"width": "50%"},
                    ),
                ]
            ),
            dbc.Card(
                [
                    html.Div(
                        [
                            html.H3(
                                "Add or Merge Players", style={"marginBottom": "0"}
                            ),
                            dbc.Button(
                                "Refresh",
                                color="secondary",
                                id="unpublished_players_refresh",
                                outline=True,
                                size="sm",
                                style={"marginLeft": "12px"},
                            ),
                        ],
                        style={
                            "flexDirection": "row",
                            "display": "flex",
                            "marginBottom": "20px",
                        },
                    ),
                    html.Div(id="unpublished_players"),
                ],
                style={"marginTop": "12px"},
            ),
            dbc.Card(
                [
                    html.Div(
                        [
                            html.H3("Payout report", style={"marginBottom": "0"}),
                            dcc.Link(
                                "Create new",
                                target="_blank",
                                href=get_payout_report_href(),
                                style={"marginTop": "8px", "marginLeft": "8px"},
                            ),
                        ],
                        style={
                            "flexDirection": "row",
                            "display": "flex",
                            "marginBottom": "12px",
                        },
                    ),
                    html.B(get_payout_status()),
                    dbc.Button(
                        "Mark all as paid",
                        color="secondary",
                        id="payout_button",
                        outline=True,
                        style={"width": "200px", "marginTop": "8px"},
                    ),
                ],
                style={"marginTop": "20px"},
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Please confirm")),
                    dbc.ModalBody("Are you sho about that"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Yes",
                            id="payout_button_confirm",
                        )
                    ),
                ],
                id="payout_confirm_modal",
                size="sm",
                is_open=False,
                centered=True,
            ),
            dcc.Store(id="unpublished_players_store"),
            dcc.Store(id="merge_player_selection"),
        ]
    )


def layout():
    return html.Div(
        [
            html.H2("Admin page"),
            password_input,
            html.Div(id="root"),
            dcc.ConfirmDialog(id="error_dialog"),
        ]
    )


@callback(
    Output("payout_confirm_modal", "is_open"),
    Input("payout_button", "n_clicks"),
    Input("payout_button_confirm", "n_clicks"),
)
def update_payout_confirm_modal(a, b):
    button_clicked = ctx.triggered_id
    if button_clicked == "payout_button":
        return True
    if button_clicked == "payout_button_confirm":
        mark_unpaid_ledgers_as_paid()
    return False


def get_payout_report_href():
    return "/payouts?ids=%s" % get_unpaid_ledgers_ids()


@callback(
    Output(component_id="root", component_property="children"),
    Output(component_id="password_input", component_property="style"),
    Output(component_id="password_submit", component_property="style"),
    State(component_id="password_input", component_property="value"),
    Input(component_id="password_submit", component_property="n_clicks"),
)
def on_password_submit(password, submit_n_clicks):
    authed_content = (
        html.Div(id="authed_content"),
        {"display": "none"},
        {"display": "none"},
    )
    if not IS_PROD:
        return authed_content
    if password is None:
        return [], {}, {}
    if hashlib.sha512(password.encode()).hexdigest() == PASSWORD_SHA512_HASH:
        return authed_content
    return wrong_password, {}, {}


@callback(
    Output(component_id="authed_content", component_property="children"),
    Input(component_id="root", component_property="children"),
)
def update_authed_content(a):
    return get_authed_content()


@callback(
    Output(component_id="error_dialog", component_property="displayed"),
    Output(component_id="error_dialog", component_property="message"),
    Input(component_id="ledger_upload", component_property="contents"),
    Input(component_id="url_field_submit", component_property="n_clicks"),
    State(component_id="ledger_upload", component_property="filename"),
    State(component_id="url_field", component_property="value"),
)
def on_ledger_upload(contents, n_clicks, filename, url):
    try:
        if contents is not None:
            new_ledger_from_bytes(filename, contents)
            return True, "Success"
        if url:
            file_path = ledgers.download_ledger(url, "/tmp")
            with open(file_path) as f:
                new_ledger(os.path.basename(file_path), f.read())
            return True, "Success"
    except Exception as error:
        return True, str(error)

    return False, ""


@callback(
    Output(component_id="unpublished_players_store", component_property="data"),
    Input(component_id="unpublished_players_refresh", component_property="n_clicks"),
    Input(
        component_id={"type": "create_new_player_modal", "index": ALL},
        component_property="is_open",
    ),
    Input(
        component_id={"type": "merge_player_modal", "index": ALL},
        component_property="is_open",
    ),
    Input(component_id="error_dialog", component_property="displayed"),
    State(component_id="unpublished_players_store", component_property="data"),
)
def on_unpublished_players_refresh(
    n_clicks, create_models_open, merge_models_open, dialog_displayed, previous
):
    # Refresh after closing modals.
    if len(create_models_open) != 0 and any(create_models_open):
        raise PreventUpdate
    if len(merge_models_open) != 0 and any(merge_models_open):
        raise PreventUpdate

    return json.dumps([x.to_json() for x in get_unpublished_players()])


@callback(
    Output(component_id="unpublished_players", component_property="children"),
    Input(component_id="unpublished_players_store", component_property="data"),
)
def update_unpublished_players(data):
    if data is None:
        return []
    unpublished_players_dicts = json.loads(data)
    unpublished_players = [
        UnpublishedPlayer.from_json(x) for x in unpublished_players_dicts
    ]
    return [
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.B(", ".join(x.pokernow_names))),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        "Merge with a player",
                                        id={
                                            "type": "merge_player_button",
                                            "index": i,
                                        },
                                    ),
                                    (
                                        html.Div(
                                            [
                                                html.B("Suggestion found:"),
                                                html.B(x.merge_suggestion_name),
                                            ],
                                            style={
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "marginLeft": "10px",
                                            },
                                        )
                                        if x.merge_suggestion_name
                                        else None
                                    ),
                                ],
                                style={"display": "flex", "flexDirection": "row"},
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Create new player",
                                color="primary",
                                id={
                                    "type": "create_new_player_button",
                                    "index": x.player_id,
                                },
                            )
                        ),
                    ]
                ),
                html.Hr(),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle(
                                "Creating a new player for "
                                + ", ".join(x.pokernow_names)
                            )
                        ),
                        dbc.ModalBody(
                            id="create_new_player_model_content",
                            children=[
                                html.B(),
                                dbc.Form(
                                    [
                                        html.Div(
                                            [
                                                dbc.Label("First name"),
                                                dbc.Input(
                                                    type="text",
                                                    id={
                                                        "type": "new_player_first_name_field",
                                                        "index": x.player_id,
                                                    },
                                                    placeholder="Required",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                dbc.Label("Last name"),
                                                dbc.Input(
                                                    type="text",
                                                    id={
                                                        "type": "new_player_last_name_field",
                                                        "index": x.player_id,
                                                    },
                                                    placeholder="Required",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(
                                            [
                                                dbc.Label("Venmo"),
                                                dbc.Input(
                                                    type="text",
                                                    id={
                                                        "type": "new_player_venmo_field",
                                                        "index": x.player_id,
                                                    },
                                                    placeholder="Optional",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Submit",
                                id={"type": "new_player_submit", "index": x.player_id},
                            )
                        ),
                    ],
                    id={"type": "create_new_player_modal", "index": x.player_id},
                    size="lg",
                    is_open=False,
                    centered=True,
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle("Merging " + ", ".join(x.pokernow_names))
                        ),
                        dbc.ModalBody(
                            id={
                                "type": "merge_player_modal_content",
                                "index": i,
                            }
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Submit",
                                id={
                                    "type": "merge_player_submit",
                                    "index": i,
                                },
                            )
                        ),
                    ],
                    id={"type": "merge_player_modal", "index": i},
                    size="lg",
                    is_open=False,
                    centered=True,
                ),
            ]
        )
        for i, x in enumerate(unpublished_players)
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
    Input(
        component_id={"type": "new_player_submit", "index": MATCH},
        component_property="n_clicks",
    ),
    State(
        component_id={"type": "create_new_player_button", "index": MATCH},
        component_property="id",
    ),
    State(
        component_id={"type": "create_new_player_modal", "index": MATCH},
        component_property="is_open",
    ),
    State(
        component_id={"type": "new_player_first_name_field", "index": MATCH},
        component_property="value",
    ),
    State(
        component_id={"type": "new_player_last_name_field", "index": MATCH},
        component_property="value",
    ),
    State(
        component_id={"type": "new_player_venmo_field", "index": MATCH},
        component_property="value",
    ),
)
def update_create_new_player_modal(
    n_clicks, submit_n_clicks, button_id, is_open, first_name, last_name, venmo
):
    if n_clicks is None or n_clicks == 0:
        return False
    if not is_open:
        return True
    publish_player(button_id["index"], first_name, last_name, venmo)
    return False


@callback(
    Output(
        component_id={"type": "merge_player_modal", "index": MATCH},
        component_property="is_open",
    ),
    Output(
        component_id={"type": "merge_player_modal_content", "index": MATCH},
        component_property="children",
    ),
    Input(
        component_id={"type": "merge_player_button", "index": MATCH},
        component_property="n_clicks",
    ),
    Input(
        component_id={"type": "merge_player_submit", "index": MATCH},
        component_property="n_clicks",
    ),
    State(
        component_id={"type": "merge_player_modal", "index": MATCH},
        component_property="is_open",
    ),
    State(
        component_id={"type": "merge_player_button", "index": MATCH},
        component_property="id",
    ),
    State(component_id="unpublished_players_store", component_property="data"),
    State(component_id="merge_player_selection", component_property="data"),
)
def update_merge_player_modal(
    n_clicks, submit_n_clicks, is_open, merge_player_button_id, data, selection
):
    if n_clicks is None or n_clicks == 0:
        return False, []

    unpublished_players_dicts = json.loads(data)
    unpublished_players = [
        UnpublishedPlayer.from_json(x) for x in unpublished_players_dicts
    ]
    target_unpublished_players = unpublished_players[merge_player_button_id["index"]]
    suggested_player_id = target_unpublished_players.merge_suggestion_player_id

    if not is_open:
        published_players = get_published_players()
        return True, [
            dbc.Form(
                [
                    html.Div(
                        [
                            dbc.Label("Merge with"),
                            dbc.Select(
                                id="merge_player_select",
                                options=[
                                    {"label": " ".join([x[0], x[1]]), "value": x[2]}
                                    for x in published_players
                                ],
                                value=(
                                    suggested_player_id
                                    if suggested_player_id is not None
                                    else published_players[0][2]
                                ),
                            ),
                        ],
                        className="mb-3",
                    )
                ]
            ),
        ]
    merge_player(target_unpublished_players.player_id, selection)
    return False, []


@callback(
    Output(component_id="merge_player_selection", component_property="data"),
    Input(component_id="merge_player_select", component_property="value"),
)
def update_merge_player_selection(value):
    return value
