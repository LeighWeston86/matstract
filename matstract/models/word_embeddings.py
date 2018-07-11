import numpy as np
from matstract.nlp.data_preparation import DataPreparation
from gensim.models.phrases import Phraser, Phrases
from collections import defaultdict
import operator
import regex


class EmbeddingEngine:
    ABBR_LIST = ["C41H11O11", "PV", "OPV", "PV12", "CsOS", "CsKPSV", "CsPS", "CsHIOS", "OPV",
                 "CsPSV", "CsOPV", "CsIOS", "BCsIS", "CsPrS", "CEsH", "KP307", "AsOV", "CEsS",
                 "COsV", "CNoO", "BEsF", "I2P3", "KP115", "BCsIS", "C9705IS", "ISC0501", "B349S",
                 "CISe", "CISSe", "CsIPS", "CEsP", "BCsF", "CsFOS", "BCY10", "C12P", "EsHP", "CsHP",
                 "C2K8", "CsOP", "EsHS", "CsHS", "C3P", "C50I", "CEs", "CSm", "BF", "EsN", "BN50S", "AsCP",
                 "CPo", "LiPb17", "CsS", "EsIS", "AsCU", "CCsHS", "CsHPU", "AsOS", "AsCI", "EsF", "FV448",
                 "CNS", "CP5", "AsFP", "EsOP", "NS", "NS2", "EsI", "BH", "PPmV", "PSe", "AsN", "OPV5",
                 "NSiW"]

    def __init__(self):
        ds = np.DataSource()

        # loading pre-trained embeddings and the dictionary
        embeddings_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_abs_sg_w8_n10_a001_phrtsh20_pc20_pd3_exp.wv.vectors.npy"
        ds.open(embeddings_url)
        self.embeddings = np.load(ds.abspath(embeddings_url))

        out_embeddings_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_abs_sg_w8_n10_a001_phrtsh20_pc20_pd3_exp.trainables.syn1neg.npy"
        ds.open(out_embeddings_url)
        self.out_embeddings = np.load(ds.abspath(out_embeddings_url))
        dict_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/model_abs_sg_w8_n10_a001_phrtsh20_pc20_pd3_exp.tsv"
        with ds.open(dict_url, encoding='utf-8') as f:
            self.reverse_dictionary = [x.strip('\n') for x in f.readlines()]

        self.word2index = dict()
        for i, word in enumerate(self.reverse_dictionary):
            self.word2index[word] = i

        self.norm = np.sqrt(np.sum(np.square(self.embeddings), 1, keepdims=True))
        self.out_norm = np.sqrt(np.sum(np.square(self.out_embeddings), 1, keepdims=True))
        # self.normalized_embeddings = embeddings / self.norm
        # del embeddings  # to free up some memory

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

        self.dp = DataPreparation()
        # loading pre-trained embeddings and the dictionary
        formulas_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/abstracts_clean_valence_formula.pkl"
        ds.open(formulas_url)
        self.formulas = self.dp.load_obj(ds.abspath(formulas_url[:-4]))
        self.formulas_full = self.dp.load_obj(ds.abspath(formulas_url[:-4]))
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
        scores = []
        normalized_embeddings = self.embeddings / self.norm
        if isinstance(word, str):
            word_embedding = self.get_word_vector(word)
        else:
            word_embedding = word

        if word_embedding is not None:
            sim = np.dot([word_embedding], normalized_embeddings.T)
            nearest = (-sim[0, :]).argsort()[1:top_k + 1] if exclude_self else (-sim[0, :]).argsort()[:top_k]
            for k in range(top_k):
                close_words.append(self.reverse_dictionary[nearest[k]])
                scores.append(sim[0, nearest[k]])
            return close_words, scores
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
            word = self.dp.process_sentence([word])[0][0]
            # get all normalized word vectors
            try:
                return (self.embeddings / self.norm)[self.word2index[word], :]
            except Exception as ex:
                print(ex)
                return None
        else:
            return None

    def find_similar_materials(self, sentence, n_sentence=None, min_count=10, use_output_emb=False):
        """
        Finds materials that match the best with the context of the sentence
        :param sentence: a list of words
        :param min_count: the minimum number of occurances for the formula to be considered
        :return:
        """
        similarities = dict()
        avg_embedding = np.zeros(200)
        nr_words = 0
        normalized_embeddings = self.embeddings / self.norm
        embs = (self.out_embeddings / self.out_norm) if use_output_emb else normalized_embeddings  # the embeddings to use for similarity
        # positive contribution
        for word in sentence:
            if word in self.word2index:
                avg_embedding += normalized_embeddings[self.word2index[word]]
                nr_words += 1
        # negative contribution
        if n_sentence is not None:
            for n_word in n_sentence:
                if n_word in self.word2index:
                    avg_embedding -= normalized_embeddings[self.word2index[n_word]]
                    nr_words += 1
        avg_embedding = avg_embedding / nr_words
        for i, formla in enumerate(self.formulas):
            if self.formula_counts[i] > min_count:
                similarities[formla] = np.dot(avg_embedding, embs[self.word2index[formla]])
        return sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    def most_common_form(self, form_dict):
        """
        Return the most common form of the formula given a dictionary with values as form: count dictionary
        :param form_dict: the dictionary
        :return:
        """
        common_form_score_cout = []
        for formula in form_dict:
            if formula[0] in self.dp.ELEMENTS:
                most_common_form = formula[0]
            else:
                most_common_form = max(self.formulas[formula[0]].items(), key=operator.itemgetter(1))[0]
            common_form_score_cout.append((
                most_common_form,
                formula[1],
                sum(self.formulas[formula[0]].values()),
                self.norm[self.word2index[formula[0]]][0]))
        return common_form_score_cout

    def filter_by_elements(self, formula_list, plus_elems=None, minus_elems=None, max=50):
        if plus_elems is None:
            plus_elems = []
        if minus_elems is None:
            minus_elems = []
        pe = set(plus_elems) - set(minus_elems)
        minus_elems = set(minus_elems) - set(plus_elems)
        plus_elems = pe

        def has_plus(composition, plus_elems):
            if plus_elems is None or len(plus_elems) == 0:
                return True
            for elem in composition:
                if elem in plus_elems:
                    return True
            return False

        def has_minus(composition, minus_elems):
            if minus_elems is None or len(minus_elems) == 0:
                return False
            for elem in composition:
                if elem in minus_elems:
                    return True
            return False

        matched = 0
        matched_formula = []
        for form in formula_list:
            composition = self.dp.parser.parse_formula(form[0])
            if has_plus(composition, plus_elems) and not has_minus(composition, minus_elems):
                matched_formula.append(form)
                matched += 1
            if matched >= max:
                return matched_formula
        return matched_formula


def number_to_substring(text):
    return regex.sub("(\d*\.?\d+)", r'<sub>\1</sub>', text)