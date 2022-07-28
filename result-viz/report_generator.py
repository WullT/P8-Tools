import os
import json
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from parsing import Parser
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from tqdm import tqdm
import datetime
import argparse

date_now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
parser = argparse.ArgumentParser()
parser.add_argument(
    "--output_dir", "-o", type=str, default="report_output" + date_now + "/"
)
parser.add_argument("--input_dir", "-i", type=str, default=".")
parser.add_argument("--pdf", action="store_true")
parser.add_argument("--pdf_name", type=str, default="report_" + date_now + ".pdf")
args = parser.parse_args()
OUTPUT_DIR = args.output_dir
BASE_DIR = args.input_dir
STORE_PDF = args.pdf

if STORE_PDF:
    from fpdf import FPDF

PDF_FILENAME = args.pdf_name
if not PDF_FILENAME.endswith(".pdf"):
    PDF_FILENAME.replace(".", "_")
    PDF_FILENAME += ".pdf"

if not OUTPUT_DIR.endswith("/"):
    OUTPUT_DIR += "/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


# Figure constants
TOTAL_WIDTH = 2100
TOTAL_HEIGHT = 2970
FONT_SIZE = 30
CROP_IMAGE_SIZE = 480
CROP_GRID_COLS = 8
GRID_MAX_ROWS = 6

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
pollinator_df["day"] = pollinator_df["timestamp"].dt.day
pollinator_df["minute"] = pollinator_df["timestamp"].dt.minute
pollinator_df["time"] = pollinator_df["hour"] + pollinator_df["minute"] / 60
flower_df["hour"] = flower_df["timestamp"].dt.hour
flower_df["day"] = flower_df["timestamp"].dt.day

node_ids = list(set(pollinator_df["node_id"]))
node_id_str = ""
for i in range(len(node_ids)):
    node_id_str += str(node_ids[i]) + ", "
    if i > 0 and (i + 1) % 7 == 0:
        node_id_str += "\n"
if node_id_str.endswith("\n"):
    node_id_str = node_id_str[:-1]
node_id_str = node_id_str[:-2]

print("Camera IDs:", node_id_str)

unique_polli_classes = list(set(pollinator_df["class_name"]))
unique_flower_classes = list(set(flower_df["class_name"]))
unique_polli_classes.sort()
unique_flower_classes.sort()


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
    sz = CROP_IMAGE_SIZE
    fnt = ImageFont.truetype("arial.ttf", 25)
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
        font_size=FONT_SIZE,
        width=TOTAL_HEIGHT,
        height=TOTAL_WIDTH,
    )
    return fig


def generate_image_grid(class_name):
    dfp = pollinator_df[pollinator_df["class_name"] == class_name]
    dfp = dfp.sort_values(by="timestamp", ascending=False)
    dfp = dfp.sample(frac=1).reset_index(drop=True)
    cols = CROP_GRID_COLS
    rows = min(int(len(dfp) / cols) + 1, GRID_MAX_ROWS)
    im = image_grid(dfp, rows, cols, offset=0)
    return im


def save_pollinator_images():
    for c in unique_polli_classes:
        im = generate_image_grid(c)
        im.save(OUTPUT_DIR + "grid_" + c + ".png")


def get_single_distplot_polli(class_name):
    dfp = pollinator_df[pollinator_df["class_name"] == class_name]
    if len(dfp) <= 1:
        fig = go.Figure()
    else:
        group_labels = [class_name]
        # fig = ff.create_distplot([dfp["time"]], group_labels, bin_size=.2,show_hist=False,curve_type='kde',histnorm = 'probability')

        fig = ff.create_distplot(
            [dfp["time"]],
            [class_name],
            colors=[colors[unique_polli_classes.index(class_name)]],
            show_hist=False,
            curve_type="kde",
            histnorm="probability",
        )
        fig.update_traces(
            line=dict(
                width=5,
            )
        )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend=dict(orientation="h"),
        width=TOTAL_WIDTH,
        height=TOTAL_HEIGHT / 3,
        font_size=FONT_SIZE,
    )
    return fig


def get_barplot_polli():
    fig = go.Figure()
    vals = []
    for c in unique_polli_classes:
        vals.append(len(pollinator_df[pollinator_df["class_name"] == c]))

    fig.add_trace(
        go.Bar(
            x=unique_polli_classes,
            y=vals,
            text=vals,
            marker_color=colors,
        )
    )
    fig.update_layout(
        template="plotly_white",
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        width=TOTAL_WIDTH,
        height=TOTAL_HEIGHT / 3,
        font_size=FONT_SIZE,
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
        width=TOTAL_WIDTH,
        height=TOTAL_HEIGHT,
        font_size=FONT_SIZE,
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
        width=TOTAL_WIDTH / 2,
        height=TOTAL_HEIGHT / 3,
        font_size=FONT_SIZE,
    )
    return fig


print("Exporting images...")
save_pollinator_images()
for c in unique_polli_classes:
    get_single_distplot_polli(c).write_image(
        OUTPUT_DIR + "fig_distplot_" + c + ".png", format="png"
    )

get_barplot_polli().write_image(OUTPUT_DIR + "fig_pollinator_bar.png", format="png")

get_dates_polli().write_image(OUTPUT_DIR + "fig_by_date.png", format="png")


get_flower_pie_chart().write_image(OUTPUT_DIR + "fig_flower_pie.png", format="png")

if not STORE_PDF:
    print("Done.")
    exit(0)

print("Generating PDF...")
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=25)
pdf.cell(200, 10, txt="Pollinator Report", ln=1, align="C")
pdf.ln(4)
pdf.set_font("Arial", size=13)
pdf.cell(200, 10, txt="Cameras", ln=1, align="C")

pdf.set_font("Arial", size=11)

pdf.multi_cell(200, 5, txt=node_id_str, align="C")
pdf.set_font("Arial", size=13)

pdf.cell(
    200,
    10,
    txt="Time Range: "
    + str(min(pollinator_df["timestamp"]))
    + " - "
    + str(max(pollinator_df["timestamp"])),
    ln=1,
    align="C",
)
pdf.ln(10)
pdf.set_font("Arial", size=13)

pdf.cell(200, 10, txt="Observed Pollinators", ln=1, align="L")
pdf.image(OUTPUT_DIR + "fig_pollinator_bar.png", w=pdf.w - 10)
pdf.ln(10)
pdf.cell(200, 10, txt="Flower Types", ln=1, align="L")
pdf.ln(1.5)

pdf.image(OUTPUT_DIR + "fig_flower_pie.png", w=80)
output_filename = "Pollinator_Report_" + node_ids[0].replace(",", "_") + ".pdf"

# pdf.add_page()
pdf.set_font("Arial", size=15)

pdf.image(OUTPUT_DIR + "fig_by_date.png", w=pdf.w - 20, h=pdf.h - 20)

for c in unique_polli_classes:
    pdf.add_page()

    pdf.cell(200, 10, txt=c, ln=1, align="L")
    pdf.ln(1.5)

    pdf.image(OUTPUT_DIR + "fig_distplot_" + c + ".png", w=pdf.w - 20)
    pdf.ln(1.5)
    pdf.image(OUTPUT_DIR + "grid_" + c + ".png", w=pdf.w - 20)

print("Saving PDF({})...".format(OUTPUT_DIR + PDF_FILENAME))
pdf.output(OUTPUT_DIR + PDF_FILENAME)
