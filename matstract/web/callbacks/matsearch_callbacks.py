from dash.dependencies import Input, Output, State
from matstract.models.word_embeddings import EmbeddingEngine, number_to_substring
from matstract.web.view.matsearch_app import matlist_figure
from matstract.web.view import trends_app
from matstract.web.view.summary_app import get_entities
import dash_core_components as dcc
import dash_html_components as html
import regex


def bind(app):
    # updates similar words
    @app.callback(
        Output('material_metrics', 'figure'),
        [Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value'), State('matsearch_negative_input', 'value'),
         State('has_elements', 'value'), State('n_has_elements', 'value')])
    def get_relevant_materials(_, search_text, n_search_text, plus_elems, minus_elems):
        if search_text is not None and search_text != "":
            ee = EmbeddingEngine()

            # the positive word vectors
            sentence = ee.phraser[ee.dp.process_sentence(search_text.split())]

            # the negative word vectors
            n_sentence = ee.phraser[ee.dp.process_sentence(n_search_text.split())] \
                if n_search_text is not None and len(n_search_text) > 0 else None

            # finding materials sorted by similarity
            most_similar = ee.find_similar_materials(
                sentence=sentence,
                n_sentence=n_sentence,
                min_count=15,
                use_output_emb=False if ee.dp.is_simple_formula(sentence[0]) else True)

            # filtering the results by elements and returning top 50
            elem_filtered = ee.filter_by_elements(most_similar, plus_elems, minus_elems, max=50)

            # display top 50 results
            matlist = ee.most_common_form(elem_filtered[:50])
            material_names, material_scores, material_counts, _ = zip(*matlist)
            return matlist_figure([number_to_substring(name) for name in material_names], material_scores, material_counts)
        else:
            return ""

    @app.callback(
        Output('material_summary_div', 'children'),
        [Input('material_metrics', 'clickData'),
         Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value')])
    def display_trends(click_data, n_clicks, input_text):
        if click_data is not None:
            material = regex.sub(r"<sub>|</sub>", r"", click_data["points"][0]["y"])  # name of the material
            print(material)
            layout = {"height": 300,
                      "title": number_to_substring(material) + " trends",
                      "showlegend": False,
                      "margin": dict(l=60, r=40, t=40, b=40),
                      "xaxis": dict(
                          title="Year",
                      ),
                      "yaxis": dict(
                          title="Number of Publications"
                      )}
            figure = trends_app.generate_trends_graph(
                material=material,
                layout=layout)
            figure["mode"] = "histogram"
            graph = dcc.Graph(
                id='material_trend',
                figure=figure,
            )
            return [graph,
                    html.Div([
                        html.H6(material + " summary", style={
                            "fontWeight": "bold",
                            "marginTop": "20px"}),
                        html.Div(get_entities(material, class_name=""))])]
        elif n_clicks is not None and input_text is not None and len(input_text) > 0:
            return "Click the graph to load material info."
        else:
            return ""

    @app.callback(
        Output('material_metrics', 'clickData'),
        [Input('matsearch_button', 'n_clicks')])
    def clear_clicks(_):
        return None

    # updates analogies
    @app.callback(
        Output('matsearch_input', 'value'),
        [Input('matsearch_example', 'n_clicks')])
    def example_pos_input(n_clicks):
        if n_clicks is not None:
            return search_examples[n_clicks % len(search_examples)][0]

    # updates analogies
    @app.callback(
        Output('matsearch_negative_input', 'value'),
        [Input('matsearch_example', 'n_clicks')])
    def example_neg_input(n_clicks):
        if n_clicks is not None:
            return search_examples[n_clicks % len(search_examples)][1]

    # updates analogies
    @app.callback(
        Output('has_elements', 'value'),
        [Input('matsearch_example', 'n_clicks')])
    def example_has_elements(n_clicks):
        if n_clicks is not None:
            return search_examples[n_clicks % len(search_examples)][2]

    # updates analogies
    @app.callback(
        Output('n_has_elements', 'value'),
        [Input('matsearch_example', 'n_clicks')])
    def example_n_has_elements(n_clicks):
        if n_clicks is not None:
            return search_examples[n_clicks % len(search_examples)][3]


search_examples = [
    ["ferroelectric", "perovskite", None, None],
    ["solar cells", "", None, None],
    ["LiCoO2", "", ["Na"], None],
    ["thermoelectric", "", None, ["Bi"]],
    ["ferromagnetic", "", None, None],
    ["amorphous", "", None, None],
]
