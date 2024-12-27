import dash
from dash import html, Input, Output, dcc, callback
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale
from datetime import datetime, timedelta

dash.register_page(__name__, path="/")

leaderboard_card = [
    dbc.Card(
        [
            html.H3("Leaderboard", style={"marginBottom": "-8px"}),
            dbc.FormText(
                id="leaderboard_subtitle",
                color="secondary",
                style={"marginBottom": "12px"},
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
                        ],
                        value=None,
                    ),
                ],
                className="radio-group",
            ),
            dbc.Table(
                id="leaderboard_table",
                bordered=True,
                hover=True,
                responsive=True,
                style={"marginTop": "4px"},
            ),
        ],
        style={"padding": "20px"},
    )
]

layout = dbc.Row(
    [
        dbc.Col(leaderboard_card, width={"size": "4"}),
        dbc.Col([], width={"size": "8"}),
        dcc.Store(id="leaderboard_store"),
    ]
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
            [0, "rgb(197, 67, 60)"],  # Green
            [0.5, "rgb(255, 255, 255)"],  # White
            [1, "rgb(120, 166, 90)"],  # Red
        ],
        minmax_scale(nets),
    )

    return [
        html.Thead(html.Tr([html.Th("Player"), html.Th("Games"), html.Th("Stack")]))
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
    return "Data from %s ledgers (%s-%s). Some ledgers may not be published yet." % (
        n_ledgers,
        datetime.fromisoformat(start_date).strftime("%m/%d/%y"),
        datetime.fromisoformat(end_date).strftime("%m/%d/%y"),
    )
