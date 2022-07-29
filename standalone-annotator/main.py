from dash import Dash, html, dcc, Input, Output, callback, no_update, State, dash_table
import dash
from flask import Flask, make_response, send_file
import dash_bootstrap_components as dbc
import plotly.express as px
from skimage import io
import os
import json


IMG_PATH = "path/to/images/"

LABEL_PATH = "path/to/store/labels/"

flask_app = Flask(__name__)
app = Dash(
    server=flask_app,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

CONTENT_STYLE = {
    "margin-left": "1rem",
    "margin-right": "1rem",
    "padding": "1rem 1rem",
}


def save_labels(filepath, labels, label_id):
    """
    Save labels to file.
    [{'x': 0.4013605442176871, 'y': 0.44776119402985076, 'w': 0.16326530612244897, 'h': 0.15671641791044777}]
    """
    with open(filepath, "w") as f:
        for label in labels:
            f.write(
                str(label_id)
                + " "
                + str(label["x"])
                + " "
                + str(label["y"])
                + " "
                + str(label["w"])
                + " "
                + str(label["h"])
                + "\n"
            )


def abs2rel(x, y, w, h, image_width, image_height):
    cx = x / image_width
    cy = y / image_height
    w = w / image_width
    h = h / image_height
    return cx, cy, w, h


def get_images():
    images = []
    for filename in os.listdir(IMG_PATH):
        if filename.endswith(".jpg"):
            images.append(filename)
    return images


def get_labels():
    labels = []
    for filename in os.listdir(LABEL_PATH):
        if filename.endswith(".txt"):
            labels.append(filename)
    return labels


def remove_images_with_labels(images, labels):
    images_with_labels = []
    for image in images:
        if image.split(".")[0] + ".txt" not in labels:
            images_with_labels.append(image)
    return images_with_labels


def get_unseen_images():
    images = get_images()
    labels = get_labels()
    images_with_labels = remove_images_with_labels(images, labels)
    return images_with_labels


def image_dropdown():
    images = get_unseen_images()
    if len(images) == 0:
        return dbc.Alert(
            "No images left to label",
            color="danger",
            style={"margin-top": "1rem", "margin-bottom": "1rem"},
        )

    return dcc.Dropdown(
        id="image-dropdown",
        options=[{"label": i, "value": i} for i in images],
        value=images[0],
        clearable=False,
    )


def category_dropdown():
    return dcc.Dropdown(
        id="category-dropdown",
        options=[
            {"label": "daisy", "value": 0},
            {"label": "wildemoere", "value": 1},
            {"label": "flockenblume", "value": 2},
        ],
        value=1,
        clearable=False,
    )


def_path = "https://i.imgflip.com/3ftmzb.jpg"


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


app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3("Standalone Labeler", className="display-7"),
                    ],
                    width=3,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Select the image"),
                        image_dropdown(),
                        html.Br(),
                        category_dropdown(),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Previous",
                                            id="prev-button",
                                            color="secondary",
                                            class_name="btn input-block-level form-control",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Next",
                                            id="next-button",
                                            color="secondary",
                                            class_name="btn input-block-level form-control",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Br(),
                        dbc.Button(
                            "Export",
                            id="export-button",
                            color="success",
                            class_name="btn input-block-level form-control",
                        ),
                        html.Br(),
                        html.Br(),
                        dbc.Progress(id="progress-bar", value=0, max=100, color="info"),
                        html.Div(id="export-div"),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        get_image(def_path),
                    ],
                    width=9,
                    id="image-col",
                ),
            ]
        ),
    ],
    style=CONTENT_STYLE,
)


def get_annotations_from_figure(fig, im_width, im_height):
    annotations = []
    if "layout" in fig:
        f = open("fig.json", "w")
        f.write(json.dumps(fig))
        f.close()

        if "shapes" in fig["layout"]:
            for shape in fig["layout"]["shapes"]:
                cx = int((shape["x0"] + shape["x1"]) / 2)
                cy = int((shape["y0"] + shape["y1"]) / 2)
                w = int(abs(shape["x1"] - shape["x0"]))
                h = int(abs(shape["y1"] - shape["y0"]))
                print(cx, cy, w, h, im_width, im_height)
                cx, cy, w, h = abs2rel(cx, cy, w, h, im_width, im_height)
                annotations.append({"x": cx, "y": cy, "w": w, "h": h})
    return annotations


@app.callback(
    Output("export-div", "children"),
    Output("progress-bar", "value"),
    Output("progress-bar", "max"),
    Input("export-button", "n_clicks"),
    State("image-dropdown", "value"),
    State("graph-pic", "figure"),
    State("category-dropdown", "value"),
    prevent_initial_call=True,
)
def export_button(n_clicks, image, fig, category):
    if n_clicks is None:
        return None
    if n_clicks > 0:
        shape = io.imread(IMG_PATH + image).shape
        im_width = shape[1]
        im_height = shape[0]
        annots = get_annotations_from_figure(fig, im_width, im_height)
        save_labels(LABEL_PATH + image.split(".")[0] + ".txt", annots, category)
        print(annots)

        return (
            html.Pre(json.dumps(annots, indent=2)),
            len(os.listdir(LABEL_PATH)),
            len(os.listdir(IMG_PATH)),
        )


@app.callback(
    Output("image-col", "children"),
    Input("image-dropdown", "value"),
)
def update_img(image):
    return get_image(IMG_PATH + image)


@app.callback(
    Output("image-dropdown", "value"),
    Input("prev-button", "n_clicks"),
    Input("next-button", "n_clicks"),
    State("image-dropdown", "value"),
    State("image-dropdown", "options"),
    prevent_initial_call=True,
)
def button_callback(n_prev, n_next, image, options):

    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    values = [opt["value"] for opt in options]
    current_index = values.index(image)
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "prev-button":
        new_index = max(0, current_index - 1)
    elif button_id == "next-button":
        new_index = min(len(values) - 1, current_index + 1)
    return values[new_index]


print("Nr of images:", len(os.listdir(IMG_PATH)))
print("Nr of labels:", len(os.listdir(LABEL_PATH)))

app.run_server(host="0.0.0.0", debug=True, port=8060)
