from dash.dependencies import Input, Output, State
from matstract.utils import open_db_connection
import dash_html_components as html
import numpy as np
from numpy import DataSource
from matstract.nlp.data_preparation import DataPreparation

db = open_db_connection(local=False)

ds = DataSource()
# loading pre-trained embeddings and the dictionary
embeddings_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_phrases_sg_w8_n10_a001_pc20.wv.vectors.npy"
embeddings_file = ds.open(embeddings_url)
embeddings = np.load(ds.abspath(embeddings_url))
with ds.open("https://s3-us-west-1.amazonaws.com/materialsintelligence/model_phrases_sg_w8_n10_a001_pc20.tsv") as f:
    reverse_dictionary = [x.strip('\n') for x in f.readlines()]

norm = np.sqrt(np.sum(np.square(embeddings), 1, keepdims=True))
normalized_embeddings = embeddings / norm
del embeddings, norm  # to free up some memory

# # getting word embeddings from the database
# all_embeddings = db.embeddings.find()
# embeddings = np.empty((all_embeddings.count(), 200))
# for i, embedding in enumerate(all_embeddings):
#     print("Getting embedding #{}".format(i), end='\r')
#     embeddings[embedding["index"], :] = embedding["vector"]
# reverse_dictionary = db.embeddings.dictionary.find_one()["dict"]
#
# normalized_embeddings = embeddings / np.sqrt(np.sum(np.square(embeddings), 1, keepdims=True))


def bind(app):
    # updates similar words
    @app.callback(
        Output('similar_words_container', 'children'),
        [Input('similar_words_button', 'n_clicks')],
        [State('similar_words_input', 'value')])
    def get_similar_words(_, word):
        if word is not None and word != "":
            word = word.replace(" ", "_")
            word = DataPreparation.process_sentence([word])[0]
            # get all normalized word vectors
            try:
                word_embedding = [normalized_embeddings[reverse_dictionary.index(word)]]
            except Exception:
                return "Word not found in the dictionary"
            sim = np.dot(word_embedding, normalized_embeddings.T)
            top_k = 8  # number of nearest neighbors
            nearest = (-sim[0, :]).argsort()[1:top_k + 1]
            close_words = []
            for k in range(top_k):
                close_word = reverse_dictionary[nearest[k]]
                close_words.append(html.Span(close_word))
                close_words.append(html.Br())
            return close_words
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
        def get_word_vector(word):
            if word is not None and word != "":
                word = word.replace(" ", "_")
                word = dp.process_sentence([word])[0]
                # get all normalized word vectors
                try:
                    return normalized_embeddings[reverse_dictionary.index(word), :]
                except Exception:
                    return None
            else:
                return None

        pos_1_vec = get_word_vector(pos_1)
        neg_1_vec = get_word_vector(neg_1)
        pos_2_vec = get_word_vector(pos_2)
        if pos_1_vec is not None and neg_1_vec is not None and pos_2_vec is not None:
            diff_vec = (pos_2_vec + pos_1_vec - neg_1_vec)
            norm_diff = diff_vec / np.linalg.norm(diff_vec)  # unit length

            sim = np.dot([norm_diff], normalized_embeddings.T)
            top_k = 4  # number of nearest neighbors
            nearest = (-sim[0, :]).argsort()[:top_k]
            for k in range(top_k):
                close_word = reverse_dictionary[nearest[k]]
                if close_word not in [pos_1, neg_1, pos_2]:
                    return close_word
        else:
            return ""
