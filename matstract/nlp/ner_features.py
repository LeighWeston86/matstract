import nltk
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, MinMaxScaler
from numpy import array
import pandas as pd
from scipy.sparse import hstack
import string
from matstract.extract import parsing
import numpy as np
from scipy import sparse
import pickle
import os

class FeatureGenerator:
    '''
    Class for generating features for named entity recognition (ner) in materials science text.

    Example usage:
    >>>feature_generator = FeatureGenerator()
    >>>features, outcomes = feature_generator.fit_transform(annotations)

    Where annotations is a list of documents.
    Each document is a list of sentences.
    Sentences are a list where each token is a nested tuple with format ((word, pos), tag)
    word: string containg the word
    pos: part-of-speach tag for the word
    tag: ner tag for the word
    '''
    def __init__(self, train_test_split = 0.5):
        '''
        :param train_test_split: cutoff for splitting of the train/test set
        '''
        self.encoders = []
        self.scalers = []
        self._features_outcomes = None
        self.train_test_split = train_test_split
        #load in lookup tables
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        open(os.path.join(__location__, 'lookup_tables.p'), 'rb')
        self.lookup_tables =  pickle.load(open(os.path.join(__location__, 'lookup_tables.p'), 'rb'))

    def get_feature(self, word_array, index):
        '''
        :param word_array: array/list of tuples representing a sentence
        :param index: element in word array to be indexed
        :return: required feature
        '''
        out_of_bounds = [['out_of_bounds'] * 2, 'out_of_bounds']
        if index >= 0:
            try:
                return word_array[index]
            except IndexError:
                return out_of_bounds
        else:
            return out_of_bounds

    def contextual_features(self, sent, idx):
        '''
        Create context-based features for a token

        :param sent: a sentence; list of tokens with the format (word, pos), tag.
        :param idx: index for the token for which features are being generated
        :return: list of contextual features
        '''
        stemmer = nltk.PorterStemmer()
        #generate the features
        (current_word, current_pos), current_ne = self.get_feature(sent, idx)
        (previous_word, previous_pos), previous_ne = self.get_feature(sent, idx - 1)
        (previous_word2, previous_pos2), previous_ne2 = self.get_feature(sent, idx - 2)
        (next_word, next_pos), next_ne = self.get_feature(sent, idx + 1)
        (next_word2, next_pos2), next_ne2 = self.get_feature(sent, idx + 2)
        # Add word/tag context
        features = [ stemmer.stem(previous_word2.lower()),
                     stemmer.stem(previous_word).lower(),
                     current_word.lower(),
                     stemmer.stem(next_word.lower()),
                     stemmer.stem(next_word2.lower()),
                     previous_pos2,
                     previous_pos,
                     current_pos,
                     next_pos,
                     next_pos2,
                     previous_ne]
        return features

    def syntactical_features(self, word):
        '''
        Create syntax-based features for a token

        :param word: string containg the word for which syntactical features are generated
        :return: list of syntactical features
        '''
        #All syntax features
        pre1 = word[:1]
        pre2 = word[:2]
        pre3 = word[:3]
        suf1 = word[-1:]
        suf2 = word[-2:]
        suf3 = word[-2:]
        length = len(word)
        is_lower = word.islower()
        is_upper = word.upper()
        is_title = word.istitle()
        is_digit = word.isdigit()
        is_alnum = word.isalnum()

        #check if word is a number
        try:
            float(word)
            is_number = 1
        except ValueError:
            is_number = 0

        #Check if word is a chemical formula
        parser = parsing.SimpleParser()
        is_formula = 1 if parser.matgen_parser(word) else 0

        #Check if punctuation due  tokenization
        is_punct = 1 if word in string.punctuation else 0

        #Combine the features
        features = [
            pre1,
            pre2,
            pre3,
            suf1,
            suf2,
            suf3,
            length,
            is_lower,
            is_upper,
            is_title,
            is_digit,
            is_alnum,
            is_formula,
            is_punct
        ]
        return features

    def lookup_features(self, word):
        '''
        Checks if a word is in a look up table

        :param word: string containg the word to be looked up
        :return: list indicating whether word was in look up table
        '''
        #look up in chem tables
        in_chem = 1 if word.lower() in self.lookup_tables['chem_lookup'] else 0
        in_chem_stem = 1 if word.lower() in self.lookup_tables['chem_stem_lookup'] else 0
        #lookup space group tables
        in_spacegroup = 1 if word.lower() in self.lookup_tables['spacegroup_lookup'] else 0
        return [in_chem, in_chem_stem, in_spacegroup ]


    def hot_encoder(self, data_vec):
        '''
        Binary encoder for categorical features

        :param array/list containg categoricla features:
        :return: sklean OneHotEncoder vector
        '''
        values = array(data_vec)
        # integer encode
        label_encoder = LabelEncoder()
        integer_encoded = label_encoder.fit_transform(values)
        # binary encode
        onehot_encoder = OneHotEncoder(sparse=True)
        integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
        onehot_encoded = onehot_encoder.fit_transform(integer_encoded)
        self.encoders.append( (label_encoder, onehot_encoder) )
        return onehot_encoded

    def scaler(self, data_vec):
        '''
        Scaler for numerical features

        :param array/list containg numerical features:
        :return: scaled features using sklearn MinMaxScaler
        '''
        values = array(data_vec)
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(values.reshape(-1, 1))
        self.scalers.append(scaler)
        return scaled


    def fit_transform(self, tagged_documents):
        '''
        Generate an array of features representing the tagged documents

        :param tagged_documents: pos and NE tagged documents as a list.
        :return: returns a tuple (features, outcomes). Feature array as is a scipy sparse array.
        '''
        all_features = []
        all_outcomes = []
        for doc in tagged_documents:
            for sent in doc:
                for n, ((word, pos), NE_tag) in enumerate(sent):
                    feature_vector  = self.contextual_features(sent, n)
                    feature_vector += self.syntactical_features(word)
                    feature_vector += self.lookup_features(word)
                    all_features.append(feature_vector)
                    all_outcomes.append(NE_tag)
        df = pd.DataFrame(all_features)
        #Separate numerical and categorical features - numerical go to a scaler, categorical to hot encoder
        categorical = df[[col for col in df.columns if not np.issubdtype(df[col].dtype, np.number)]]
        numeric = df[[col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]]
        #Onehot encode categorical features
        cat_array_exists = False
        for col in categorical.columns:
            data_vec = self.hot_encoder(categorical[col])
            if not cat_array_exists:
                cat_feature_array = data_vec
                cat_array_exists = True
            else:
                cat_feature_array = hstack([cat_feature_array, data_vec])
        #Scale numerical features
        num_array_exists = False
        for col in numeric.columns:
            data_vec = self.scaler(numeric[col])
            if not num_array_exists:
                num_feature_array = data_vec
                num_array_exists = True
            else:
                num_feature_array = np.hstack([num_feature_array, data_vec])

        feature_array = hstack([cat_feature_array, sparse.csr_matrix(num_feature_array)])
        self._features_outcomes = (feature_array, all_outcomes)

        return self._features_outcomes

    @property
    def features_outcomes(self):
        return self._features_outcomes

    @property
    def train_test_set(self):
        features, outcomes = self._features_outcomes
        cutoff = int(self.train_test_split*len(outcomes))
        X_train = features.tocsr()[:cutoff]
        X_test = features.tocsr()[cutoff:]
        y_train = outcomes[:cutoff]
        y_test = outcomes[cutoff:]
        return (X_train, y_train), (X_test, y_test)