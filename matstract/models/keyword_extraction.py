from matstract.web.search_app import get_search_results
from sklearn.feature_extraction.text import CountVectorizer
from operator import itemgetter
import numpy as np
import nltk
from nltk.corpus import stopwords
from matstract.utils import open_db_connection

class TermFrequency(object):
    '''
    Key word extraction class.
    Supports keyword extraction based on term frequencey.
    Input is a list of documents; documents are a single string.
    '''

    def __init__(self,
                 normalize=False,
                 cutoff=6,
                 min_counts=5,
                 token_type='unigrams',
                 first_last_sentence_only=False):
        self.normalize = normalize
        self.min_counts = min_counts
        self.cutoff = cutoff
        self.token_type = token_type
        self.first_last_sentence_only = first_last_sentence_only
        self.tf = None

    def preprocessing(self, text):
        if self.first_last_sentence_only:
            sents = nltk.sent_tokenize(text)
            words = nltk.word_tokenize(sents[0] + sents[-1])
        else:
            words = nltk.word_tokenize(text)
        words = [word for word in words if word not in stopwords.words('english')]
        if self.normalize:
            words = [word.lower() for word in words]
        if self.token_type == 'unigrams':
            words = [word for word in words if len(word) >= self.cutoff]
            return words
        elif self.token_type == 'bigrams':
            return list(nltk.bigrams(words))
        elif self.token_type == 'trigrams':
            return list(nltk.trigrams(words))

    def process(self, collection):
        processed = [self.preprocessing(document) for document in collection]
        return processed

    def fit_tf(self, collection, cutoff=5, min_counts=5):
        processed = self.process(collection)
        tokens = []
        for text in processed:
            tokens += text
        self.tf = nltk.FreqDist(tokens)

    @property
    def term_frequencies(self):
        return self.tf

    @property
    def sorted_frequencies(self):
        as_list = [(keys, values) for keys, values in zip(self.tf.keys(), self.tf.values())]
        return sorted(as_list, key=itemgetter(1), reverse=True)

    @property
    def most_frequent(self):
        return [ngram for (ngram, count) in self.tf.most_common(self.cutoff) if count >= self.min_counts]


class DocumentFrequency(CountVectorizer):
    '''
    A wrapper class for sklearn.feature_extraction.text.CountVectorizer.
    '''

    def __init__(self,
                 n_grams=1,
                 first_last_sentence_only=False):
        CountVectorizer.__init__(self, ngram_range=(n_grams, n_grams))
        self.first_last_sentence_only = first_last_sentence_only
        self.term_dict = {}

    def process(self, text):
        if self.first_last_sentence_only:
            sents = nltk.sent_tokenize(text)
            text = sents[0] + sents[-1]
        return text

    def fit_df(self, collection):
        processed = [self.process(document) for document in collection]
        bag_of_words = self.fit(processed)
        sparse_matrix = bag_of_words.transform(processed)
        to_binary = np.where(sparse_matrix.toarray() > 0, 1, 0)
        word_sum = np.sum(to_binary, axis=0)
        self.term_dict = {word: freq for (word, freq) in zip(bag_of_words.get_feature_names(), word_sum)}

    @property
    def document_frequency(self):
        return self.term_dict

    @property
    def inverse_document_frequency(self):
        keys = self.term_dict.keys()
        return {key: (1 / self.term_dict[key]) for key in keys}

    @property
    def sorted_document_frequency(self):
        return sorted([(key, self.term_dict[key]) for key in self.term_dict.keys()], key=itemgetter(1), reverse=True)


def idf_mongo(db_l, word, cutoff=3):
    if type(word) == str:
        document_frequency = db_l.abstracts.find({'$text': {'$search': "\"{}\"".format(word)}}).count()
    else:
        document_frequency = db_l.abstracts.find({'$text': {'$search': "\"{}\"".format(' '.join(word))}}).count()
    if document_frequency > cutoff:
        idf = 1 / document_frequency
    else:
        idf = 0
    return idf


def cleanup_keywords(kw):
    unigrams, bigrams, trigrams = kw
    bigrams_flat = [word for grams in bigrams for word in grams]
    unigrams = [gram for gram in unigrams if gram not in bigrams_flat]
    trigrams_flat = [gram for gram_list in [list(nltk.bigrams(gram)) for gram in trigrams] for gram in gram_list]
    bigrams = [gram for gram in bigrams if gram not in trigrams_flat]
    return [' '.join(gram) if type(gram) != str else gram for gram in unigrams + bigrams + trigrams]


def extract_tf(list_of_abstracts, count=5):
    kwds_tf = {}
    for tt in ['unigrams', 'bigrams', 'trigrams']:
        tf = TermFrequency(normalize=True, first_last_sentence_only=True, token_type=tt)
        tf.fit_tf(list_of_abstracts)
        kwds_tf[tt] = tf.sorted_frequencies[:count]
    return kwds_tf


def extract_tfidf(list_of_abstracts, db_l, count=5):
    kwds_tfidf = {}
    for tt in ['unigrams', 'bigrams', 'trigrams']:
        tf = TermFrequency(normalize=True, first_last_sentence_only=True, token_type=tt)
        tf.fit_tf(list_of_abstracts)
        most_common = tf.sorted_frequencies[:20]
        idf_scores = [(word, idf_mongo(db_l, word) * score) for (word, score) in most_common]
        top_idf = sorted(idf_scores, key=itemgetter(1), reverse=True)[:count]
        kwds_tfidf[tt] = top_idf
    return kwds_tfidf


if __name__ == '__main__':
    db = open_db_connection()
    material = 'GaN'
    result = get_search_results(material=material)
    abstracts = [doc['abstract'] for doc in result]
    # Extract term frequencies
    term_frequencies = extract_tf(abstracts, count=5)
    # Extract tfidf
    tfidf = extract_tfidf(abstracts, db, count=5)
    for n_grams in ['unigrams', 'bigrams', 'trigrams']:
        print('####', n_grams, '####', sep='\n')
        for tf, tf_idf in zip(term_frequencies[n_grams], tfidf[n_grams]):
            print(tf, tf_idf)