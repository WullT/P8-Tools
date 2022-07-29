from dash import Dash, html, dcc, Input, Output, callback, no_update
from dash.dependencies import Input, Output, State
import dash
from flask import Flask, make_response, send_file

from dash_extensions import Keyboard
import dash_bootstrap_components as dbc
from annot import *
from sqlitehelper import *
from configuration import BASE_PATH, PORT, HOST
from pages import chart, flowers, overview, annotate


flask_app = Flask(__name__)
app = Dash(
    server=flask_app,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Image Explorer"


nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Explore", active="exact", href="/explore")),
        dbc.NavItem(
            dbc.NavLink("Overview", active="exact", href="/stats", id="dts-link")
        ),
        dbc.NavItem(dbc.NavLink("Data by Node", active="exact", href="/data")),
        dbc.NavItem(dbc.NavLink("Annotate", active="partial", href="/annotate")),
    ],
    pills=True,
    horizontal="end",
    class_name="ml-auto",
    justified=True,
)
CONTENT_STYLE = {
    "margin-left": "2rem",
    "margin-right": "1rem",
    "padding": "1rem 1rem",
}


@flask_app.route("/image/<path:path>")
def return_image(path):
    filepath = BASE_PATH + path
    print(filepath)
    return send_file(filepath, mimetype="image/jpg")


app.layout = html.Div(
    [
        dcc.Store(id="current_filename", storage_type="session"),
        dcc.Store(id="annot", storage_type="session"),
        dcc.Location(id="url", refresh=False),
        dbc.Row(
            [
                dbc.Col("", id="title", width=8),
                dbc.Col(nav, width=4),
            ]
        ),
        html.Div(id="page-content"),
    ],
    style=CONTENT_STYLE,
)


@app.callback(
    Output("page-content", "children"), Input("url", "pathname"), State("url", "href")
)
def display_page(pathname, href):
    if pathname == "/explore":
        return flowers.get_layout()
    elif pathname == "/stats":
        return chart.get_layout()
    elif pathname == "/data":
        return overview.get_layout()
    else:
        if pathname.startswith("/annotate"):
            href, pn = href.split("/annotate")
            img_url = href + "/image" + pn
            return annotate.get_layout(img_url)
        return flowers.get_layout()


if __name__ == "__main__":
    flask_app.run(host=HOST, port=PORT, debug=True)
