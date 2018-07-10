import os

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi
from flask import send_from_directory

from dash.dependencies import Input, Output
from matstract.web.view import new_search_app, trends_app, summary_app

# app config
app = dash.Dash()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.suppress_callback_exceptions = True
app.title = "Matstract - Rediscovering Materials"

# loading css files
css_files = ["dash_extra.css", "skeleton.min.css", "webstract.css",
             "googleapis.raleway.css", "googleapis.dosis.css"]
stylesheets_links = [html.Link(rel='stylesheet', href='/static/css/' + css) for css in css_files]

header = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(dmi.DropdownCreatable(),style={"display": "none"}),
    html.Img(src="https://s3-us-west-1.amazonaws.com/matstract/matstract_with_text.png",
         style={
             'height': '50px',
             'float': 'right',
             'max-width': "100%",
             "margin": "5px 3px 20px 5px",
             "clear": "both"
         }),
    html.H4("Rediscovering Materials",
            className="headline",
            style={
                "float": "left",
                "margin": "15px 5px 10px 1px",
                "whiteSpace": "nowrap"})
], className="row")

nav = html.Nav(
        style={"margin": "10px 1px", "borderBottom": "1px solid #eee"},
        children=[
            dcc.Link("Search", href="/search"),
            html.Span(u" \u2022 "),
            dcc.Link("Trends", href="/trends"),
            html.Span(u" \u2022 "),
            dcc.Link("Material Summary", href="/summary"),
        ],
        id="nav_bar")


app.layout = html.Div([
    html.Div(stylesheets_links, style={"display": "none"}),
    header,
    nav,
    html.Div("", id="app-container")], className='container main-container')


@app.callback(
    Output('app-container', 'children'),
    [Input('url', 'pathname')])
def display_page(path):
    path = str(path)
    if path.startswith("/search"):
        return new_search_app.serve_layout()
    elif path == "/trends":
        return trends_app.layout
    elif path == "/summary":
         return summary_app.layout
    else:
        return new_search_app.serve_layout()


# setting the static path for loading css files
@app.server.route('/static/css/<path:path>')
def get_stylesheet(path):
    static_folder = os.path.join(os.getcwd(), 'matstract/web/static/css')
    return send_from_directory(static_folder, path)


