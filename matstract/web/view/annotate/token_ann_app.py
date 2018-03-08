import dash_html_components as html
import dash_materialsintelligence as dmi
from matstract.models.AnnotationBuilder import AnnotationBuilder


def serve_layout(db, labels):
    """Generates the layout dynamically on every refresh"""
    show_labels = None
    if labels is not None:
        show_labels = str(labels).split('&')
    return [html.Div(serve_abstract(
                db,
                empty=True,
                show_labels=show_labels),
                id="annotation_parent_div",
            className="row"),
            html.Div(serve_buttons(), id="buttons_container", className="row"),
            html.Div(labels, id="annotation_labels", style={"display": "none"})]


def serve_abstract(db, empty=False, show_labels=None):
    """Returns a random abstract and refreshes annotation options"""
    ttl_tokens, abs_tokens = [], []
    doi = ""
    if not empty:
        # get a random paragraph
        random_abstract = db.abstracts_vahe.aggregate([{"$sample": {"size": 1}}]).next()
        doi = random_abstract['doi']
        # tokenize and get initial annotation
        pre_annotate = False
        if show_labels is not None and "material" in show_labels:
            pre_annotate = True

        ttl_tokens = AnnotationBuilder.get_tokens(random_abstract["title"], pre_annotate)
        abs_tokens = AnnotationBuilder.get_tokens(random_abstract["abstract"], pre_annotate)

    # labels for token-by-token annotation
    labels = AnnotationBuilder.LABELS

    macro_display = "none"
    if show_labels is not None:
        labels = [label for label in labels if label["value"] in show_labels]
        if "application" in show_labels:
            macro_display = "block"

    return [
        html.Div([
            html.Span("doi: "), html.A(
                doi,
                href="https://doi.org/" + doi,
                target="_blank",
                id="doi_container")],
            className="row", style={"paddingBottom": "10px"}),
        dmi.AnnotationContainer(
            doi=doi,
            tokens=ttl_tokens + abs_tokens,
            labels=labels,
            className="annotation-container",
            selectedValue=labels[0]['value'],
            id="annotation_container"
        ),
        html.Div(serve_macro_annotation(db, macro_display), id="macro_annotation_container"),
    ]


def serve_macro_annotation(db, display):
    """Things like experimental vs theoretical, inorganic vs organic, etc."""
    tags = []
    for tag in db.abstract_tags.find({}):
        tags.append({'label': tag["tag"], 'value': tag['tag']})

    return [html.Div([html.Div("Tags: ", className="two columns"),
                     html.Div(dmi.DropdownCreatable(
                         options=tags,
                         id='abstract_tags',
                         multi=True,
                         value=''
                     ), className="ten columns")],
                     className="row", style={"display": display})]


def serve_buttons():
    """Confirm and skip buttons"""
    return [html.Button("Skip", id="annotate_skip", className="button"),
            html.Button("Confirm", id="annotate_confirm", className="button-primary"),
            html.Button("Flag", id="token_ann_flag", className="ann-flag"),
            html.Span("", id="annotation_message", style={"color": "red", "paddingLeft": "5px"})]