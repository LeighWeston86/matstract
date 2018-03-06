import dash_html_components as html
import dash_core_components as dcc


def serve_layout(db, _):
    """Generates the layout dynamically on every refresh"""

    return [html.Div(serve_plain_abstract(db=db, empty=True), id="macro_ann_parent_div", className="row"),
            html.Div(serve_buttons(), className="row")]


def serve_plain_abstract(db, empty=False):
    random_abstract = {"abstract": "", "title": ""}
    doi = ""
    if not empty:
        random_abstract = db.abstracts_vahe.aggregate([{"$sample": {"size": 1}}]).next()
        doi = random_abstract['doi']

    return [
        html.Div([
            html.Span("doi: "), html.A(
                doi,
                href="https://doi.org/" + doi,
                target="_blank",
                id="doi_container")],
            className="row", style={"paddingBottom": "10px"}),
        html.Div(
            random_abstract["title"],
            style={'fontSize': 'large', "padding": "8px 0px", "borderTop": "1px solid black"}
        ),
        html.Div(
            random_abstract["abstract"],
            style={"borderBottom": "1px solid black", "padding-bottom": "10px"}
        ),
    ]


def serve_buttons():
    the_dropdown = dcc.Dropdown(
                        options=[
                            {'label': 'Experimental', 'value': 'experimental'},
                            {'label': 'Theoretical', 'value': 'theoretical'},
                            {'label': 'Both', 'value': 'both'},

                        ],
                        clearable=True,
                        id='macro_ann_type')
    not_rel_button = html.Button(
        "Not relevant",
        id="macro_ann_not_rel",
        className="button-primary")
    confirm_button = html.Button(
        "Confirm",
        id="macro_ann_confirm",
        className="button-primary")
    skip_button = html.Button(
        "Skip",
        id="macro_ann_skip",
        className="button")
    annotation_msg = html.Span(
        "",
        id="macro_ann_message",
        style={"color": "red", "paddingLeft": "5px"})
    return html.Div([
        not_rel_button,
        html.Span("Type: ", style={"paddingLeft": "10px"}),
        the_dropdown,
        confirm_button,
        skip_button,
        annotation_msg])
