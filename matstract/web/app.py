import dash
from flask_caching import Cache
import dash_core_components as dcc
import dash_html_components as html
from matstract.web import search_app, trends_app, extract_app, similar_app, \
    annotate_app, keyword_app
from dash.dependencies import Input, Output, State
from matstract.extract.parsing import extract_materials, materials_extract
import os
from flask import send_from_directory

import dash_materialsintelligence as dmi
from matstract.models.AnnotationBuilder import AnnotationBuilder
from matstract.utils import open_db_connection

db = open_db_connection(local=True)

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
        href='/styles/' + css
    ))

# # Adding Google Analytics
# app.scripts.append_script({"external_url": "https://s3-us-west-1.amazonaws.com/webstract/webstract_analytics.js"})

#### App Layout ####


### Header and Intro text ##

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
            dcc.Link("Keyword Extraction", href="/keyword"),
            html.Span(' • '),
            html.Span(html.A("Submit An Issue", href="https://github.com/materialsintelligence/matstract/issues/new",
                             style={"color": "red"}, target="_blank"))
        ],
        id="nav_bar"),
], className='row', style={'position': 'relative', 'right': '15px'})

app.layout = html.Div([
    html.Div(stylesheets_links),
    header,
    html.Div(search_app.layout, id='page-content'),
    html.Div("", id='user_key', style={'display': 'none'}),
    html.Div("", id='username', style={'display': 'none'})
    ],
    className='container main-container')


#### Callbacks ####


### General Callbacks ###

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('user_key', 'children')])
def display_page(path, user_key):
    if path == "/search":
        return search_app.layout
    elif path == "/trends":
        return trends_app.layout
    elif path == "/extract":
        return extract_app.layout
    elif path == "/similar":
        return similar_app.layout
    elif path == "/annotate":
        return annotate_app.serve_layout(user_key)
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
    if material is not None:
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
    if n_clicks is not None:
        if text is None:
            text = ''
        materials = extract_materials(text)
        materials = [m for m in materials if len(m) > 0]
        # return [{"name": m, "value": m} for m in materials]
        return ", ".join(materials)
    return ""


@app.callback(
    Output('extract-highlighted', 'children'),
    [Input('extract-button', 'n_clicks')],
    [State('extract-textarea', 'value')])
def highlight_extracted(n_clicks, text):
    if n_clicks is not None:
        parsed, missed = materials_extract(text)
        highlighted = extract_app.highlighter(text, parsed, missed)
        return highlighted
    return ""


@app.callback(
    Output('highlight-random', 'children'),
    [Input('random-abstract', 'n_clicks')])
def highlight_random(n_clicks):
    if n_clicks is not None:
        text = extract_app.random_abstract()
        parsed, missed = materials_extract(text)
        highlighted = extract_app.highlighter(text, parsed, missed)
        return highlighted
    return ""


### Trends App Callbacks ###

@cache.memoize(timeout=600)
@app.callback(
    Output('graph-label', 'children'),
    [Input('trends-button', 'n_clicks')],
    [State('trends-material-box', 'value'), State('trends-search-box', 'value')])
def update_title(n_clicks, material, search):
    if n_clicks is not None:
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
    else:
        return "Number of papers mentioning {} per year:".format("graphene")


@cache.memoize(timeout=600)
@app.callback(
    Output('trend', 'figure'),
    [Input('trends-button', 'n_clicks')],
    [State('trends-material-box', 'value'),
     State('trends-search-box', 'value'),
     State('trend', 'figure')])
def update_graph(n_clicks, material, search, current_figure):
    if n_clicks is not None:
        figure = trends_app.generate_trends_graph(search=search, material=material)
        figure["mode"] = "histogram"
        return figure
    else:
        return current_figure


### Annotation App Callbacks ###

@app.callback(
    Output('annotation_parent_div', 'children'),
    [Input('annotate_skip', 'n_clicks'),
     Input('annotate_confirm', 'n_clicks')],
    [State('annotation_container', 'tokens'),
     State('doi_container', 'children'),
     State('abstract_tags', 'value'),
     State('abstract_type', 'value'),
     State('abstract_category', 'value'),
     State('user_key_input', 'value'),
     State('completed_tasks', 'values')])
def load_next_abstract(
        skip_clicks,
        confirm_clicks,
        tokens,
        doi,
        abstract_tags,
        abstract_type,
        abstract_category,
        user_key,
        tasks):
    if confirm_clicks is not None:
        builder = AnnotationBuilder()
        if builder.get_username(user_key) is not None:
            if abstract_tags is not None:
                tag_values = [tag["value"].lower() for tag in abstract_tags]
            else:
                tag_values = None
            macro = {
                "tags": tag_values,
                "type": abstract_type,
                "category": abstract_category,
            }

            annotation = AnnotationBuilder.prepare_annotation(doi, tokens, macro, tasks, user_key)
            builder.insert_annotation(annotation)
            builder.update_tags(tag_values)
    return annotate_app.serve_abstract()

@app.callback(
    Output('annotation_message', 'children'),
    [Input('annotate_confirm', 'n_clicks')],
    [State('user_key_input', 'value')])
def feedback_message(n_clicks, user_key):
    if n_clicks is not None:
        builder = AnnotationBuilder()
        if builder.get_username(user_key) is None:
            return "Not authorised: Did not save the annotation!"
    return ""

@app.callback(
    Output('user_key', 'children'),
    [Input('user_key_input', 'value')])
def set_user_key(user_key):
    return user_key

@app.callback(
    Output('auth_info', 'children'),
    [Input('user_key_input', 'value')])
def set_user_info(user_key):
    builder = AnnotationBuilder()
    username = builder.get_username(user_key)
    return annotate_app.serve_auth_info(username)

### Keywords App Callbacks ###

@app.callback(
    Output('extract-keywords', 'children'),
    [Input('keyword-button', 'n_clicks')],
    [State('keyword-material', 'value')])
def keywords_table(n_clicks, text):
    if text is not None and text != '':
        return keyword_app.get_keywords(text)
    else:
        return ""


# def highlight_extracted(n_clicks, text):
#    if n_clicks is not None:
#        results = [html.Div(word) for word in keyword_extraction.extract_keywords(text)]
#        return results
#    else:
#        return []


@app.server.route('/styles/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'matstract/web/styles')
    return send_from_directory(static_folder, path)
