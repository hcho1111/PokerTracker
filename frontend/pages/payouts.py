import dash
from dash import html, Input, Output, dcc, callback, State
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard, get_recent_ledgers, get_payout_report
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale
from datetime import datetime, timedelta, date
from api.players import get_top_offenders

dash.register_page(__name__, path="/payouts")


def layout(ids):
    leaderboard_rows, ledger_columns, ledger_table = get_payout_report(ids.split(","))

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
    print()

    def generate_table_row(player_id):
        result = []
        for column in ledger_columns:
            ledger_id, _ = column
            value = ledger_table.get(ledger_id, {}).get(player_id, None)
            if value is None:
                result.append(html.Td())
            else:
                result.append(
                    html.Td("{:.2f}".format(value / 100), style={"textAlign": "end"})
                )
        return result

    return html.Div(
        [
            html.H3("Payout Ledger"),
            dbc.Table(
                bordered=True,
                hover=True,
                responsive=True,
                style={"marginTop": "4px"},
                children=[
                    html.Thead(
                        html.Tr(
                            [html.Th("Player"), html.Th("Venmo"), html.Th("Total Net")]
                            + [
                                html.Th(
                                    dcc.Link(
                                        x[1].strftime("%m/%d"),
                                        href="https://www.pokernow.club/games/%s"
                                        % x[0],
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
                                    html.Td(
                                        (
                                            dcc.Clipboard(
                                                content=x[4],
                                                title="copy",
                                                style={
                                                    "fontSize": 16,
                                                },
                                            )
                                            if x[4] != "None"
                                            else None
                                        ),
                                        style={"textAlign": "end"},
                                    ),
                                    html.Td(
                                        html.Div(
                                            [
                                                dcc.Clipboard(
                                                    target_id="net_%s" % i,
                                                    style={
                                                        "fontSize": 16,
                                                        "display": "inline",
                                                    },
                                                ),
                                                html.B(
                                                    "{:.2f}".format(x[3] / 100),
                                                    id="net_%s" % i,
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "flexDirection": "row",
                                                "justifyContent": "space-between",
                                            },
                                        ),
                                        style={
                                            "fontWeight": "bold",
                                            "backgroundColor": discrete_colors[i],
                                        },
                                    ),
                                ]
                                + generate_table_row(x[0])
                            )
                            for i, x in enumerate(leaderboard_rows)
                        ]
                    ),
                ],
            ),
        ]
    )
