from dash import Dash, html, dcc, Input, Output, callback, no_update, State, dash_table
import dash_bootstrap_components as dbc
import dash
from matplotlib.pyplot import figure
import plotly.graph_objects as go
import plotly.express as px
from annot import *
from sqlitehelper import *
import pandas as pd
from skimage import io


def get_image(path):
    try:
        img = io.imread(path)
    except:
        return None

    fig = px.imshow(img)
    fig.update_layout(
        dragmode="drawrect",
        newshape=dict(line=dict(color="red", width=4)),
        modebar=dict(orientation="v"),
    ),
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=2,
        spikecolor="blue",
        spikedash="solid",
    )
    fig.update_yaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=2,
        spikecolor="blue",
        spikedash="solid",
    )
    fig.update_traces(hovertemplate=None, hoverinfo="none")
    fig.update_layout(margin=dict(l=0, r=20, b=0, t=10))
    config = {
        "modeBarButtonsToAdd": [
            "drawrect",
            "eraseshape",
        ],
        "modeBarButtonsToRemove": ["autoscale", "toImage", "pan"],
        "scrollZoom": True,
        "displaylogo": False,
        "displayModeBar": True,
    }
    return dcc.Graph(
        id="graph-pic",
        figure=fig,
        config=config,
        style={"height": "80vh", "align": "end"},
    )


def get_annot_type_radio():
    return dbc.RadioItems(
        options=[
            {"label": "Labeling Daisy", "value": 2},
            {"label": "Labeling Wilde Möhre", "value": 3},
            {"label": "Labeling Flockenblume", "value": 4},
        ],
        value=2,
        id="annottype-input",
    )


def get_layout(image_url=None):
    if image_url is not None:
        image_url = image_url.replace("\\", "/")
    return html.Div(
        [
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Input(
                                id="image_input",
                                type="text",
                                placeholder="Enter the image url...",
                                class_name="input-block-level form-control",
                                value=image_url,
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            get_annot_type_radio(),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Load Annotations",
                                id="load_button",
                                n_clicks=0,
                                color="primary",
                                class_name="btn input-block-level form-control",
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Remove Annotations",
                                id="remove_button",
                                n_clicks=0,
                                color="danger",
                                class_name="btn input-block-level form-control",
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Save Annotations",
                                id="save_button",
                                n_clicks=0,
                                class_name="btn input-block-level form-control",
                                color="success",
                            ),
                        ],
                        width=2,
                    ),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Loading(
                                [
                                    html.Div(id="annotation_table"),
                                ]
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            html.Div(
                                [
                                    get_image(image_url),
                                ],
                                id="image_div",
                            ),
                        ),
                        width=8,
                    ),
                ],
                align="start",
            ),
        ]
    )


def get_annot_json(figure, filename):
    if "layout" in figure:
        if "shapes" in figure["layout"]:
            json_annot = {"filename": filename, "annotations": []}
            i = 0
            for shape in figure["layout"]["shapes"]:
                cx = int((shape["x0"] + shape["x1"]) / 2)
                cy = int((shape["y0"] + shape["y1"]) / 2)
                w = int(abs(shape["x1"] - shape["x0"]))
                h = int(abs(shape["y1"] - shape["y0"]))
                json_annot["annotations"].append(
                    {
                        "id": i,
                        "cx": cx,
                        "cy": cy,
                        "w": w,
                        "h": h,
                        "x0": int(shape["x0"]),
                        "y0": int(shape["y0"]),
                        "x1": int(shape["x1"]),
                        "y1": int(shape["y1"]),
                    }
                )
                i += 1
            if i > 0:
                return json_annot
            return None
        else:
            return None
    else:
        return None


