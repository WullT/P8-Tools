from dash import Dash, html, dcc, Input, Output, callback, no_update, State, dash_table
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objects as go
import plotly.express as px
from annot import *
from sqlitehelper import *
import pandas as pd
from skimage import io


def get_image(path):
    img = io.imread(path)
    fig = px.imshow(img)
    fig.update_layout(
        dragmode="drawrect",
        newshape=dict(line=dict(color="blue", width=8)),
        modebar=dict(orientation="v"),
    ),
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
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
        id="graph-pic-f",
        figure=fig,
        config=config,
        style={"height": "84vh", "align": "end"},
    )


def get_layout():
    return html.Div(
        [
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P("Select an Image"),
                        ],
                        width=1,
                    ),
                    dbc.Col(
                        [
                            dbc.Input(
                                id="image_input_f",
                                type="text",
                                placeholder="Image ID",
                                class_name="input-block-level form-control",
                            ),
                        ],
                        width=5,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "Load Annotations",
                                id="load_button_f",
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
                                id="remove_button_f",
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
                                id="save_button_f",
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
                                    html.Div(id="annotation_table_f"),
                                    html.Br(),
                                    html.Pre(
                                        "No annotations",
                                        id="annotations-data-pre-f",
                                        style={
                                            "height": "40vh",
                                            "overflow": "auto",
                                            "font-size": "small",
                                        },
                                    ),
                                ]
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            html.Div(
                                [],
                                id="image_div_f",
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
                center_x = int((shape["x0"] + shape["x1"]) / 2)
                center_y = int((shape["y0"] + shape["y1"]) / 2)
                w = int(abs(shape["x1"] - shape["x0"]))
                h = int(abs(shape["y1"] - shape["y0"]))
                json_annot["annotations"].append(
                    {
                        "id": i,
                        "center_x": center_x,
                        "center_y": center_y,
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


def store_annotations(annot_json):
    if annot_json is None:

        return False
    filename = annot_json["filename"]
    if filename is None:
        return False
    remove_annotations(filename, 2)
    if "annotations" in annot_json:
        if len(annot_json["annotations"]) == 0:
            remove_annotations(filename, 2)
            return True
        for annot in annot_json["annotations"]:
            insert_annotation(
                filename,
                annot["id"],
                annot["center_x"],
                annot["center_y"],
                annot["w"],
                annot["h"],
                annot["x0"],
                annot["y0"],
                annot["x1"],
                annot["y1"],
                2,
            )
    print(select_annotations(filename))


def get_annotations(filename):
    if filename is None:
        return None
    annots = select_annotations(filename, 2)
    print(annots)
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


@callback(
    Output("annotations-data-pre-f", "children"),
    Output("annotation_table_f", "children"),
    Input("graph-pic-f", "relayoutData"),
    State("graph-pic-f", "figure"),
    Input("graph-pic-f", "figure"),
    State("image_input_f", "value"),
    prevent_initial_call=True,
)
def on_new_annotation(in_reld, figure, disc_btn, image_input_f):
    ctx = dash.callback_context
    if ctx.triggered:
        if not "shapes" in str(ctx.triggered[0]["value"]):
            print("not shapes")
    filename = image_input_f.split("/")[-1]
    if "layout" in figure:
        if "shapes" in figure["layout"]:

            aj = get_annot_json(figure, filename)
            if aj is None:
                return "No annotations", None
            table = dash_table.DataTable(
                aj["annotations"],
                [
                    {"name": i, "id": i}
                    for i in ["id", "center_x", "center_y", "w", "h"]
                ],
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

            return json.dumps(aj, indent=2), html.Div(
                [table], style={"height": "40vh", "overflow": "auto"}
            )
        else:
            return "No annotations", None
    return "No annotations", None


@callback(
    Output("graph-pic-f", "figure"),
    Input("remove_button_f", "n_clicks"),
    Input("load_button_f", "n_clicks"),
    Input("save_button_f", "n_clicks"),
    State("graph-pic-f", "figure"),
    State("image_input_f", "value"),
    prevent_initial_call=True,
)
def on_button_click(n_clicks, apply_clicks, save_clicks, figure, image_url):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "remove_button_f":
            if n_clicks is not None:
                remove_annotations(image_url.split("/")[-1], 2)
                figure["layout"]["shapes"] = []
                return figure
        elif prop_id == "load_button_f":
            if apply_clicks is not None:
                annots = get_annotations(image_url.split("/")[-1])
                if annots is not None:

                    return append_annotations_to_fig(
                        get_annotations(image_url.split("/")[-1]), figure
                    )
                else:
                    return figure
        elif prop_id == "save_button_f":
            if save_clicks is not None:

                annot_json = get_annot_json(figure, image_url.split("/")[-1])
                if annot_json is not None:
                    store_annotations(annot_json)
                return dash.no_update
        else:
            return dash.no_update

    else:
        return dash.no_update


@callback(
    Output("image_div_f", "children"),
    Output("load_button_f", "n_clicks"),
    Input("image_input_f", "value"),
    State("load_button_f", "n_clicks"),
    prevent_initial_call=True,
)
def load_image(image_url, n_clicks):
    if image_url is not None:
        if n_clicks is None:
            n_clicks = 0
        n_clicks += 1
        return get_image(image_url), n_clicks
    return dash.no_update, dash.no_update
