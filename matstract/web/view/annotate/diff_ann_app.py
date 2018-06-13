import dash_html_components as html
import dash_materialsintelligence as dmi
from matstract.models.annotation_builder import AnnotationBuilder
from urllib.parse import unquote


def serve_layout(_, user_key, attrs):
    """Generates the layout dynamically on every refresh"""
    if len(attrs) >= 1:
        doi = unquote(attrs[0])
    else:
        doi = None
    return html.Div(serve_abstract(
                user_key=user_key,
                doi=doi),
                id="diff_view_div", className="row")


def serve_abstract(user_key,
                   doi=None):
    """Returns a random abstract and refreshes annotation options"""
    builder = AnnotationBuilder(local=False)
    diff_tokens, message = builder.get_diff_tokens(doi=doi, user=user_key)
    if diff_tokens is not None:
        return [
            html.Div([
                html.Span("doi: "), html.A(
                    doi,
                    href="https://doi.org/" + str(doi),
                    target="_blank",
                    id="doi_container")],
                className="row", style={"paddingBottom": "10px"}),
            dmi.AnnotationContainer(
                doi=doi,
                tokens=diff_tokens,
                labels=[],
                className="annotation-container",
                selectedValue=None,
                id="annotation_container"
            ),
        ]
    return message
