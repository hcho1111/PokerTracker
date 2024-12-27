import dash
from dash import html, Input, Output, dcc, callback
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard, get_recent_ledgers
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale
from datetime import datetime, timedelta
from api.players import get_top_offenders

dash.register_page(__name__, path="/")

leaderboard_card = dbc.Card(
    [
        html.H3("Leaderboard 📈"),
        html.Div(
            [
                dbc.RadioItems(
                    id="leaderboard_time_range",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "All Time", "value": None},
                        {"label": "1w", "value": 7},
                        {"label": "1m", "value": 30},
                        {"label": "3m", "value": 90},
                        {"label": "1y", "value": 365},
                    ],
                    value=None,
                ),
            ],
            className="radio-group",
        ),
        dbc.FormText(
            id="leaderboard_subtitle", color="secondary", style={"marginBottom": "8px"}
        ),
        dbc.Table(
            id="leaderboard_table",
            bordered=True,
            hover=True,
            responsive=True,
            style={"marginTop": "8px"},
        ),
    ],
)


def get_top_username_counts():
    return [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(x[0] + " " + x[1]),
                        html.Td(x[2]),
                    ]
                )
                for i, x in enumerate(get_top_offenders())
            ]
        )
    ]


top_username_count_card = dbc.Card(
    [
        html.H3("User IDs Count - Top Offenders 😠"),
        dbc.FormText(
            "(Please make a pokernow account to make paying out easier, especially you Ming!)",
            color="secondary",
            style={"marginTop": "-8px"},
        ),
        dbc.Table(
            id="top_username_count_card",
            children=get_top_username_counts(),
            bordered=True,
            hover=True,
            responsive=True,
            style={"marginTop": "16px"},
        ),
    ]
)


def get_recent_ledgers_children():
    data = get_recent_ledgers()
    merged_nets = [x[4] for x in data] + [x[7] for x in data]
    abs_max = max([abs(x) for x in merged_nets])
    discrete_colors = sample_colorscale(
        [
            [0, "rgb(197, 67, 60)"],  # Red
            [0.5, "rgb(255, 255, 255)"],  # White
            [1, "rgb(120, 166, 90)"],  # Green
        ],
        minmax_scale(merged_nets + [-abs_max] + [abs_max]),
    )

    return [html.Thead(html.Tr([html.Th("Date"), html.Th("🦈 Shark"), html.Th("Net"), html.Th("🐟 Fish"), html.Th("Net")]))] + [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            dcc.Link(
                                x[1].strftime("%m/%d"),
                                target="_blank",
                                href="https://www.pokernow.club/games/%s" % x[0],
                            )
                        ),
                                         html.Td(", ".join([
                            "%s %s" % (first, last) for first, last in zip(x[2].split(', '), x[3].split(', '))])),
                        html.Td(
                            "{:.2f}".format(x[4] / 100),
                            style={
                                "textAlign": "end",
                                "backgroundColor": discrete_colors[i],
                            },
                        ),
                        html.Td(", ".join([
                            "%s %s" % (first, last) for first, last in zip(x[5].split(', '), x[6].split(', '))])),
                        html.Td(
                            "{:.2f}".format(x[7] / 100),
                            style={
                                "textAlign": "end",
                                "backgroundColor": discrete_colors[i + len(data)],
                            },
                        ),
                    ]
                )
                for i, x in enumerate(data)
            ]
        )
    ]


recent_ledgers_card = dbc.Card(
    [
        html.H3("Recent Ledgers ⏰"),
        dbc.Table(
            id="recent_ledgers",
            children=get_recent_ledgers_children(),
            bordered=True,
            hover=True,
            responsive=True,
            style={"marginTop": "8px"},
        ),
    ]
)

layout = dbc.Row(
    [
        dbc.Col([dbc.Row(children=[leaderboard_card])], md=6),
        dbc.Col(
            [
                dbc.Row(children=[recent_ledgers_card]),
                dbc.Row(
                    children=[top_username_count_card], style={"marginTop": "24px"}
                ),
            ],
            md=6,
        ),
        dcc.Store(id="leaderboard_store"),
    ],
    className="g-5",
)


@callback(Output("leaderboard_store", "data"), Input("leaderboard_time_range", "value"))
def update_leaderboard_store(value):
    return get_leaderboard(
        "2020-01-01"
        if value is None
        else (datetime.now() - timedelta(days=value)).isoformat()
    )


@callback(Output("leaderboard_table", "children"), Input("leaderboard_store", "data"))
def update_leaderboard_table(leaderboard_store):
    data, _, _, _ = leaderboard_store
    abs_max = max([abs(x[2]) for x in data])
    nets = [-abs_max] + [x[2] for x in data] + [abs_max]
    discrete_colors = sample_colorscale(
        [
            [0, "rgb(197, 67, 60)"],  # Red
            [0.5, "rgb(255, 255, 255)"],  # White
            [1, "rgb(120, 166, 90)"],  # Green
        ],
        minmax_scale(nets),
    )

    return [
        html.Thead(html.Tr([html.Th("Player"), html.Th("Games"), html.Th("Net")]))
    ] + [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(x[0] + " " + x[1]),
                        html.Td(str(x[3])),
                        html.Td(
                            "{:.2f}".format(x[2] / 100),
                            style={
                                "textAlign": "end",
                                "backgroundColor": discrete_colors[i + 1],
                            },
                        ),
                    ]
                )
                for i, x in enumerate(data)
            ]
        )
    ]


@callback(
    Output("leaderboard_subtitle", "children"), Input("leaderboard_store", "data")
)
def update_leaderboard_subtitle(leaderboard_store):
    _, n_ledgers, start_date, end_date = leaderboard_store
    return "Data from %s ledgers (%s-%s)" % (
        n_ledgers,
        datetime.fromisoformat(start_date).strftime("%m/%d/%y"),
        datetime.fromisoformat(end_date).strftime("%m/%d/%y"),
    )
