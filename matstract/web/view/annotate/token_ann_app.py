import dash_html_components as html
import dash_materialsintelligence as dmi
from matstract.models.annotation_builder import AnnotationBuilder
from urllib.parse import unquote


def serve_layout(db, user_key, attrs):
    """Generates the layout dynamically on every refresh"""
    labels, show_labels, doi = None, None, None
    if len(attrs) == 1:
        labels = attrs[0]
    elif len(attrs) == 2:
        doi = unquote(attrs[0])
        labels = attrs[1]
    if labels == "":
        labels = None
    if labels is not None:
        show_labels = str(labels).split('&')
    return [html.Div(serve_abstract(
                db,
                user_key=user_key,
                empty=doi is None,
                doi=doi,
                show_labels=show_labels),
                id="annotation_parent_div",
            className="row"),
            html.Div("", id="annotation_message", style={"color": "red", "paddingLeft": "5px"}),
            html.Div(labels, id="annotation_labels", style={"display": "none"})]


def serve_abstract(db,
                   user_key,
                   empty=False,
                   show_labels=None,
                   doi=None,
                   past_tokens=None):
    """Returns a random abstract and refreshes annotation options"""
    if empty:
        tokens = []
        existing_labels = []
    else:
        builder = AnnotationBuilder(local=False)
        # get a random paragraph
        random_abstract = builder.get_abstract(good_ones=False, doi=doi, user_key=user_key, only_relevant=True)
        doi = random_abstract['doi']
        # tokenize and get initial annotation
        cems = False
        # if show_labels is not None and "MAT" in show_labels:
        #     cems = True
        tokens, existing_labels = builder.get_tokens(random_abstract, user_key, cems)
        if past_tokens is not None:
            tokens = past_tokens

    # labels for token-by-token annotation
    labels = AnnotationBuilder.LABELS

    macro_display = "none"
    passive_labels = []
    if show_labels is not None:
        passive_labels = [pl for pl in labels if pl["value"] in existing_labels and pl["value"] not in show_labels]
        labels = [label for label in labels if label["value"] in show_labels]
        if "application" in show_labels:
            macro_display = "block"

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
            tokens=tokens,
            labels=labels,
            passiveLabels=passive_labels,
            className="annotation-container",
            selectedValue=labels[0]['value'],
            id="annotation_container"
        ),
        html.Div(serve_macro_annotation(db, macro_display), id="macro_annotation_container"),
        html.Div("", className="row instructions", id="annotation_instructions"),
        html.Div(serve_buttons(), id="buttons_container", className="row")
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
    return [html.Button("Confirm", id="annotate_confirm", className="button-primary"),
            html.Button("Flag", id="token_ann_flag", className="ann-flag"),
            html.Button("Skip", id="annotate_skip", className="button")]
