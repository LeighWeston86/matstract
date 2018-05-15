import numpy as np
from matstract.nlp.data_preparation import DataPreparation
from gensim.models.phrases import Phraser, Phrases
from collections import defaultdict
import operator


class EmbeddingEngine:
    ABBR_LIST = ["C41H11O11", "PV", "OPV", "PV12", "CsOS", "CsKPSV", "CsPS", "CsHIOS", "OPV",
                 "CsPSV", "CsOPV", "CsIOS", "BCsIS", "CsPrS", "CEsH", "KP307", "AsOV", "CEsS",
                 "COsV", "CNoO", "BEsF", "I2P3", "KP115", "BCsIS", "C9705IS", "ISC0501", "B349S",
                 "CISe", "CISSe", "CsIPS", "CEsP", "BCsF", "CsFOS", "BCY10", "C12P", "EsHP", "CsHP",
                 "C2K8", "CsOP", "EsHS", "CsHS", "C3P", "C50I", "CEs"]

    def __init__(self):
        ds = np.DataSource()

        # loading pre-trained embeddings and the dictionary
        embeddings_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_abs_phrases_matnorm_keepformula_sg_w8_n10_a001_pc20.wv.vectors.npy"
        ds.open(embeddings_url)
        embeddings = np.load(ds.abspath(embeddings_url))
        with ds.open(
                "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_abs_phrases_matnorm_keepformula_sg_w8_n10_a001_pc20.tsv") as f:
            self.reverse_dictionary = [x.strip('\n') for x in f.readlines()]

        self.word2index = dict()
        for i, word in enumerate(self.reverse_dictionary):
            self.word2index[word] = i

        norm = np.sqrt(np.sum(np.square(embeddings), 1, keepdims=True))
        self.normalized_embeddings = embeddings / norm
        del embeddings, norm  # to free up some memory

        phrases = Phrases(threshold=0.0001, min_count=1)
        vocab = defaultdict(int)
        for word in self.reverse_dictionary:
            if "_" in word:
                vocab[str.encode(word)] = 100  # phrase
            else:
                vocab[str.encode(word)] = 1  # single word
        phrases.vocab = vocab
        self.phraser = Phraser(phrases)
        del vocab, phrases

        self._dp = DataPreparation()
        # loading pre-trained embeddings and the dictionary
        formulas_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/abstracts_matnorm_lower_punct_units_formula.pkl"
        ds.open(formulas_url)
        self.formulas = self._dp.load_obj(ds.abspath(formulas_url[:-4]))
        for abbr in self.ABBR_LIST:
            self.formulas.pop(abbr, None)

        self.formula_counts = [0] * len(self.formulas)
        for i, formula in enumerate(self.formulas):
            for writing in self.formulas[formula]:
                self.formula_counts[i] += self.formulas[formula][writing]
        del ds

    def close_words(self, word, top_k=8, exclude_self=True):
        """
        Returns a list of close words
        :param word: can be either a numeric vector or a string
        :param top_k: number of close words to return
        :param exclude_self: boolean, if the supplied word should be excluded or not
        :return:
        """
        close_words = []
        if isinstance(word, str):
            word_embedding = self.get_word_vector(word)
        else:
            word_embedding = word

        if word_embedding is not None:
            sim = np.dot([word_embedding], self.normalized_embeddings.T)
            nearest = (-sim[0, :]).argsort()[1:top_k + 1] if exclude_self else (-sim[0, :]).argsort()[:top_k]
            for k in range(top_k):
                close_words.append(self.reverse_dictionary[nearest[k]])
            return close_words
        else:
            return []

    def get_word_vector(self, word):
        """
        Gets the embedding for the given word
        :param word: a string word
        :return:
        """
        if word is not None and word != "":
            word = word.replace(" ", "_")
            word = self._dp.process_sentence([word])[0]
            # get all normalized word vectors
            try:
                return self.normalized_embeddings[self.reverse_dictionary.index(word), :]
            except Exception as ex:
                print(ex)
                return None
        else:
            return None

    def find_similar_materials(self, sentence, min_count=10):
        """
        Finds materials that match the best with the context of the sentence
        :param sentence: a list of words
        :param min_count: the minimum number of occurances for the formula to be considered
        :return:
        """
        similarities = dict()
        avg_embedding = np.zeros(200)
        for word in sentence:
            if word in self.word2index:
                avg_embedding += self.normalized_embeddings[self.word2index[word]]
        avg_embedding = avg_embedding / len(sentence)
        for i, formla in enumerate(self.formulas):
            if self.formula_counts[i] > min_count:
                similarities[formla] = np.dot(avg_embedding, self.normalized_embeddings[self.word2index[formla]])
        return sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    def most_common_form(self, form_dict):
        """
        Return the most common form of the formula given a dictionary with values as form: count dictionary
        :param form_dict: the dictionary
        :return:
        """
        common_form_score_cout = []
        for formula in form_dict:
            most_common_form = max(self.formulas[formula[0]].items(), key=operator.itemgetter(1))[0]
            common_form_score_cout.append((most_common_form, formula[1], sum(self.formulas[formula[0]].values())))
        return common_form_score_cout
