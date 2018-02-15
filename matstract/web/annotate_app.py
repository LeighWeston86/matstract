import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi

from matstract.utils import open_db_connection
from matstract.models.AnnotationBuilder import AnnotationBuilder

import pprint
db = open_db_connection()


def serve_layout():
    """Generates the layout dynamically on every refresh"""
    return html.Div(serve_abstract(), id="annotation_container")


def serve_abstract():
    """Returns a random abstract and refreshes annotation options"""
    # get a random paragraph
    random_abstract = db.abstracts_vahe.aggregate([{"$sample": {"size": 1}}]).next()

    builder = AnnotationBuilder()
    # tokenize and get initial annotation
    ttl_tokens, ttl_annotations = builder.get_tokens(random_abstract["title"])
    abs_tokens, abs_annotations = builder.get_tokens(random_abstract["abstract"])

    return [
        html.Div(serve_labels(), id="label_container"),
        html.Div(dmi.AnnotationContainer(
            tokens=ttl_tokens,
            annotations=ttl_annotations,
            id=random_abstract["doi"]
        ), className="row", id="title_container", style={"fontSize": "large"}),
        html.Div(dmi.AnnotationContainer(
            tokens=abs_tokens,
            annotations=abs_annotations,
            id=random_abstract["doi"]
        ), className="row", id="abstract_container"),
        html.Div(serve_macro_annotation(), id="macro_annotation_container"),
        # html.Div(list_cde_cems(abs_cems), id='token_container'),
        html.Div(serve_buttons(), id="buttons_container", className="row")
    ]


def serve_macro_annotation():
    return [html.Div([html.Div("Type: ", className='two columns'),
            html.Div(dcc.Dropdown(
                options=[
                    {'label': 'Experimental', 'value': 'experimental'},
                    {'label': 'Theoretical', 'value': 'theoretical'},
                    {'label': 'Both', 'value': 'both'},
                    {'label': 'Unclear', 'value': 'unclear'},

                ],
                value='experimental',
                clearable=False,
                id='abstract_type'
            ), className='five columns',
            ), html.Div(dcc.Dropdown(
                options=[
                    {'label': 'Inorganic Crystals', 'value': 'inorganic'},
                    {'label': 'Other Materials', 'value': 'other_materials'},
                    {'label': 'Not Materials', 'value': 'not_materials'},
                ],
                value='inorganic',
                clearable=False,
                id='abstract_category'
            ), className='five columns',
            )], className='row'),
            html.Div([html.Div("Applications: ", className="two columns"),
                     html.Div(dcc.Dropdown(
                         options=[
                             {'label': 'Thermoelectric', 'value': 'thermoelectric'},
                             {'label': 'Battery', 'value': 'battery'},
                             {'label': 'Magnetic', 'value': 'magnetic'},
                             {'label': 'Other', 'value': 'other'}
                         ],
                         value='',
                         id='abstract_tags',
                         multi=True
                     ), className="ten columns")],
                     className="row")]


def build_tokens_html(tokens, cems):
    """builds the HTML for tokenized paragraph"""
    cde_cem_starts = [cem.start for cem in cems]
    html_builder = []
    for row in tokens:
        for elem in row:
            selected_state = False
            extra_class = ''
            if elem.start in cde_cem_starts:
                selected_state = True
                extra_class = ' mtl highlighted'
            html_builder.append(" ")
            html_builder.append(dmi.Annotatable(
                id="token-" + str(elem.start) + '-' + str(elem.end),
                value=elem.text,
                className="token",
                isSelected=selected_state,
            ))
    return html_builder


# def list_cde_cems(cems):
#     html_builder = []
#     for cem in cems:
#         html_builder.append(html.Div([
#             html.Div(
#                 cem.text,
#                 id="cde-cem-" + str(cem.start) + '-' + str(cem.end),
#                 className="six columns",
#             ), html.Div(dcc.Dropdown(
#                 options=[
#                     {'label': 'Material', 'value': 'mtl'},
#                     {'label': 'Inorganic Crystal', 'value': 'igc'},
#                 ],
#                 value='mtl',
#                 ),
#                 className="six columns",
#             )],
#             className="row",
#         ))
#     return html_builder


def serve_buttons():
    return [html.Button("Skip", id="annotate_skip", className="button"),
            html.Button("Confirm Annotation", id="annotate_confirm", className="button-primary")]


def serve_labels():
    return html.Div([
        html.Div(html.Span("Labels: "), className="two columns"),
        html.Div([
            html.Span("Material", className="highlighted mtl label"),
            html.Span("Inorganic Crystal", className="highlighted inrg label"),
            html.Span("Main Material", className="highlighted main_mtl label"),
            html.Br(),
            html.Span("Property Name", className="highlighted prop_name label"),
            html.Span("Property Value", className="highlighted prop_val label"),
            html.Span("Property Unit", className="highlighted prop_unit label")]
            , className="ten columns")], className="row")
