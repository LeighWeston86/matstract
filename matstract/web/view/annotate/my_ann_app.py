import dash_html_components as html
import dash_core_components as dcc
from matstract.models.annotation_builder import AnnotationBuilder
from urllib.parse import quote


def serve_layout(_, user_key, __):
    builder = AnnotationBuilder(local=False)
    my_annotations = builder.get_annotations(user=user_key)
    children = []
    for annotation in my_annotations:
        children.append(html.Li([
            html.Span([token["text"] + " " for token in annotation.tokens[0]], style={"fontWeight": "bold"}),
            html.Br(),
            html.Span(annotation.doi),
            html.Span(" "),
            serve_ann_options(quote(annotation.doi, safe="")),
            html.Br(),
            html.Span(str(annotation.labels))
        ]))

    return html.Div([html.H5("My Annotated Abstracts"),
                    html.Ol(children)])


def serve_ann_options(doi_str):
    return html.Span([
            dcc.Link("Materials", href="/annotate/token/" + doi_str + "/CHM&MAT&REF&MTC&DSC"),
            html.Span(' | '),
            dcc.Link(
                "Properties and Conditions",
                href="/annotate/token/" + doi_str + "/PRO&PVL&PUT&CON&CVL&CUT&PRC&SPL"),
            html.Span(' | '),
            dcc.Link("Methods and Applications", href="/annotate/token/" + doi_str + "/SMT&CMT&PMT&APL"),
            html.Span(' | '),
            dcc.Link("All", href="/annotate/token/" + doi_str + "/"),
            html.Span(' | '),
            dcc.Link("diff", href="/annotate/diff/" + doi_str + "/")
    ])
