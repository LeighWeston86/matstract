import dash
from flask_caching import Cache
import dash_core_components as dcc
import dash_html_components as html
from matstract.web import search_app, trends_app, extract_app, similar_app, annotate_app, keyword_app
from dash.dependencies import Input, Output, State
from matstract.extract.parsing import extract_materials, materials_extract
from matstract.models import keyword_extraction
import os
from flask import send_from_directory
import dash_materialsintelligence as dmi

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
css_files = ["dash_styles.css", "dash_extra.css", "skeleton.min.css",
             "googleapis.raleway.css", "googleapis.dosis.css",
             "webstract.css", "annotation_styles.css"]

stylesheets_links = []
for css in css_files:
    stylesheets_links.append(html.Link(
        rel='stylesheet',
        href='/styles/' + css
    ))

# # Adding Google Analytics
# app.scripts.append_script({"external_url":"https://s3-us-west-1.amazonaws.com/webstract/webstract_analytics.js"})

#### App Layout ####


### Header and Intro text ##


header = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Img(src="https://s3-us-west-1.amazonaws.com/webstract/matstract_with_text.png",
             style={
                 'height': '100px',
                 'float': 'right',
                 'position': 'relative',
                 'bottom': '20px',
                 'left': '10px'
             },
             ),
    html.H2('Matstract db',
            style={
                'position': 'relative',
                'top': '0px',
                'left': '27px',
                'font-family': 'Dosis',
                'display': 'inline',
                'font-size': '6.0rem',
                'color': '#4D637F'
            }),
    dmi.Annotatable(value="", className="", id=""),
    html.Nav(
        style={
            'margin': '10px 27px',
        },
        children=[
            dcc.Link("Search", href="/search", ),
            html.Span(' • '),
            dcc.Link("Trends", href="/trends"),
            html.Span(' • '),
            dcc.Link("Extract", href="/extract"),
            html.Span(' • '),
            dcc.Link("Similar Abstracts", href="/similar"),
            html.Span(' • '),
            dcc.Link("Annotate", href="/annotate"),
            html.Span(' • '),
            dcc.Link("Keyword Extraction", href="/keyword")
        ],
        id="nav_bar"),
    html.Br()
], className='row twelve columns', style={'position': 'relative', 'right': '15px'})


app.layout = html.Div([html.Div(stylesheets_links), header, html.Div(search_app.layout, id='page-content')],
                      className='container')

#### Callbacks ####


### General Callbacks ###


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')])
def display_page(path):
    if path == "/search":
        return search_app.layout
    elif path == "/trends":
        return trends_app.layout
    elif path == "/extract":
        return extract_app.layout
    elif path == "/similar":
        return similar_app.layout
    elif path == "/annotate":
        return annotate_app.serve_layout()
    elif path == "/keyword":
        return keyword_app.layout
    else:
        return search_app.layout


### Search App Callbacks ###


@cache.memoize(timeout=600)
@app.callback(
    Output('table-element', 'children'),
    # [Input('search-box', 'value')])
    [Input('search-button', 'n_clicks')],
    [State('search-box', 'value'), State('material-box', 'value')])
def update_table(n_clicks, search, material):
    if not material is None:
        table = search_app.generate_table(search, material)
    else:
        table = search_app.generate_table(search)
    return table


@cache.memoize(timeout=600)
@app.callback(
    Output('number_results', 'children'),
    [Input('search-button', 'n_clicks')],
    [State('search-box', 'value'), State('material-box', 'value')])
def update_num_results_label(n_clicks, search, material):
    results = search_app.get_search_results(search, material)
    if material or search:
        n = len(results)
        if n == 0:
            return "No Results"
        elif n == 10000:
            n = "> 10,000"
        return 'Showing {} of {} results'.format(min(100, n), n)
    else:
        return ''


### Extract App Callbacks ###

@app.callback(
    Output('extract-results', 'value'),
    [Input('extract-button', 'n_clicks')],
    [State('extract-textarea', 'value')])
def update_extract(n_clicks, text):
    if text is None:
        text = ''
    materials = extract_materials(text)
    materials = [m for m in materials if len(m) > 0]
    # return [{"name": m, "value": m} for m in materials]
    return ", ".join(materials)

@app.callback(
    Output('extract-highlighted', 'children'),
    [Input('extract-button', 'n_clicks')],
    [State('extract-textarea', 'value')])
def highlight_extracted(n_clicks, text):
    parsed, missed = materials_extract(text)
    highlighted = extract_app.highlighter(text, parsed, missed)
    return highlighted

@app.callback(
    Output('highlight-random', 'children'),
    [Input('random-abstract', 'n_clicks')])
def highlight_random(n_clicks):
    text = extract_app.random_abstract()
    parsed, missed = materials_extract(text)
    highlighted = extract_app.highlighter(text, parsed, missed)
    return highlighted


### Trends App Callbacks ###

@cache.memoize(timeout=600)
@app.callback(
    Output('trend', 'figure'),
    # [Input('search-box', 'value')])
    [Input('trends-button', 'n_clicks')],
    [State('trends-material-box', 'value'), State('trends-search-box', 'value')])
def update_graph(n_clicks, material, search):
    figure = trends_app.generate_trends_graph(search=search, material=material)
    figure["mode"] = "histogram"
    return figure


@cache.memoize(timeout=600)
@app.callback(
    Output('graph-label', 'children'),
    [Input('trends-button', 'n_clicks')],
    [State('trends-material-box', 'value'), State('trends-search-box', 'value')])
def update_title(n_clicks, material, search):
    if material is None:
        material = ''
    if search is None:
        search = ''
    if len(search) == 0:
        return "Number of papers mentioning {} per year:".format(material)
    else:
        if len(material) > 0:
            return "Number of papers related to '{}' mentioning {} per year:".format(search, material)

    return ''


"""
Annotation App Callbacks
"""
@app.callback(
    Output('annotation_container', 'children'),
    [Input('annotate_skip', 'n_clicks'),
     Input('annotate_confirm', 'n_clicks')])
def load_next_abstract(skip_clicks, confirm_clicks):
    # print("Skip: {}, Confirm: {}".format(skip_clicks, confirm_clicks))
    if confirm_clicks is not None:
        a = 1
        # do something to record the annotation
    return annotate_app.serve_abstract()




### Keywords App Callbacks ###
@app.callback(
    Output('extract-keywords', 'children'),
    [Input('keyword-button', 'n_clicks')],
    [State('keyword-material', 'value')])
def highlight_extracted(n_clicks, text):
    results =  [html.Div(word) for word in keyword_extraction.extract_keywords(text)]
    return results


@app.server.route('/styles/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'matstract/web/styles')
    return send_from_directory(static_folder, path)

