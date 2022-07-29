from dash import Dash, html, dcc, Input, Output, callback, no_update, State, dash_table
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objects as go
from annot import *
from sqlitehelper import *
import pandas as pd


def get_node_dropdown():
    nodes = get_counts_by_node_as_df()
    active_nodes = [item for t in get_node_ids() for item in t]
    ids = nodes["node_id"].to_list()
    image_counts = nodes["count_images"].to_list()
    default_node_index = 0
    options = []
    for i in range(len(ids)):
        active = ""
        if ids[i] in active_nodes:
            active = " [active]"
            default_node_index = i
        options.append(
            {
                "label": ids[i] + " (" + str(image_counts[i]) + " Pictures)" + active,
                "value": ids[i],
            }
        )

    return dcc.Dropdown(
        id="node_id",
        options=options,
        value=ids[default_node_index],
        clearable=True,
        searchable=True,
        placeholder="Select a node",
    )


def get_layout_left():
    return html.Div(
        [
            html.P("Select a node"),
            get_node_dropdown(),
        ]
    )


def create_pie_chart(positive, negative, neutral):
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=["Flowers visible", "No Flowers visible", "Not sure"],
            values=[positive, negative, neutral],
            marker_colors=["#00ff00", "#ff0000", "#ffff00"],
            textinfo="label+percent",
            hole=0.4,
        )
    )
    fig.update_layout(
        title="Flower Classification",
        template="plotly_white",
    )
    return dcc.Graph(figure=fig)


def get_flower_times(node_id):
    df = get_data_by_node_as_df(node_id, True)
    df["MA"] = df.flower.rolling(window=5, center=True).min()
    df.replace({"MA": {0: 0, -1: 0}}, inplace=True)
    starts = []
    s_indexes = []
    ends = []
    e_indexes = []
    state = 0
    for i in range(len(df)):
        if df.MA[i] == 1:
            if state == 0:
                state = 1
                s_indexes.append(i)
                starts.append(df.date[i])

        elif df.MA[i] == 0:
            if state == 1:
                state = 0
                e_indexes.append(i)
                ends.append(df.date[i])
    if len(ends) < len(starts):
        ends.append(df.date.iloc[-1])
        e_indexes.append(len(df) - 1)
    durations = []
    for i in range(len(e_indexes)):
        durations.append(
            str(
                pd.to_datetime(df.date[e_indexes[i]])
                - pd.to_datetime(df.date[s_indexes[i]])
            )
        )

    df = pd.DataFrame({"start": starts, "end": ends, "duration": durations})
    return df


def get_timeranges_with_flowers(node_id):
    df = get_flower_times(node_id)

    return dash_table.DataTable(
        df.to_dict("records"),
        [{"name": i, "id": i} for i in df.columns],
        style_as_list_view=True,
        style_cell={"textAlign": "center"},
        style_header={"textAlign": "center"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"}
        ],
    )


def create_line_chart(node_id):
    df = get_data_by_node_as_df(node_id, True)

    df["MA"] = df.flower.rolling(window=3, center=True).max()
    df.replace({"MA": {0: -1, -1: -1}}, inplace=True)
    df["BL"] = df["MA"]
    df.replace({"BL": {1: -1}}, inplace=True)
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["BL"],
            mode="lines",
            line_shape="hv",
            name="Moving Average",
            line=dict(color="black", width=0.01),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["MA"],
            mode="lines",
            line_shape="hv",
            name="Moving Minimum",
            fill="tonexty",
            line=dict(color="#00ff00", width=1),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["flower"],
            mode="markers",
            name="Flowers " + str(node_id),
            marker=dict(color="#0000ff", size=8),
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Flowers",
        template="plotly_white",
    )
    fig.update_layout(showlegend=False)
    return dcc.Graph(figure=fig)


def get_download_buttons():
    return html.Div(
        [
            dbc.Button(
                "Download CSV",
                id="download-csv",
                color="primary",
                className="mr-1",
                style={"margin-left": "10px", "margin-right": "10px"},
            ),
            dbc.Button(
                "Download Excel",
                id="download-excel",
                class_name="mr-1",
                style={"margin-left": "10px", "margin-right": "10px"},
            ),
        ]
    )


def get_layout():
    return html.Div(
        [
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            get_layout_left(),
                            html.Div(id="metadata"),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            [
                                html.Div(id="content-graph"),
                                get_download_buttons(),
                                dcc.Download(id="download-dataframe-csv"),
                                dcc.Download(id="download-dataframe-excel"),
                            ]
                        ),
                        width=8,
                    ),
                ],
            ),
        ]
    )


@callback(
    Output("download-dataframe-csv", "data"),
    Input("download-csv", "n_clicks"),
    State("node_id", "value"),
    prevent_initial_call=True,
)
def func(n_clicks, node_id):
    return dcc.send_data_frame(
        get_flower_times(node_id).to_csv, "flower_timeranges_" + node_id + ".csv"
    )


@callback(
    Output("download-dataframe-excel", "data"),
    Input("download-excel", "n_clicks"),
    State("node_id", "value"),
    prevent_initial_call=True,
)
def func(n_clicks, node_id):
    return dcc.send_data_frame(
        get_flower_times(node_id).to_excel,
        "flower_timeranges_" + node_id + ".xlsx",
        sheet_name="times_with_flowers",
    )


@callback(
    Output("content-graph", "children"),
    Output("metadata", "children"),
    Input("node_id", "value"),
)
def update_graph(node_id):
    df = get_counts_by_node_as_df()
    df = df[df["node_id"] == node_id]
    print(df)

    return (
        html.Div(
            [
                html.Br(),
                create_line_chart(node_id),
                html.Br(),
                html.H3("Time ranges with flowers"),
                html.Br(),
                get_timeranges_with_flowers(node_id),
            ],
            style={"padding": "10px"},
        ),
        html.Div(
            [
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4("Node ID:"),
                            width=6,
                        ),
                        dbc.Col(
                            html.H3(str(node_id)),
                            width=6,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4("Pictures:"),
                            width=6,
                        ),
                        dbc.Col(
                            html.H3(str(df["count_images"].iloc[0])),
                            width=6,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4("Classified:"),
                            width=6,
                        ),
                        dbc.Col(
                            html.H3(str(df["count_classified"].iloc[0])),
                            width=6,
                        ),
                    ]
                ),
                html.Hr(),
                create_pie_chart(
                    df["count_flower"].iloc[0],
                    df["count_no_flower"].iloc[0],
                    df["count_not_sure"].iloc[0],
                ),
            ]
        ),
    )