def store_annotations(annot_json, annot_type, img_url):
    if annot_json is None:
        return False
    filename = annot_json["filename"]
    if filename is None:
        return False
    remove_annotations(filename, annot_type)
    shape = io.imread(img_url).shape
    im_width = shape[1]
    im_height = shape[0]
    if "annotations" in annot_json:
        if len(annot_json["annotations"]) == 0:
            return True
        for annot in annot_json["annotations"]:
            insert_annotation(
                filename,
                annot["id"],
                annot["cx"],
                annot["cy"],
                annot["w"],
                annot["h"],
                annot["x0"],
                annot["y0"],
                annot["x1"],
                annot["y1"],
                im_width,
                im_height,
                annot_type,
            )


def get_annotations(filename, annot_type):
    if filename is None:
        return None
    annots = select_annotations(filename, annot_type)
    if annots is None:
        return None
    annots.drop(columns=["filename"], inplace=True)
    annots.rename(columns={"annot_id": "id"}, inplace=True)
    annots_json = json.loads(annots.to_json(orient="records"))
    print(type(annots_json))

    return {"filename": filename, "annotations": annots_json}


def append_annotations_to_fig(annot_json, figure):
    if "layout" in figure:
        if "shapes" in figure["layout"]:
            for shape in figure["layout"]["shapes"]:
                figure["layout"]["shapes"].remove(shape)
        else:
            figure["layout"]["shapes"] = []
        for annotation in annot_json["annotations"]:
            print(annotation)
            figure["layout"]["shapes"].append(
                {
                    "editable": True,
                    "xref": "x",
                    "yref": "y",
                    "type": "rect",
                    "x0": annotation["x0"],
                    "y0": annotation["y0"],
                    "x1": annotation["x1"],
                    "y1": annotation["y1"],
                    "line": {"color": "red", "width": 8},
                }
            )
    return figure


def create_annot_table_view(annot_json):
    table = dash_table.DataTable(
        annot_json["annotations"],
        [{"name": i, "id": i} for i in ["id", "cx", "cy", "w", "h"]],
        style_as_list_view=True,
        style_cell={"textAlign": "center"},
        style_header={"textAlign": "center"},
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 248, 248)",
            }
        ],
    )
    return table


@callback(
    Output("graph-pic", "figure"),
    Output("annotation_table", "children"),
    Input("remove_button", "n_clicks"),
    Input("load_button", "n_clicks"),
    Input("save_button", "n_clicks"),
    State("graph-pic", "figure"),
    State("image_input", "value"),
    State("annottype-input", "value"),
    prevent_initial_call=True,
)
def on_button_click(n_clicks, apply_clicks, save_clicks, figure, image_url, annot_type):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "remove_button":
            if n_clicks is not None:
                remove_annotations(image_url.split("/")[-1], annot_type)
                figure["layout"]["shapes"] = []
                return figure, None
        elif prop_id == "load_button":
            if apply_clicks is not None:
                annots = get_annotations(image_url.split("/")[-1], annot_type)
                print("annots:", annots)
                if annots is not None:
                    annot_json = get_annotations(image_url.split("/")[-1], annot_type)
                    fig = append_annotations_to_fig(
                        annot_json,
                        figure,
                    )
                    return fig, create_annot_table_view(annot_json)

                else:
                    figure["layout"]["shapes"] = []

                    return figure, None
        elif prop_id == "save_button":
            if save_clicks is not None:

                annot_json = get_annot_json(figure, image_url.split("/")[-1])
                if annot_json is not None:
                    store_annotations(annot_json, annot_type, image_url)
                return dash.no_update, create_annot_table_view(annot_json)
        else:
            return dash.no_update

    else:
        return dash.no_update


@callback(
    Output("image_div", "children"),
    Output("load_button", "n_clicks"),
    Input("image_input", "value"),
    State("load_button", "n_clicks"),
    Input("annottype-input", "value"),
)
def load_image(image_url, n_clicks, anntype_input):
    print("load event fired!")
    if image_url is not None:
        if n_clicks is None:
            n_clicks = 0
        n_clicks += 1
        return get_image(image_url), n_clicks
    return dash.no_update, dash.no_update
