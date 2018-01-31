import dash_html_components as html
import dash_core_components as dcc
from matstract.web.utils import open_db_connection
from chemdataextractor.doc import Paragraph

db = open_db_connection()


def serve_layout():
    """Generates the layout dynamically on every refresh"""
    return [html.Label('Annotate Materials and Corresponding Properties'),
            html.Div(serve_abstract(), id="annotation_container")]


def serve_abstract():
    """Returns a random abstract and refreshes annotation options"""
    # get a random paragraph
    random_abstract = db.abstracts.aggregate([{"$sample": {"size": 1}}]).next()

    # tokenize using chemdataextractor
    abs_tokens = Paragraph(random_abstract["abstract"]).tokens

    return [
        html.Div(build_tokens_html(abs_tokens), id="abstract_container"),
        html.Button("Next", id="annotate_next")
    ]


def build_tokens_html(tokens):
    """builds the HTML for tokenized paragraph"""
    html_builder = []
    for row in tokens:
        for elem in row:
            html_builder.append(" ")
            html_builder.append(html.Span(
                elem.text,
                id="abs-token-" + str(elem.start) + '-' + str(elem.end),
                className="abs-token",
            ))
    return html_builder