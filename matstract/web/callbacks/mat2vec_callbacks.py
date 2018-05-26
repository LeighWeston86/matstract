from dash.dependencies import Input, Output, State
import dash_html_components as html
import numpy as np
from matstract.models.word_embeddings import EmbeddingEngine


def bind(app):
    # updates similar words
    @app.callback(
        Output('similar_words_container', 'children'),
        [Input('similar_words_button', 'n_clicks')],
        [State('similar_words_input', 'value')])
    def get_similar_words(_, word):
        if word is not None and word != "":
            ee = EmbeddingEngine()
            close_words, scores = ee.close_words(word)
            return [html.Span(["({:.2f}) {}".format(scores[i], close_word.replace("_", " ")), html.Br()])
                    for i, close_word in enumerate(close_words)]
        else:
            return ""

    # updates analogies
    @app.callback(
        Output('analogy_container', 'children'),
        [Input("analogy_run", "n_clicks")],
        [State('analogy_pos_1', 'value'),
         State('analogy_neg_1', 'value'),
         State('analogy_pos_2', 'value')])
    def get_analogy(_, pos_1, neg_1, pos_2):
        ee = EmbeddingEngine()
        pos_1 = ee.phraser[ee.dp.process_sentence(pos_1.split())]
        neg_1 = ee.phraser[ee.dp.process_sentence(neg_1.split())]
        pos_2 = ee.phraser[ee.dp.process_sentence(pos_2.split())]
        pos_1_vec = ee.get_word_vector(pos_1[0])
        neg_1_vec = ee.get_word_vector(neg_1[0])
        pos_2_vec = ee.get_word_vector(pos_2[0])
        if pos_1_vec is not None and neg_1_vec is not None and pos_2_vec is not None:
            diff_vec = pos_2_vec + pos_1_vec - neg_1_vec
            norm_diff = diff_vec / np.linalg.norm(diff_vec, axis=0)  # unit length
            close_words = ee.close_words(norm_diff, exclude_self=False)[0]
            for close_word in close_words:
                if close_word not in [pos_1[0], neg_1[0], pos_2[0]]:
                    return close_word.replace("_", " ")
        else:
            return ""
