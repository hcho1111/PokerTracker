import dash
from dash import html, Input, Output, dcc, callback, State
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard, get_recent_ledgers, get_payout_report
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale
from datetime import datetime, timedelta, date
from api.players import get_top_offenders
from zoneinfo import ZoneInfo
import dash_daq as daq
from flask import request

dash.register_page(__name__, path="/payouts")


def user_on_mobile() -> bool:
    user_agent = request.headers.get("User-Agent")
    user_agent = user_agent.lower()
    phones = ["android", "iphone"]

    if any(x in user_agent for x in phones):
        return True
    return False


def create_venmo_deeplink(venmo, amount, comment):
    txn = "pay" if amount > 0 else "charge"
    if user_on_mobile():
        return (
            "venmo://paycharge?txn=pay&recipients=%s&note=%s&amount=%s&txn=%s&audience=private"
            % (venmo, comment, abs(amount), txn)
        )

    return (
        "https://account.venmo.com/pay?recipients=%s&note=%s&amount=%s&txn=%s&audience=private"
        % (venmo, comment, abs(amount), txn)
    )


# fbclid param ignored. Added from FB messenger.
def layout(ids, fbclid=""):
    return html.Div(
        [
            html.Div(
                [
                    html.H3("Payout Ledger"),
                    daq.PowerButton(
                        id="admin_mode_power_button",
                        on=False,
                        size=20,
                        color="#FF5E5E",
                        style={"marginLeft": "12px", "marginTop": "4px"},
                    ),
                    dbc.FormText(
                        "Admin mode",
                        color="secondary",
                        style={"marginLeft": "6px", "marginBottom": "4px"},
                    ),
                ],
                style={"display": "flex", "flexDirection": "row"},
            ),
            dbc.Table(
                id="payout_table",
                bordered=True,
                hover=True,
                responsive=True,
                style={"marginTop": "4px"},
            ),
            dcc.Store(id="payout_report_store", data=get_payout_report(ids.split(","))),
        ]
    )


@callback(
    Output("payout_table", "children"),
    Input("admin_mode_power_button", "on"),
    State("payout_report_store", "data"),
)
def update_table(admin_mode, data):
    leaderboard_rows, ledger_columns, ledger_table = data

    nets = [x[3] for x in leaderboard_rows]
    abs_max = max([abs(x[3]) for x in leaderboard_rows])
    discrete_colors = sample_colorscale(
        [
            [0, "rgb(197, 67, 60)"],  # Red
            [0.5, "rgb(255, 255, 255)"],  # White
            [1, "rgb(120, 166, 90)"],  # Green
        ],
        minmax_scale(nets + [-abs_max] + [abs_max]),
    )

    def generate_table_row(player_id):
        result = []
        for column in ledger_columns:
            ledger_id, _ = column
            value = ledger_table.get(ledger_id, {}).get(str(player_id), None)
            if value is None:
                result.append(html.Td())
            else:
                result.append(
                    html.Td("{:.2f}".format(value / 100), style={"textAlign": "end"})
                )
        return result

    def format_date(date_string):
        return (
            datetime.fromisoformat(date_string)
            .astimezone(ZoneInfo("America/New_York"))
            .strftime("%m/%d")
        )

    return [
        html.Thead(
            html.Tr(
                [html.Th("Player")]
                + ([html.Th("Venmo")] if admin_mode else [])
                + [html.Th("Total Net")]
                + [
                    html.Th(
                        dcc.Link(
                            format_date(x[1]),
                            href="https://www.pokernow.club/games/%s" % x[0],
                            target="_blank",
                        )
                    )
                    for x in ledger_columns
                ]
            )
        ),
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td("%s %s" % (x[1], x[2])),
                    ]
                    + (
                        [
                            html.Td(
                                (
                                    dcc.Link(
                                        "Venmo",
                                        href=create_venmo_deeplink(
                                            venmo=x[4],
                                            amount=x[3] / 100.0,
                                            comment="♠️♥️♣️♦️ for %s-%s"
                                            % (
                                                format_date(ledger_columns[0][1]),
                                                format_date(ledger_columns[-1][1]),
                                            ),
                                        ),
                                        target="_blank",
                                    )
                                    if x[4] != "None"
                                    else None
                                ),
                                style={"textAlign": "end"},
                            ),
                        ]
                        if admin_mode
                        else []
                    )
                    + [
                        html.Td(
                            html.B("{:.2f}".format(x[3] / 100)),
                            style={
                                "fontWeight": "bold",
                                "textAlign": "end",
                                "backgroundColor": discrete_colors[i],
                            },
                        ),
                    ]
                    + generate_table_row(x[0])
                )
                for i, x in enumerate(leaderboard_rows)
            ]
        ),
    ]
