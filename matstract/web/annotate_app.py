import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi

from matstract.utils import open_db_connection
from matstract.models.AnnotationBuilder import AnnotationBuilder

db = open_db_connection(local=True)


def serve_layout(username):
    """Generates the layout dynamically on every refresh"""
    return [html.Div([html.Span("Logged in as "), html.Span(username, style={"fontWeight": "bold"})],
            id="user_info", className="row", style={"textAlign": "right"}),
            html.Div(serve_abstract(empty=True), id="annotation_parent_div", className="row"),
            html.Div(serve_buttons(), id="buttons_container", className="row")]


def serve_abstract(empty=False):
    """Returns a random abstract and refreshes annotation options"""
    ttl_tokens, abs_tokens = [], []
    doi = ""
    if not empty:
        # get a random paragraph
        random_abstract = db.abstracts_vahe.aggregate([{"$sample": {"size": 1}}]).next()
        doi = random_abstract['doi']

        # tokenize and get initial annotation
        ttl_tokens = AnnotationBuilder.get_tokens(random_abstract["title"])
        abs_tokens = AnnotationBuilder.get_tokens(random_abstract["abstract"])

    labels = [{'text': 'Material', 'value': 'material'},
              {'text': 'Inorganic Crystal', 'value': 'inorganic_crystal'},
              {'text': 'Main Material', 'value': 'main_material'},
              {'text': 'Keyword', 'value': 'keyword'}]

    return [
        dmi.AnnotationContainer(
            doi=doi,
            tokens=ttl_tokens + abs_tokens,
            labels=labels,
            className="annotation-container",
            selectedValue=labels[0]['value'],
            id="annotation_container"
        ),
        html.Div(serve_macro_annotation(), id="macro_annotation_container"),
        html.Div(doi, id="doi_container", style={"display": "none"})
    ]


def serve_macro_annotation():
    application_tags = db.abstract_tags.find({})
    tags = []
    for tag in application_tags:
        tags.append({'label': tag["tag"], 'value': tag['tag']})

    return [html.Div([html.Div("Type: ", className='two columns'),
            html.Div(dcc.Dropdown(
                options=[
                    {'label': 'Experimental', 'value': 'experimental'},
                    {'label': 'Theoretical', 'value': 'theoretical'},
                    {'label': 'Both', 'value': 'both'},

                ],
                clearable=True,
                id='abstract_type'
            ), className='five columns',
            ), html.Div(dcc.Dropdown(
                options=[
                    {'label': 'Inorganic Crystals', 'value': 'inorganic'},
                    {'label': 'Other Materials', 'value': 'other_materials'},
                    {'label': 'Not Materials', 'value': 'not_materials'},
                ],
                clearable=True,
                id='abstract_category'
            ), className='five columns',
            )], className='row', id="first_macro_row"),
            html.Div([html.Div("Tags: ", className="two columns"),
                     html.Div(dmi.DropdownCreatable(
                         options=tags,
                         id='abstract_tags',
                         multi=True,
                         value=''
                     ), className="ten columns")],
                     className="row")]


def serve_buttons():
    return [html.Button("Skip", id="annotate_skip", className="button"),
            html.Button("Confirm Annotation", id="annotate_confirm", className="button-primary")]
