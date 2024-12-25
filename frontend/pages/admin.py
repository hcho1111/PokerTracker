import dash
from dash import dcc, html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import hashlib
from api.ledger import new_ledger
from api.players import get_unresolved_players

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

upload_input = html.Div(
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
        html.H3("Add or Merge Players"),
        dbc.Button("Refresh", color="primary", id="unresolved_players_refresh"),
        html.Div(id="unresolved_players"),
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
    return upload_input


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
  Output(component_id="unresolved_players", component_property="children"),
  Input(component_id="unresolved_players_refresh", component_property="n_clicks"))
def on_testing_clicked(n_clicks):
  unresolved_players = get_unresolved_players()
  return [
    dbc.Row([dbc.Col(
      html.B(", ".join(x.pokernow_names))
    )]) for x in unresolved_players
  ]
