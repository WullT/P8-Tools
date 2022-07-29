from dash import Dash, html, dcc, Input, Output, callback, no_update, State
import dash_bootstrap_components as dbc
from dash_extensions import Keyboard
import dash
from annot import *
from sqlitehelper import *
from configuration import BASE_PATH

imageList = ImageList(BASE_PATH)


layout_right = html.Div(
    [
        html.Br(),
        html.Div([], id="toast", style={"height": "5vh"}),
        html.Div([], id="prev_annot", style={"height": "10vh"}),
        dbc.Button(
            [
                html.I(className="bi bi-flower3 me-2"),
                "Flowers visible",
            ],
            id="flower",
            color="success",
            className="mr-1",
        ),
        dbc.Button(
            [
                html.I(className="bi bi-x-square me-2"),
                "No Flowers visible",
            ],
            id="no_flower",
            color="danger",
            className="mr-1",
        ),
        dbc.Button(
            [
                html.I(className="bi bi-question-square me-2"),
                "Not sure",
            ],
            id="unknown",
            color="secondary",
            className="mr-1",
        ),
        html.Br(),
        html.Br(),
        dbc.Button(
            [
                html.I(className="bi bi-box-arrow-up-right me-2"),
                "Open Image in new Tab",
            ],
            id="open_image",
            href="/image/" + imageList.get_file(),
            external_link=True,
            target="_blank",
            color="info",
            className="mr-1",
        ),
        dbc.Button(
            [
                html.I(className="bi bi-box-arrow-up-right me-2"),
                "Annotate",
            ],
            id="annotate_image",
            href="/annotate/" + imageList.get_file(),
            external_link=True,
            target="_blank",
            color="warning",
            className="mr-1",
        ),
        html.Br(),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-card-image me-2"),
                            "Load",
                        ],
                        id="load_first",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-shuffle me-2"),
                            "Random",
                        ],
                        id="random",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-skip-backward-fill me-2"),
                            "Jump back",
                        ],
                        id="skip_back",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-skip-forward-fill me-2"),
                            "Jump forward",
                        ],
                        id="skip_forward",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-skip-start-fill me-2"), "Previous"],
                        id="previous",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
                dbc.Col(
                    dbc.Button(
                        [
                            html.I(className="bi bi-skip-end-fill me-3"),
                            "Next",
                        ],
                        id="next",
                        color="primary",
                        className="btn input-block-level form-control",
                    ),
                    width=6,
                ),
            ]
        ),
    ],
    className="d-grid gap-2 col-10 mx-auto",
)


def get_node_dropdown():
    nodeids = [item for t in get_node_ids() for item in t]
    return dcc.Dropdown(
        id="node_id",
        options=[{"label": i, "value": i} for i in nodeids],
        clearable=True,
        searchable=True,
        placeholder="Select a node",
    )


layout_left = html.Div(
    [
        html.P("Base directory = " + BASE_PATH, id="base_path"),
        html.Br(),
        html.P("Images to show:"),
        dbc.RadioItems(
            options=[
                {"label": "All Images", "value": 1},
                {"label": "Unseen Images", "value": 2},
                {"label": "Seen Images", "value": 3},
                {"label": "Images tagged as Not Sure", "value": 4},
                {"label": "Favourites", "value": 5},
            ],
            value=1,
            id="radioitems-input",
        ),
        html.Br(),
        html.P("Node ID"),
        get_node_dropdown(),
        html.Br(),
        html.Div(id="selected-node"),
        html.Br(),
        html.Label("Time range"),
        html.Br(),
        html.Br(),
        dcc.RangeSlider(
            id="slider",
            min=8,
            max=18,
            step=1,
            value=[8, 18],
        ),
        html.Br(),
    ]
)


def get_layout():
    return html.Div(
        [
            Keyboard(id="keyboard"),
            dbc.Row(
                [
                    dbc.Col(
                        layout_left,
                        width=3,
                    ),
                    dbc.Col(
                        [
                            html.H2("", id="filename", className="display-9"),
                            html.Br(),
                            html.Div(
                                dcc.Loading(
                                    [
                                        html.Div(id="imagediv"),
                                    ]
                                ),
                            ),
                            html.Br(),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            layout_right,
                        ],
                        width=3,
                    ),
                ]
            ),
        ]
    )


