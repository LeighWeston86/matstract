from dash.dependencies import Input, Output, State
import operator
import numpy as np
from matstract.web.callbacks.mat2vec_callbacks import normalized_embeddings, reverse_dictionary, dp, word2index
from matstract.web.view.matsearch_app import serve_matlist
from gensim.models.phrases import Phraser, Phrases
from collections import defaultdict


phrases = Phrases(threshold=0.0001, min_count=1)
vocab = defaultdict(int)
for word in reverse_dictionary:
    if "_" in word:
        vocab[str.encode(word)] = 100  # phrase
    else:
        vocab[str.encode(word)] = 1  # single word
phrases.vocab = vocab
phraser = Phraser(phrases)
del vocab, phrases

formulas = dp.load_obj("/Users/vtshitoyan/dev/ml/gensim/data/abstracts_matnorm_lower_punct_units_formula")
ABBR_LIST = ["C41H11O11", "PV", "OPV", "PV12", "CsOS", "CsKPSV", "CsPS", "CsHIOS", "OPV",
             "CsPSV", "CsOPV", "CsIOS", "BCsIS", "CsPrS", "CEsH", "KP307", "AsOV", "CEsS",
             "COsV", "CNoO", "BEsF", "I2P3", "KP115", "BCsIS", "C9705IS", "ISC0501", "B349S",
             "CISe", "CISSe", "CsIPS", "CEsP", "BCsF", "CsFOS", "BCY10", "C12P", "EsHP", "CsHP",
             "C2K8", "CsOP", "EsHS", "CsHS", "C3P", "C50I", "CEs"]
for abbr in ABBR_LIST:
    formulas.pop(abbr, None)

total_counts = [0] * len(formulas)
for i, formula in enumerate(formulas):
    for writing in formulas[formula]:
        total_counts[i] += formulas[formula][writing]


def find_similar_materials(sentence, min_count):
    similarities = dict()
    avg_embedding = np.zeros(200)
    for word in sentence:
        if word in word2index:
            avg_embedding += normalized_embeddings[word2index[word]]
    avg_embedding = avg_embedding/len(sentence)
    for i, formla in enumerate(formulas):
        if total_counts[i] > min_count:
            similarities[formla] = np.dot(avg_embedding, normalized_embeddings[word2index[formla]])
    return sorted(similarities.items(), key=lambda x:x[1], reverse=True)


def most_common_form(form_list):
    common_form_score_cout = []
    for formla in form_list:
        most_common_form = max(formulas[formla[0]].items(), key=operator.itemgetter(1))[0]
        common_form_score_cout.append((most_common_form, formla[1], sum(formulas[formla[0]].values())))
    return common_form_score_cout


def bind(app):
    # updates similar words
    @app.callback(
        Output('relevant_materials_container', 'children'),
        [Input('matsearch_button', 'n_clicks')],
        [State('matsearch_input', 'value')])
    def get_relevant_materials(_, search_text):
        if search_text is not None and search_text != "":
            sentence = phraser[dp.process_sentence(search_text.split())]
            most_similar = find_similar_materials(sentence, min_count=50)
            return serve_matlist(most_common_form(most_similar[:20]))
        else:
            return ""
