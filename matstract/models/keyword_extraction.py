from matstract.web.search_app import get_search_results
import nltk
from nltk.corpus import stopwords


class OccurrenceExtractor(object):
    '''
    Key word extraction class based on n-gram frequencies.
    '''

    def __init__(self,
                 normalize=False,
                 stemming=False,
                 cutoff=6,
                 token_type='unigrams',
                 first_sentence_only=False,
                 first_last_sentence_only=False):
        self.name = ''
        self.normalize = normalize
        self.stemming = stemming
        self.cutoff = cutoff
        self.token_type = token_type
        self.first_sentence_only = first_sentence_only
        self.first_last_sentence_only = first_last_sentence_only

    def preprocessing(self, text):
        if self.first_sentence_only:
            sents = nltk.sent_tokenize(text)
            words = nltk.word_tokenize(sents[0])
        elif self.first_last_sentence_only:
            sents = nltk.sent_tokenize(text)
            words = nltk.word_tokenize(sents[0] + sents[-1])
        else:
            words = nltk.word_tokenize(text)
        words = [word for word in words if word not in stopwords.words('english') and len(word) >= self.cutoff]
        if self.normalize:
            words = [word.lower() for word in words]
        return words

    def bigrams(self, tokens):
        return list(nltk.bigrams(tokens))

    def trigrams(self, tokens):
        return list(nltk.trigrams(tokens))

    def most_common(self, collection, cutoff=10, min_counts=5):
        all_tokens = []
        for abstract in collection:
            tokens = self.preprocessing(abstract['abstract'])
            if self.token_type == 'unigrams':
                tokens = tokens
            elif self.token_type == 'bigrams':
                tokens = self.bigrams(tokens)
            elif self.token_type == 'trigrams':
                tokens = self.trigrams(tokens)
            # print(len(tokens), len(set(tokens)), tokens)
            all_tokens += set(tokens)
        most_common = nltk.FreqDist(all_tokens).most_common(cutoff)
        most_common = [ngram for (ngram, count) in most_common if count >= min_counts]
        return most_common


def cleanup_keywords(kw):
    unigrams, bigrams, trigrams = kw
    bigrams_flat = [word for grams in bigrams for word in grams]
    unigrams = [gram for gram in unigrams if gram not in bigrams_flat]
    trigrams_flat = [gram for gram_list in [list(nltk.bigrams(gram)) for gram in trigrams] for gram in gram_list]
    bigrams = [gram for gram in bigrams if gram not in trigrams_flat]
    return [' '.join(gram) if type(gram) != str else gram for gram in unigrams + bigrams + trigrams]

def extract_keywords(to_extract):
        kwds = []
        for tt in ['unigrams', 'bigrams', 'trigrams']:
            test = OccurrenceExtractor(normalize=True, first_last_sentence_only=True, token_type=tt)
            kwds.append(test.most_common(get_search_results(material=to_extract), cutoff=5))
        return cleanup_keywords(kwds)



if __name__ == '__main__':
    kwds = []
    for tt in ['unigrams', 'bigrams', 'trigrams']:
        test = OccurrenceExtractor(normalize=True, first_last_sentence_only=True, token_type=tt)
        kwds.append(test.most_common(get_search_results(material='GaN'), cutoff=5))
    print(cleanup_keywords(kwds))