import dash_html_components as html
import dash_core_components as dcc

def serve_layout(db):
    """Generates the layout dynamically on every refresh"""

    return html.Div([
        serve_analogy(),
        serve_similarity()])


def serve_similarity():
    return html.Div([
                html.Div([
                    html.Span("Similarity", style={"fontWeight": "bold"}),
                    html.Br(),
                    dcc.Input(id='similar_words_input',
                              placeholder='e.g. LiMn2O4, anode, ...',
                              type='text'),
                    html.Button("Is similar to", id="similar_words_button"),
                    ]),
                html.Div('', id='similar_words_container', style={"padding": "0px 4px"})])


def serve_analogy():
    return html.Div([
                html.Span("Analogy", style={"fontWeight": "bold"}),
                html.Br(),
                dcc.Input(id='analogy_neg_1',
                          placeholder='e.g. LiCoO2, Co',
                          type='text'),
                html.Span(" is to "),
                dcc.Input(id='analogy_pos_1',
                          placeholder='e.g. cathode, CoO',
                          type='text'),
                html.Span(" as "),
                dcc.Input(id='analogy_pos_2',
                          placeholder='e.g. graphite, Al',
                          type='text'),
                html.Span(" is to "),
                html.Button("?",
                            id="analogy_run",
                            className="button-primary",
                            style={"textTransform": "none"}),
                html.Button("Load example",
                            id="mat2vec_surprise",
                            style={"textTransform": "none"}),
    ])


# def generate_analogy_str(l):
#     return html.Div([
#         html.Span(l[0]),
#         html.Span(" is to "),
#         html.Span(l[1]),
#         html.Span(" as "),
#         html.Span(l[2]),
#         html.Span(" is to "),
#         html.Span("?")])

# analogy_examples = html.Div([generate_analogy_str(analogy) for analogy in analogies], style={"paddingBottom": "10px"})
