import os

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi
from flask import send_from_directory

from dash.dependencies import Input, Output
from matstract.web.view import new_search_app, summary_app, matsearch_app
from matstract.web.callbacks import new_search_callbacks, summary_callbacks, matsearch_callbacks
from matstract.models.database import AtlasConnection

# app config
app = dash.Dash()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.suppress_callback_exceptions = True
app.title = "Matstract - Rediscovering Materials"

db = AtlasConnection().db

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
            dcc.Link("Material Summary", href="/summary"),
            html.Span(u" \u2022 "),
            dcc.Link("Mat2Vec Search", href="/matsearch"),
            html.Span(u" \u2022 "),
            html.A("Material Clusters", href="https://plot.ly/~vtshitoyan/6/markers-and-text/#/"),
            html.Span(u" \u2022 "),
            html.A("Word Clusters", href="https://plot.ly/~vtshitoyan/8/"),
        ],
        id="nav_bar")


app.layout = html.Div([
    html.Div(stylesheets_links, style={"display": "none"}),
    header,
    nav,
    html.Div("", id="app_container")], className='container main-container')


@app.callback(
    Output('app_container', 'children'),
    [Input('url', 'pathname')])
def display_page(path):
    path = str(path)
    if path.startswith("/search"):
        return new_search_app.serve_layout(path)
    elif path == "/summary":
         return summary_app.layout
    elif path == "/matsearch":
         return matsearch_app.serve_layout(db)
    else:
        return new_search_app.serve_layout()


# setting the static path for loading css files
@app.server.route('/static/css/<path:path>')
def get_stylesheet(path):
    static_folder = os.path.join(os.getcwd(), 'matstract/web/static/css')
    return send_from_directory(static_folder, path)


new_search_callbacks.bind(app)
summary_callbacks.bind(app)
matsearch_callbacks.bind(app)
