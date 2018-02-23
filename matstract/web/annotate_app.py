import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi

from matstract.utils import open_db_connection
from matstract.models.AnnotationBuilder import AnnotationBuilder

import pprint
db = open_db_connection(local=True)


def serve_layout():
    """Generates the layout dynamically on every refresh"""
    return [html.Div(dmi.AnnotationContainer(
            tokens=[[]],
            annotations=[[]],
            labels=[],
            className="annotation-container",
            selectedValue=None,
            id="annotation_container"
            ), id="annotation_parent_div", className="row"),
            html.Div(serve_buttons(), id="buttons_container", className="row")]


def serve_abstract():
    """Returns a random abstract and refreshes annotation options"""
    # get a random paragraph
    random_abstract = db.abstracts_vahe.aggregate([{"$sample": {"size": 1}}]).next()

    builder = AnnotationBuilder()
    # tokenize and get initial annotation
    ttl_tokens, ttl_annotations = builder.get_tokens(random_abstract["title"])
    abs_tokens, abs_annotations = builder.get_tokens(random_abstract["abstract"])

    labels = [{'text': 'Material', 'value': 'material'},
              {'text': 'Inorganic Crystal', 'value': 'inorganic_crystal'},
              {'text': 'Main Material', 'value': 'main_material'},
              {'text': 'Keyword', 'value': 'keyword'}]

    return [
        dmi.AnnotationContainer(
            tokens=[ttl_tokens, abs_tokens],
            annotations=[ttl_annotations, abs_annotations],
            labels=labels,
            className="annotation-container",
            selectedValue=labels[0]['value'],
            id="annotation_container"
        ),
        html.Div(serve_macro_annotation(), id="macro_annotation_container"),
    ]


def serve_macro_annotation():
    application_tags = db.abstract_tags.find({})
    tags = []
    for tag in application_tags:
        tags.append({'label': tag["tag"], 'value': tag['tag']})
    print(tags)

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
                         multi=True
                     ), className="ten columns")],
                     className="row")]

def serve_buttons():
    return [html.Button("Skip", id="annotate_skip", className="button"),
            html.Button("Confirm Annotation", id="annotate_confirm", className="button-primary")]