# Callback for keyboard
@callback(
    Output("next", "n_clicks"),
    Output("previous", "n_clicks"),
    Output("skip_back", "n_clicks"),
    Output("skip_forward", "n_clicks"),
    Output("random", "n_clicks"),
    Input("keyboard", "n_keydowns"),
    State("keyboard", "keydown"),
    State("next", "n_clicks"),
    State("previous", "n_clicks"),
    State("skip_back", "n_clicks"),
    State("skip_forward", "n_clicks"),
    State("random", "n_clicks"),
    prevent_initial_callbacks=True,
)
def listen_keyboard(
    n_keydowns,
    keydown,
    n_clicks_next,
    n_clicks_prev,
    n_clicks_back,
    n_clicks_forward,
    n_clicks_random,
):
    ctx = dash.callback_context

    if ctx.triggered[0]["prop_id"] == "keyboard.n_keydowns":
        print(keydown["key"])
        if keydown["key"] == "ArrowRight":
            if n_clicks_next == None:
                n_clicks_next = 0
            n_clicks_next += 1
            return n_clicks_next, no_update, no_update, no_update, no_update
        elif keydown["key"] == "ArrowLeft":
            if n_clicks_prev == None:
                n_clicks_prev = 0
            n_clicks_prev += 1
            return no_update, n_clicks_prev, no_update, no_update, no_update
        elif keydown["key"] == "ArrowUp":
            if n_clicks_forward == None:
                n_clicks_forward = 0
            n_clicks_forward += 1
            return no_update, no_update, no_update, n_clicks_forward, no_update
        elif keydown["key"] == "ArrowDown":
            if n_clicks_back == None:
                n_clicks_back = 0
            n_clicks_back += 1
            return no_update, no_update, n_clicks_back, no_update, no_update

        elif keydown["key"] == "r" or keydown["key"] == "0" or keydown["key"] == " ":
            if n_clicks_random == None:
                n_clicks_random = 0
            n_clicks_random += 1
            return no_update, no_update, no_update, no_update, n_clicks_random
        else:
            return no_update, no_update, no_update, no_update, no_update
    else:
        return no_update, no_update, no_update, no_update, no_update


@callback(
    Output("toast", "children"),
    Input("flower", "n_clicks"),
    Input("no_flower", "n_clicks"),
    Input("unknown", "n_clicks"),
    Input("keyboard", "n_keydowns"),
    State("keyboard", "keydown"),
    State("current_filename", "data"),
    Input("current_filename", "modified_timestamp"),
    prevent_initial_callbacks=True,
)
def store_flower(flower, no_flower, unknown, nkd, kd, path, fnts):
    if path is None:
        return
    if flower is None and no_flower is None and unknown is None and kd is None:
        return None
    ctx = dash.callback_context
    flower = None
    favourite = None
    if ctx.triggered[0]["prop_id"] == "flower.n_clicks":
        flower = 1
        print("flower")
    elif ctx.triggered[0]["prop_id"] == "no_flower.n_clicks":
        flower = -1
        print("no_flower")
    elif ctx.triggered[0]["prop_id"] == "unknown.n_clicks":
        flower = 0
    elif ctx.triggered[0]["prop_id"] == "keyboard.n_keydowns":
        print("keyboard")
        if kd["key"] == "y":
            flower = 1
        elif kd["key"] == "x":
            flower = -1
        elif kd["key"] == "q":
            flower = 0
        elif kd["key"] == "a":
            favourite = 1
        elif kd["key"] == "A":
            favourite = 0
        else:
            return None
    else:
        return None

    col = "success"
    text = "Marked as flower"

    if flower == -1:
        col = "danger"
        text = "Marked as no flower"
    elif flower == 0:
        col = "secondary"
        text = "Marked as unknown"
    if favourite == 1:
        col = "warning"
        text = "Marked as favourite"
    elif favourite == 0:
        col = "secondary"
        text = "Removed from favourite"
    node_id, date = get_metadata_from_filename(path.split("/")[-1])
    filename = path.split("/")[-1]
    if favourite is not None:
        set_favorite(filename=filename, favorite=favourite)
    if flower is not None:
        set_flower(filename=filename, flower=flower)

    return dbc.Alert(
        [html.I(className="bi bi-check-circle-fill me-2"), text], color=col
    )


