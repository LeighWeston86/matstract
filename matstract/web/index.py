import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_materialsintelligence as dmi

from flask_caching import Cache

from flask import send_from_directory
from matstract.web.view import annotate_app, similar_app, \
    search_app, keyword_app, trends_app, mat2vec_app, matsearch_app, extract_app, summary_app
from matstract.web.callbacks import search_callbacks, annotate_callbacks, summary_callbacks, \
    keyword_callbacks, trends_callbacks, similar_callbacks, mat2vec_callbacks, matsearch_callbacks, extract_callbacks
from dash.dependencies import Input, Output, State
from matstract.models.database import AtlasConnection

import os

db = AtlasConnection().db

app = dash.Dash()
server = app.server

# To include local css and js files
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.suppress_callback_exceptions = True
app.title = "Matstract"

cache = Cache(server, config={"CACHE_TYPE": "simple"})

### CSS settings ###
BACKGROUND = 'rgb(230, 230, 230)'
COLORSCALE = [[0, "rgb(244,236,21)"], [0.3, "rgb(249,210,41)"], [0.4, "rgb(134,191,118)"],
              [0.5, "rgb(37,180,167)"], [0.65, "rgb(17,123,215)"], [1, "rgb(54,50,153)"]]

# loading css files
css_files = ["dash_extra.css", "skeleton.min.css",
             "googleapis.raleway.css", "googleapis.dosis.css",
             "webstract.css", "annotation_styles.css"]

stylesheets_links = []
for css in css_files:
    stylesheets_links.append(html.Link(
        rel='stylesheet',
        href='/static/css/' + css
    ))

# # Adding Google Analytics
# app.scripts.append_script({"external_url": "https://s3-us-west-1.amazonaws.com/webstract/webstract_analytics.js"})

#### App Layout ####

header = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        html.Div(
        html.Img(src="https://s3-us-west-1.amazonaws.com/webstract/matstract_with_text.png",
             style={
                 'width': '400px',
                 'float': 'right',
                 'max-width': "100%"
             })),
        html.H2(
            'Matstract db',
            style={
                'padding-left': '27px',
                'font-family': 'Dosis',
                'font-size': '6.0rem',
                'color': '#4D637F',
                "float": "left",
                "whiteSpace": "nowrap"
            }),
    ]),
    dmi.Annotatable(value="", className="dummy_class", id="dummy_span"),
    html.Nav(
        style={
            'margin': '10px 27px',
            'clear': "both"
        },
        children=[
            dcc.Link("Search", href="/search"),
            html.Span(u" \u2022 "),
            dcc.Link("Trends", href="/trends"),
            html.Span(u" \u2022 "),
            dcc.Link("Extract", href="/extract"),
            html.Span(u" \u2022 "),
            dcc.Link("Similar Abstracts", href="/similar"),
            html.Span(u" \u2022 "),
            dcc.Link("Annotate", href="/annotate"),
            html.Span(u" \u2022 "),
            dcc.Link("Keyword Extraction", href="/keyword"),
            html.Span(u" \u2022 "),
            dcc.Link("Mat2Vec", href="/mat2vec"),
            html.Span(u" \u2022 "),
            dcc.Link("MatSearch", href="/matsearch"),
            html.Span(u" \u2022 "),
            dcc.Link("Material Summary", href="/summary"),
            html.Span(u" \u2022 "),
            html.Span(html.A("Submit An Issue", href="https://github.com/materialsintelligence/matstract/issues/new",
                             style={"color": "red"}, target="_blank"))
        ],
        id="nav_bar"),
], className='row', style={'position': 'relative', 'right': '15px'})

app.layout = html.Div([
    html.Div(stylesheets_links),
    header,
    html.Div("", id='page-content'),
    html.Div("", id='user_key', style={'display': 'none'}),
    html.Div("", id='username', style={'display': 'none'})
    ],
    className='container main-container')


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('user_key', 'children')])
def display_page(path, user_key):
    # tr.print_diff()
    path = str(path)
    if path.startswith("/search"):
        return search_app.serve_layout(path)
    elif path == "/trends":
        return trends_app.layout
    elif path == "/extract":
        return extract_app.layout
    elif path == "/summary":
         return summary_app.layout
    elif path == "/similar":
        return similar_app.layout
    elif path.startswith("/annotate"):
        return annotate_app.serve_layout(db, user_key, path)
    elif path == "/keyword":
        return keyword_app.layout
    elif path == "/mat2vec":
        return mat2vec_app.serve_layout(db)
    elif path == "/matsearch":
        return matsearch_app.serve_layout(db)
    else:
        return search_app.serve_layout(path)


@app.server.route('/static/css/<path:path>')
def get_stylesheet(path):
    static_folder = os.path.join(os.getcwd(), 'matstract/web/static/css')
    return send_from_directory(static_folder, path)


# App Callbacks
search_callbacks.bind(app, cache)
trends_callbacks.bind(app, cache)
extract_callbacks.bind(app)
summary_callbacks.bind(app)
keyword_callbacks.bind(app)
annotate_callbacks.bind(app)
similar_callbacks.bind(app, cache)
mat2vec_callbacks.bind(app)
matsearch_callbacks.bind(app)
