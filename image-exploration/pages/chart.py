from dash import Dash, html, dcc, Input, Output, callback, no_update, State
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objects as go
from annot import *
from sqlitehelper import *
import pandas as pd


def create_heatmap():
    df = get_categorized_as_df()
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            x=df["date"],
            y=df["node_id"],
            z=df["flower"],
            colorscale="RdYlGn",
            showscale=False,
        )
    )
    fig.update_layout(
        title="Flower vs Date",
        xaxis_title="Date",
        yaxis_title="Node ID",
        template="plotly_white",
    )

    return fig


def create_scatter():
    df = get_categorized_as_df()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["node_id"],
            mode="markers",
            marker=dict(
                color=df["flower"],
                colorscale="RdYlGn",
                symbol=df["available"],
                size=10,
                opacity=0.8,
                showscale=False,
            ),
        )
    )
    fig.update_layout(
        title="Flower vs Node ID",
        xaxis_title="Date",
        yaxis_title="Node ID",
        template="plotly_white",
    )

    return fig


def get_layout():
    return html.Div(
        [
            dcc.Graph(
                id="scatterplot",
                figure=create_scatter(),
                clear_on_unhover=False,
                style={"height": "70vh"},
            ),
            dcc.Tooltip(
                id="scatter-tooltip",
                targetable=True,
                style={
                    "font-size": "1rem",
                    "font-family": "sans-serif",
                    "padding": "0px",
                },
            ),
        ]
    )


@callback(
    Output("scatter-tooltip", "show"),
    Output("scatter-tooltip", "bbox"),
    Output("scatter-tooltip", "children"),
    Input("scatterplot", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update
    pt = hoverData["points"][0]
    bbox = pt["bbox"]
    num = pt["pointNumber"]
    df = get_categorized_as_df()
    df_row = df.iloc[num]
    img_src = df_row["path"]

    img_src = "/image/" + img_src
    name = df_row["node_id"]
    flower = df_row["flower"]
    flower_text = "Not classified"
    card_color = "warning"
    if flower == 0:
        flower_text = "Not sure"
    elif flower == 1:
        flower_text = "Flower"
        card_color = "success"
    elif flower == -1:
        flower_text = "No flower"
        card_color = "danger"
    date = df_row["date"]
    img_card = None
    if df_row["available"] == True:
        img_card = dbc.CardImg(src=img_src, bottom=True, style={"padding": "0px"})

    children = [
        html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.B(name + " " + flower_text),
                            ],
                            style={"padding": "8px"},
                        ),
                        dbc.CardBody(
                            html.Small(date, className="card-text text-muted"),
                            style={"padding": "6px"},
                        ),
                        img_card,
                    ],
                    color=card_color,
                    outline=True,
                ),
            ],
            style={
                "width": "300px",
                "white-space": "normal",
                "margin": "auto",
            },
        )
    ]

    return True, bbox, children