@callback(
    Output("filename", "children"),
    Output("current_filename", "data"),
    Output("imagediv", "children"),
    Input("random", "n_clicks"),
    Input("next", "n_clicks"),
    Input("previous", "n_clicks"),
    Input("skip_back", "n_clicks"),
    Input("skip_forward", "n_clicks"),
    Input("load_first", "n_clicks"),
    prevent_initial_callbacks=True,
)
def update_figure(
    random_click,
    next_click,
    previous_click,
    skip_back_n_clicks,
    skip_forward_n_clicks,
    load_first_click,
):
    if (
        random_click is None
        and next_click is None
        and previous_click is None
        and skip_back_n_clicks is None
        and skip_forward_n_clicks is None
        and load_first_click is None
    ):

        return no_update
    ctx = dash.callback_context
    filename = None
    if ctx.triggered[0]["prop_id"] == "random.n_clicks":
        print("random")
        filename = imageList.get_random_file()
    elif ctx.triggered[0]["prop_id"] == "next.n_clicks":
        print("next")
        filename = imageList.get_next_file()
    elif ctx.triggered[0]["prop_id"] == "previous.n_clicks":
        print("previous")
        filename = imageList.get_previous_file()
    elif ctx.triggered[0]["prop_id"] == "skip_back.n_clicks":
        print("skip_back")
        filename = imageList.get_file_skip_backward(240)
    elif ctx.triggered[0]["prop_id"] == "skip_forward.n_clicks":
        print("skip_forward")
        filename = imageList.get_file_skip_forward(240)
    elif ctx.triggered[0]["prop_id"] == "load_first.n_clicks":
        print("load_first")
        filename = imageList.get_first_file()
    else:
        return no_update

    node_id, date = get_metadata_from_filename(filename.split("/")[-1])
    return (
        "ID: " + node_id + " Date: " + date.strftime("%Y-%m-%d %H:%M:%S"),
        filename,
        html.Img(src="/image/" + filename, style={"width": "100%"}),
    )


@callback(
    Output("prev_annot", "children"),
    Output("open_image", "href"),
    Output("annotate_image", "href"),
    Input("current_filename", "modified_timestamp"),
    State("current_filename", "data"),
    prevent_initial_callbacks=True,
)
def check_annotation(modified, filename):
    if filename is None:
        return no_update, no_update, no_update
    annotated, flower = check_if_exists(filename.split("/")[-1])
    new_href_img = "/image/" + filename
    new_href_annot = "/annotate/" + filename
    if annotated:
        if flower == 1:
            return (
                dbc.Alert(
                    [
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Marked as Flower",
                    ],
                    color="success",
                ),
                new_href_img,
                new_href_annot,
            )
        elif flower == -1:
            return (
                dbc.Alert(
                    [
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Marked as No Flower",
                    ],
                    color="danger",
                ),
                new_href_img,
                new_href_annot,
            )
        elif flower == 0:
            return (
                dbc.Alert(
                    [
                        html.I(className="bi bi-info-circle-fill me-2"),
                        "Marked as Unknown",
                    ],
                    color="warning",
                ),
                new_href_img,
                new_href_annot,
            )
        else:
            return None, new_href_img, new_href_annot
    else:
        return None, new_href_img, new_href_annot


@callback(
    Output("selected-node", "children"),
    Output("load_first", "n_clicks"),
    Input("node_id", "value"),
    Input("radioitems-input", "value"),
    State("radioitems-input", "value"),
    Input("slider", "value"),
    State("slider", "value"),
    prevent_initial_callbacks=True,
)
def update_selected_node(node_id, radio_input, radio_state, slider_input, slider_state):
    if node_id is None and radio_input is None and slider_input is None:
        print("getting filelist without conditions")
        imageList.update_filelist_by_selection()
        if imageList.get_file() is None:
            return "No Images for selected filters available", no_update
        return "All nodes", 1

    else:
        if slider_state[0] == 8:
            slider_state[0] = None
        if slider_state[1] == 18:
            slider_state[1] = None
        print("radio_input", radio_state)
        imageList.update_filelist_by_selection(
            node_id=node_id,
            seen_unseen_not_sure=radio_state,
            starttime_h=slider_state[0],
            endtime_h=slider_state[1],
        )
        if imageList.get_file() is None:
            return "No Images for selected filters available", no_update
        if node_id == None:
            return "All nodes", 1
        return "ID: " + node_id, 1
