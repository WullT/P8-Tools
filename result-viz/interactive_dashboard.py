import os
import json
from matplotlib.pyplot import legend, margins
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from parsing import Parser
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from dash import Dash, html, dcc, Input, Output, callback, no_update, State, dash_table
from tqdm import tqdm
import dash_bootstrap_components as dbc
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", "-i", type=str, default=".")
parser.add_argument("--port", "-p", type=int, default=8050)

args = parser.parse_args()
BASE_DIR = args.input_dir
PORT = args.port

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
)


colors = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
flower_colors = ["#bcbd22", "#17becf", "#e377c2", "#7f7f7f"]

files = []
for dir_path, dir_names, file_names in os.walk(BASE_DIR):
    for f in file_names:
        if f.endswith(".json"):
            files.append(os.path.join(dir_path, f))

flowers = []
pollinators = []
num_flowers = []

print("Parsing files...")
for i in tqdm(range(len(files))):
    parser = Parser(files[i])
    flowers.append(parser.get_flower_df())
    pollinators.append(parser.get_pollinator_df())
    num_flowers.append(len(parser.flowers))

flower_df = pd.concat(flowers)
pollinator_df = pd.concat(pollinators)
print("Number of images:", len(files))
print("Number of flowers:", len(flower_df))
print("Number of pollinators:", len(pollinator_df))

pollinator_df["hour"] = pollinator_df["timestamp"].dt.hour
pollinator_df["minute"] = pollinator_df["timestamp"].dt.minute
pollinator_df["time"] = pollinator_df["hour"] + pollinator_df["minute"] / 60
flower_df["hour"] = flower_df["timestamp"].dt.hour

node_ids = list(set(pollinator_df["node_id"]))
node_id_str = ""
for i in range(len(node_ids)):
    node_id_str += str(node_ids[i]) + ", "
    if i % 4 == 0:
        node_id_str += "\n"
if node_id_str.endswith("\n"):
    node_id_str = node_id_str[:-1]

node_id_str = node_id_str[:-2]
unique_polli_classes = list(set(pollinator_df["class_name"]))
unique_flower_classes = list(set(flower_df["class_name"]))
unique_polli_classes.sort()
unique_flower_classes.sort()
print("Flower Classes:", unique_flower_classes)
print("Pollinator Classes:", unique_polli_classes)


def encode_image(img):
    bio = BytesIO()
    img.save(bio, format="PNG")
    return base64.b64encode(bio.getvalue()).decode("utf-8")


def resize_image(img, size):
    w, h = img.size
    if w > h:
        h = int(h * size / w)
        w = size
    else:
        w = int(w * size / h)
        h = size
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    return img


def image_grid(df, rows, cols, offset=0):
    sz = 320

    fnt = ImageFont.truetype("arial.ttf", 18)
    images = []
    scores = []
    for i in range(rows * cols):
        try:
            col = df.iloc[i + offset]
            im = Image.open(BytesIO(base64.b64decode(col.crop)))
            im = resize_image(im, sz - 1)
            images.append(im)
            scores.append(str(col.score))
        except:
            images.append(Image.new("RGB", (sz, sz), "white"))
            scores.append("")

    grid = Image.new("RGB", (sz * cols, sz * rows), (255, 255, 255))
    for i in range(rows):
        for j in range(cols):
            grid.paste(images[i * cols + j], (j * sz, i * sz))
    d = ImageDraw.Draw(grid)
    for i in range(rows):
        for j in range(cols):
            d.text(
                (j * sz, i * sz), str(scores[i * cols + j]), fill=(255, 0, 0), font=fnt
            )
    return grid


def get_distplot_polli():
    times_p = []
    for c in unique_polli_classes:
        dfp = pollinator_df[pollinator_df["class_name"] == c]
        times_p.append(dfp["time"])

    fig = ff.create_distplot(
        times_p,
        unique_polli_classes,
        colors=colors,
        show_hist=False,
        curve_type="kde",
        histnorm="probability",
    )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend=dict(orientation="h"),
    )
    return fig


def generate_image_grid(class_name):
    dfp = pollinator_df[pollinator_df["class_name"] == class_name]
    dfp = dfp.sort_values(by="timestamp", ascending=False)
    dfp = dfp.sample(frac=1).reset_index(drop=True)
    cols = 8

    if len(dfp) <= 2 * cols:
        rows = 2
    else:
        rows = 3
    im = image_grid(dfp, rows, cols, offset=0)
    return im


