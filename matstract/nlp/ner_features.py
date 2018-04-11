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
from numbers import Number

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
        self.lookup_tables =  pickle.load(open(os.path.join(__location__, 'lookup_tables.p'), 'rb'))
        #load word2vec vectors
       # __location__ = os.path.realpath(
       #     os.path.join(os.getcwd(), os.path.dirname(__file__)))
       #self.w2v =  pickle.load(open(os.path.join(__location__, 'w2v_dict.p'), 'rb'))

    def get_feature(self, word_array, index,  NE_tagged = True):
        '''
        :param word_array: array/list of tuples representing a sentence
        :param index: element in word array to be indexed
        :return: required feature
        '''
        out_of_bounds = [['<out_of_bounds>']*2, '<out_of_bounds>'] if NE_tagged else ['<out_of_bounds>']*2
        if index >= 0:
            try:
                return word_array[index]
            except IndexError:
                return out_of_bounds
        else:
            return out_of_bounds

    def contextual_features(self, sent, idx, NE_tagged = True):
        '''
        Create context-based features for a token

        :param sent: a sentence; list of tokens with the format (word, pos), tag.
        :param idx: index for the token for which features are being generated
        :return: list of contextual features
        '''
        stemmer = nltk.PorterStemmer()
        #generate the features
        if NE_tagged:
            (current_word, current_pos), current_ne = self.get_feature(sent, idx)
            (previous_word, previous_pos), previous_ne = self.get_feature(sent, idx - 1)
            (previous_word2, previous_pos2), previous_ne2 = self.get_feature(sent, idx - 2)
            (next_word, next_pos), next_ne = self.get_feature(sent, idx + 1)
            (next_word2, next_pos2), next_ne2 = self.get_feature(sent, idx + 2)
        else:
            current_word, current_pos = self.get_feature(sent, idx, NE_tagged)
            previous_word, previous_pos = self.get_feature(sent, idx - 1, NE_tagged)
            previous_word2, previous_pos2 = self.get_feature(sent, idx - 2, NE_tagged)
            next_word, next_pos = self.get_feature(sent, idx + 1, NE_tagged)
            next_word2, next_pos2 = self.get_feature(sent, idx + 2, NE_tagged)
        # Add word/tag context
        features = [ stemmer.stem(previous_word2.lower()),
                     stemmer.stem(previous_word).lower(),
                     stemmer.stem(next_word.lower()),
                     stemmer.stem(next_word2.lower()),
                     previous_pos2,
                     previous_pos,
                     current_pos,
                     next_pos,
                     next_pos2]
        if NE_tagged:
            features.append(previous_ne)
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
        is_lower = 1 if word.islower() else 0
        is_upper = 1 if word.upper() else 0
        is_title = 1 if word.istitle() else 0
        is_digit = 1 if word.isdigit() else 0
        is_alnum = 1 if word.isalnum() else 0

        #check if word is a number
        try:
            float(word)
            is_number = 1
        except ValueError:
            is_number = 0

        #Check if word is a chemical formula
        parser = parsing.SimpleParser()
        is_formula = 1 if parser.matgen_parser(word) else 0

        #Check if punctuation due tokenization
        is_punct = 1 if word in string.punctuation else 0

        #Combine the features
        features = [
            word,
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

    #def w2v_features(self, word):
    #    try:
    #        return self.w2v[word]
    #    except KeyError:
    #        return np.ones(128) #this should be improved

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


    def fit_transform(self, tagged_documents, include_word2vec = False):
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
                    #add w2vec
                    #if include_word2vec:
                    #    w2v_vector = self.w2v_features(word)
                    #    if 'w2v_array' in locals():
                    #        w2v_array = np.vstack([w2v_array, w2v_vector])
                    #    else:
                    #        w2v_array = w2v_vector

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
        if include_word2vec:
            feature_array = hstack([cat_feature_array, sparse.csr_matrix(num_feature_array), w2v_array])
        else:
            feature_array = hstack([cat_feature_array, sparse.csr_matrix(num_feature_array)])
        self._features_outcomes = (feature_array, all_outcomes)

        return self._features_outcomes

    def transform(self, word_tag, sent, idx, prev_bio):
        '''
        Generate a feature array for
        :param word: string; word to be transformed
        :param sent: list of tuples; sentence containing word
        :param idx: int; index of word
        :return: feature vector representation of word
        '''
        word, tag = word_tag
        feature_vector = self.contextual_features(sent, idx,  NE_tagged = False)
        feature_vector += [prev_bio]
        feature_vector += self.syntactical_features(word)
        feature_vector += self.lookup_features(word)
        # Separate numerical and categorical features - numerical go to a scaler, categorical to hot encoder
        numerical   = [feature for feature in feature_vector if isinstance(feature, Number)]
        categorical = [feature for feature in feature_vector if not isinstance(feature, Number)]
        #encode categorical features
        for feature, encoder_set in zip(categorical, self.encoders):
            if 'hot_encoded_vector' in locals():
                hot_encoded_vector = hstack([hot_encoded_vector, self.encode_new(feature, encoder_set)])
            else:
                hot_encoded_vector = self.encode_new(feature, encoder_set)
        for feature, scaler in zip(numerical, self.scalers):
            if 'scaled_vector' in locals():
                scaled_vector = np.hstack([scaled_vector, self.scale_new(feature, scaler)])
            else:
                scaled_vector = self.scale_new(feature, scaler)

        combined_vector = hstack([hot_encoded_vector, sparse.csr_matrix(scaled_vector)])
        return combined_vector

    def encode_new(self, feature, encoders):
        '''
        Encode new features based opn previously fit encoders.
        :param feature: feature to be encoded
        :param encoders: fitted label encodres
        :return: onehot encoded feature vector
        '''
        label_encoder, onehot_encoder = encoders
        try:
        # integer encode
            integer_encoded = label_encoder.transform([feature])
        # binary encode
            onehot_encoded = onehot_encoder.transform(integer_encoded.reshape(-1, 1))
        except ValueError:
            return [0]*onehot_encoder.feature_indices_[1]

        return onehot_encoded[0]

    def scale_new(self, feature, scaler):
        '''
        Scaler numerical features based on already fitted scaler

        :param array/list containg numerical features:
        :return: scaled features using sklearn MinMaxScaler
        '''
        scaled = scaler.transform(feature)
        return scaled

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

if __name__ == '__main__':
    from matstract.models.AnnotationBuilder import AnnotationBuilder
    builder = AnnotationBuilder()
    annotations = builder.get_annotations(user='leighmi6')  #### Add user name
    annotations = [annotated.to_iob()[0] for annotated in annotations]
    annotations = [[[((word, pos), tag) for word, pos, tag in sent] for sent in doc] for doc in annotations]
    feature_generator = FeatureGenerator()
    features, outcomes = feature_generator.fit_transform(annotations)
    #Download new abstract
    #word = ('GaN', 'NN')
    #sent = [('We', 'DT'), ('grew', 'VB'), ('GaN', 'NN'), ('films', 'NNS')]
    #idx = 2
    #prev_bio = 'O'
    #print(feature_generator.transform(word, sent, idx, prev_bio))