from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from bson import ObjectId
import tqdm

import string
from operator import itemgetter
from gensim.utils import smart_open, simple_preprocess

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

STOPWORDS = set(stopwords.words('english'))
unuseful = ["discussed", "results", "various", "detail", "discussed detail","proposed", "proposed discussed",
            "studied", "field", "investigated", "time", "phase", "phases", "property", "overall property",
            "overall", "best overall property", "process", "numbers", "materials", "transitions"]
killers = ["research article", "article", "took place"]


def tokenize(text, N):
    results = []
    prepped_text = [w for w in word_tokenize(text) if not w.lower() in STOPWORDS]

    for token in prepped_text:
        if token.lower() in string.punctuation:
            prepped_text.remove(token)

    for i in range(len(prepped_text)):
        phrase = prepped_text[i:i + N]
        phrase = " ".join(phrase)
        if not len(phrase.strip()) == 1:
            results.append(phrase)
    return results


def analyze_themes(response, num_themes=25):
    phrases = {}
    for l in [5, 4, 3, 2, 1]:
        for hit in response['hits']['hits']:
            score = hit['_score']
            for phrase in tokenize(hit['_source']['abstract'], l):
                if "." == phrase.split()[-1]:
                    phrase = " ".join(phrase.split()[0:-1])
                if phrase not in unuseful and not any([k in phrase for k in killers]):
                    if phrase not in phrases:
                        phrases[phrase] = score * (l ** 3)
                    else:
                        phrases[phrase] += score * (l ** 3)

    if len(phrases) > 0:
        sorted_phrases = sorted(phrases.items(), key=itemgetter(1), reverse=True)
    else:
        sorted_phrases = []

    return sorted_phrases[0:num_themes]