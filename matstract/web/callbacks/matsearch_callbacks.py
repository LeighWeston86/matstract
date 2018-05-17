from dash.dependencies import Input, Output, State
from matstract.models.word_embeddings import EmbeddingEngine
from matstract.web.view.matsearch_app import matlist_figure
from matstract.nlp.data_preparation import DataPreparation
from matstract.web.view import trends_app
from matstract.web.view.summary_app import get_entities
import dash_core_components as dcc
import dash_html_components as html


def bind(app):
    # updates similar words
    @app.callback(
        Output('material_metrics', 'figure'),
        [Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value')])
    def get_relevant_materials(_, search_text):
        if search_text is not None and search_text != "":
            dp = DataPreparation()
            ee = EmbeddingEngine()
            sentence = ee.phraser[dp.process_sentence(search_text.split())]
            most_similar = ee.find_similar_materials(sentence, min_count=15)
            matlist = ee.most_common_form(most_similar[:50])
            material_names, material_scores, material_counts, _ = zip(*matlist)
            return matlist_figure(material_names, material_scores, material_counts)
        else:
            return ""

    @app.callback(
        Output('material_summary_div', 'children'),
        [Input('material_metrics', 'clickData'),
         Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value')])
    def display_trends(click_data, n_clicks, material):
        if click_data is not None:
            material = click_data["points"][0]["y"]  # name of the material
            layout = {"height": 300,
                      "title": material + " trends",
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
                        html.Div(get_entities(material))])]
        elif n_clicks is not None and material is not None and len(material) > 0:
            return "Click the graph to load material info."
        else:
            return ""

    @app.callback(
        Output('material_metrics', 'clickData'),
        [Input('matsearch_button', 'n_clicks')])
    def clear_clicks(_):
        return None
