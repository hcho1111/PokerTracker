import dash
from dash import html, Input, Output, dcc, callback, State
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard, get_recent_ledgers
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale
from datetime import datetime, timedelta, date
from api.players import get_top_offenders
from zoneinfo import ZoneInfo

dash.register_page(__name__, path="/")

leaderboard_card = dbc.Card(
    [
        html.H3("Leaderboard 📈"),
        html.Div(
            [
                dbc.Button(
                    id="leaderboard_show_filters",
                    color="secondary",
                    outline=True,
                    size="sm",
                ),
                dbc.FormText(
                    id="leaderboard_subtitle",
                    color="secondary",
                    style={"marginLeft": "6px", "marginBottom": "4px"},
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "0px",
                "marginTop": "-2px",
            },
            className="d-md-block",
        ),
        dbc.Collapse(
            dbc.Card(
                [
                    dbc.FormText(
                        "Filter by Time",
                        color="secondary",
                        style={"marginBottom": "4px"},
                    ),
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
                                    {"label": "Custom", "value": "custom"},
                                ],
                                value=None,
                            ),
                        ],
                        className="radio-group",
                    ),
                    dcc.DatePickerRange(
                        id="leaderboard_date_filter_range",
                        min_date_allowed=date(1995, 8, 5),
                        style={"marginBottom": "12px", "marginTop": "4px"},
                        max_date_allowed=date.today(),
                        initial_visible_month=date.today() - timedelta(days=7),
                        start_date=date.today() - timedelta(days=7),
                        end_date=date.today(),
                    ),
                    dbc.FormText(
                        "Filter by Games Played",
                        color="secondary",
                        style={"marginBottom": "8px", "marginTop": "8px"},
                    ),
                    html.Div(
                        [
                            dcc.Slider(
                                id="leaderboard_games_slider",
                                min=0,
                                max=0,
                                step=1,
                                value=0,
                                marks=None,
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                    "template": "≥{value}",
                                },
                            ),
                        ],
                        style={"paddingLeft": "8px"},
                    ),
                ],
                style={"marginTop": "8px"},
            ),
            id="leaderboard_filters_collapse",
        ),
        dbc.Table(
            id="leaderboard_table",
            bordered=True,
            hover=True,
            responsive=True,
            style={"marginTop": "16px"},
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


def get_top_username_count_card():
    return dbc.Card(
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

    return [
        html.Thead(
            html.Tr(
                [
                    html.Th("Date"),
                    html.Th("Paid"),
                    html.Th("🦈 Shark"),
                    html.Th("Net"),
                    html.Th("🐟 Fish"),
                    html.Th("Net"),
                ]
            )
        )
    ] + [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            dcc.Link(
                                x[1]
                                .astimezone(ZoneInfo("America/New_York"))
                                .strftime("%m/%d"),
                                target="_blank",
                                href="https://www.pokernow.club/games/%s" % x[0],
                            )
                        ),
                        html.Td("Y" if x[8] else "N"),
                        html.Td(
                            ", ".join(
                                [
                                    "%s %s." % (first, last[0])
                                    for first, last in zip(
                                        x[2].split(", "), x[3].split(", ")
                                    )
                                ]
                            )
                        ),
                        html.Td(
                            "{:.2f}".format(x[4] / 100),
                            style={
                                "textAlign": "end",
                                "backgroundColor": discrete_colors[i],
                            },
                        ),
                        html.Td(
                            ", ".join(
                                [
                                    "%s %s." % (first, last[0])
                                    for first, last in zip(
                                        x[5].split(", "), x[6].split(", ")
                                    )
                                ]
                            )
                        ),
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


def get_recent_ledgers_card():
    return dbc.Card(
        [
            html.H3("Ledgers 📒"),
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


# fbclid param ignored. Added from FB messenger.
def layout(fbclid=""):
    return dbc.Row(
        [
            dbc.Col([dbc.Row(children=[leaderboard_card])], md=6),
            dbc.Col(
                [
                    dbc.Row(children=[get_recent_ledgers_card()]),
                    dbc.Row(
                        children=[get_top_username_count_card()],
                        style={"marginTop": "24px"},
                    ),
                ],
                md=6,
            ),
            dcc.Store(id="leaderboard_store"),
        ],
        className="g-5",
    )


@callback(
    Output("leaderboard_filters_collapse", "is_open"),
    Input("leaderboard_show_filters", "n_clicks"),
)
def update_filters_collpase(n_clicks):
    if n_clicks is None:
        return False
    return False if n_clicks % 2 == 0 else True


@callback(
    Output("leaderboard_show_filters", "children"),
    Input("leaderboard_show_filters", "n_clicks"),
)
def update_leaderboard_show_filters_toggle(n_clicks):
    if n_clicks is None:
        return "Show Filters"
    return "Show Filters" if n_clicks % 2 == 0 else "Hide Filters"


@callback(
    Output("leaderboard_games_slider", "marks"),
    Input("leaderboard_games_slider", "max"),
)
def update_leaderboard_games_slider_marks(slider_max):
    return {0: "≥0 games", slider_max: "≥%s" % slider_max}


@callback(
    Output("leaderboard_games_slider", "max"),
    Input("leaderboard_store", "data"),
)
def update_leaderboard_games_slider_max(leaderboard_store):
    data, _, _, _ = leaderboard_store
    return max([x[3] for x in data])


@callback(
    Output("leaderboard_store", "data"),
    Input("leaderboard_time_range", "value"),
    Input("leaderboard_date_filter_range", "start_date"),
    Input("leaderboard_date_filter_range", "end_date"),
)
def update_leaderboard_store(value, start_date, end_date):
    if value == "custom":
        return get_leaderboard(start_date, end_date)
    return get_leaderboard(
        "2020-01-01"
        if value is None
        else (datetime.now() - timedelta(days=value)).isoformat()
    )


@callback(
    Output("leaderboard_table", "children"),
    Input("leaderboard_store", "data"),
    Input("leaderboard_games_slider", "value"),
)
def update_leaderboard_table(leaderboard_store, games_filter):
    data, _, _, _ = leaderboard_store

    filtered_data = []
    for row in data:
        if row[3] >= games_filter:
            filtered_data.append(row)
    data = filtered_data

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
    return "%s ledgers (%s-%s)" % (
        n_ledgers,
        datetime.fromisoformat(start_date).strftime("%m/%d/%y"),
        datetime.fromisoformat(end_date).strftime("%m/%d/%y"),
    )


@callback(
    Output("leaderboard_date_filter_range", "style"),
    Input("leaderboard_time_range", "value"),
    State("leaderboard_date_filter_range", "style"),
)
def update_date_filter_visibility(value, style):
    if value == "custom":
        return {**style, "display": "inline"}
    return {**style, "display": "none"}
