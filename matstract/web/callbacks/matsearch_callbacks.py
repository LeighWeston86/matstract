from dash.dependencies import Input, Output, State
from matstract.models.word_embeddings import EmbeddingEngine
from matstract.web.view.matsearch_app import serve_matlist
from matstract.nlp.data_preparation import DataPreparation


def bind(app):
    # updates similar words
    @app.callback(
        Output('relevant_materials_container', 'children'),
        [Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value')])
    def get_relevant_materials(_, search_text):
        if search_text is not None and search_text != "":
            dp = DataPreparation()
            ee = EmbeddingEngine()
            sentence = ee.phraser[dp.process_sentence(search_text.split())]
            most_similar = ee.find_similar_materials(sentence, min_count=50)
            return serve_matlist(ee.most_common_form(most_similar[:20]))
        else:
            return ""