def get_pollinator_images():
    res = []
    for c in unique_polli_classes:
        polli_col = dbc.Row(
            [
                html.H5(c),
                html.Img(
                    src="data:image/png;base64, " + encode_image(generate_image_grid(c))
                ),
            ],
        )
        res.append(html.Hr())
        res.append(polli_col)

    return html.Div(res)


def get_single_distplot_polli(class_name):
    dfp = pollinator_df[pollinator_df["class_name"] == class_name]
    if len(dfp) <= 1:
        fig = go.Figure()
    else:
        group_labels = [class_name]
        fig = ff.create_distplot(
            [dfp["time"]],
            [class_name],
            colors=[colors[unique_polli_classes.index(class_name)]],
            show_hist=False,
            curve_type="kde",
            histnorm="probability",
        )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend=dict(orientation="h"),
    )
    return fig


def get_single_distplot_for_each():
    res = []
    for c in unique_polli_classes:
        polli_col = dbc.Col(
            [
                html.H6(c),
                dcc.Graph(figure=get_single_distplot_polli(c)),
            ],
            # width=2,
        )
        res.append(polli_col)
    return dbc.Row(res)


def get_barplot_polli():
    fig = go.Figure()
    vals = []
    names = []
    for c in unique_polli_classes:
        vals.append(len(pollinator_df[pollinator_df["class_name"] == c]))
        names.append(c)

    fig.add_trace(
        go.Bar(
            x=names,
            y=vals,
            text=vals,
            marker_color=colors,
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


def get_dates_polli():
    timedelta = pd.Timedelta(hours=1)
    fig = make_subplots(rows=len(unique_polli_classes), cols=1, shared_xaxes=True)
    for c in unique_polli_classes:
        df_c = pollinator_df[pollinator_df["class_name"] == c]
        df_c["timestamp"] = pd.to_datetime(df_c["timestamp"])
        df_c = df_c.set_index("timestamp")
        series = pd.Series(df_c["score"])
        resampled = series.resample(timedelta).count()
        fig.add_trace(
            go.Scatter(
                x=resampled.index,
                y=resampled.values,
                name=c,
                mode="markers+lines",
                fill="tozeroy",
                marker_color=colors[unique_polli_classes.index(c)],
                opacity=0.7,
            ),
            row=unique_polli_classes.index(c) + 1,
            col=1,
        )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend=dict(orientation="h"),
    )
    return fig


def get_histogram_polli():
    fig = make_subplots(rows=len(unique_polli_classes), cols=1, shared_xaxes=True)
    for c in unique_polli_classes:
        dfp = pollinator_df[pollinator_df["class_name"] == c]
        fig.add_trace(
            go.Histogram(
                x=dfp["time"],
                histnorm="probability",
                name=c,
                opacity=0.5,
            ),
            row=unique_polli_classes.index(c) + 1,
            col=1,
        )
    fig.update_layout(
        template="plotly_white",
        legend=dict(
            orientation="h",
        ),
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


def get_flower_pie_chart():
    vals = []
    for flower_class in unique_flower_classes:
        df_flower_class = flower_df[flower_df["class_name"] == flower_class]
        vals.append(len(df_flower_class))
    fig = go.Figure()
    fig.add_trace(
        go.Pie(
            labels=unique_flower_classes,
            values=vals,
            marker_colors=flower_colors,
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend=dict(orientation="h"),
    )
    return fig


CONTENT_STYLE = {
    "margin-left": "1rem",
    "margin-right": "1rem",
    "padding": "1rem 1rem",
}

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Pollinator Report", className="display-7"),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.H4("Time Range", className="display-7"),
                        html.H5(
                            str(min(pollinator_df["timestamp"]))
                            + " - "
                            + str(max(pollinator_df["timestamp"])),
                            className="display-7",
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.H4("Camera ID's", className="display-7"),
                        html.H5(node_id_str, className="display-7"),
                    ],
                    width=7,
                ),
            ]
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("Detected Pollinators"),
                        dcc.Graph(figure=get_barplot_polli()),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.H6("Detections of Pollinators by date"),
                        dcc.Graph(figure=get_dates_polli()),
                    ],
                    width=10,
                ),
            ],
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Flowers"),
                        dcc.Graph(figure=get_flower_pie_chart()),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        html.H5("Observations of Pollinators by time of day"),
                        get_single_distplot_for_each(),
                    ],
                    width=10,
                ),
            ],
        ),
        html.H4("Observations"),
        html.Br(),
        get_pollinator_images(),
    ],
    style=CONTENT_STYLE,
)


app.run_server(debug=False, port=PORT)
