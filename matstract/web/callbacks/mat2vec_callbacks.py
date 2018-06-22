from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table_experiments as dt
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
            close_words, scores = ee.close_words(word, top_k=8)
            print(close_words)
            return dt.DataTable(
                rows=[{"#": i+1,
                       'Words and phrases similar to "{}"'.format(word): w.replace("_", " "),
                       "Cosine similarity": int(scores[i]*1000)/1000}
                      for i, w in enumerate(close_words)],
                row_selectable=False,
                filterable=False,
                editable=False,
                sortable=False,
                column_widths=[25, None, 140],
                id='analogies_table'
            )
            # return [html.Span(["({:.2f}) {}".format(scores[i], close_word.replace("_", " ")), html.Br()])
            #         for i, close_word in enumerate(close_words)]
        else:
            return ""

    # updates analogies
    @app.callback(
        Output('analogy_run', 'children'),
        [Input("analogy_run", "n_clicks"),
         Input('analogy_pos_1', 'value'),
         Input('analogy_neg_1', 'value'),
         Input('analogy_pos_2', 'value')])
    def get_analogy(n_clicks, pos_1, neg_1, pos_2):
        if n_clicks is not None and \
                pos_1 is not None and \
                pos_1 != "" and \
                neg_1 is not None and \
                neg_1 != "" and \
                pos_2 is not None and \
                pos_2 != "":
            ee = EmbeddingEngine()
            pos_1 = ee.phraser[ee.dp.process_sentence(pos_1.split())[0]]
            neg_1 = ee.phraser[ee.dp.process_sentence(neg_1.split())[0]]
            pos_2 = ee.phraser[ee.dp.process_sentence(pos_2.split())[0]]
            pos_1_vec = ee.get_word_vector(pos_1[0])
            neg_1_vec = ee.get_word_vector(neg_1[0])
            pos_2_vec = ee.get_word_vector(pos_2[0])
            if pos_1_vec is not None and neg_1_vec is not None and pos_2_vec is not None:
                diff_vec = pos_2_vec + pos_1_vec - neg_1_vec
                norm_diff = diff_vec / np.linalg.norm(diff_vec, axis=0)  # unit length
                close_words = ee.close_words(norm_diff, exclude_self=False)[0]
                print(close_words)
                for close_word in close_words:
                    if close_word not in [pos_1[0], neg_1[0], pos_2[0]]:
                        return close_word.replace("_", " ")
            else:
                return "?"
        else:
            return "?"

    # updates analogies
    @app.callback(
        Output('analogy_run', 'n_clicks'),
        [Input('analogy_pos_1', 'value'),
         Input('analogy_neg_1', 'value'),
         Input('analogy_pos_2', 'value')])
    def get_analogy(_, __, ___):
        return None

    # updates analogies
    @app.callback(
        Output('analogy_neg_1', 'value'),
        [Input('mat2vec_surprise', 'n_clicks')])
    def surprise_neg1(n_clicks):
        if n_clicks is not None:
            return analogies[n_clicks % len(analogies)][0]

    # updates analogies
    @app.callback(
        Output('analogy_pos_1', 'value'),
        [Input('mat2vec_surprise', 'n_clicks')])
    def surprise_pos1(n_clicks):
        if n_clicks is not None:
            return analogies[n_clicks % len(analogies)][1]

    # updates analogies
    @app.callback(
        Output('analogy_pos_2', 'value'),
        [Input('mat2vec_surprise', 'n_clicks')])
    def surprise_pos2(n_clicks):
        if n_clicks is not None:
            return analogies[n_clicks % len(analogies)][2]


analogies = [
    ["CoFe", "ferromagnetic", "CoO", "antiferromagnetic"],
    ["K", "temperature", "V", "voltage"],
    ["CdS", "wurtzite", "CdTe", "zincblende"],
    ["Co", "hcp", "Fe", "bcc"],
    ["Fe", "Fe2O3", "Ni", "NiO"],
    ["LiCoO2", "graphite", "cathode", "anode"]
]