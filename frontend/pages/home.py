import dash
from dash import html, Input, Output, dcc, callback
import dash_bootstrap_components as dbc
from api.ledger import get_leaderboard
from plotly.express.colors import sample_colorscale
from sklearn.preprocessing import minmax_scale

dash.register_page(__name__, path="/")

layout = html.Div(
    [
        html.Div(
            [
                html.H3("Leaderboard", style={"marginBottom": "0"}),
                dbc.Button(
                    "Refresh",
                    color="secondary",
                    id="leaderboard_refresh",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "20px"},
                ),
            ],
            style={"flexDirection": "row", "display": "flex", "marginBottom": "20px"},
        ),
        dbc.Table(
            id="leaderboard_table",
            bordered=True,
            hover=True,
            responsive=True,
            style={"width": "auto"},
        ),
        dcc.Store(id="leaderboard_store"),
    ]
)


@callback(Output("leaderboard_store", "data"), Input("leaderboard_refresh", "n_clicks"))
def update_leaderboard_store(n_clicks):
    return get_leaderboard()


@callback(Output("leaderboard_table", "children"), Input("leaderboard_store", "data"))
def update_leaderboard_table(data):
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

    return [html.Thead(html.Tr([html.Th("Player"), html.Th("Stack")]))] + [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(x[0] + " " + x[1]),
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
