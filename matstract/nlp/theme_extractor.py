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
            "overall", "best overall property", "process", "numbers", "materials", "transitions", "applications",
            "law", "centers", "center", "eV", "shifts", "obtained", "spectra", "perform", "attribute",
            "endow", "special", "properties", "nm", "range", "detection", "nM", "I", "II", "III", "IV", "times",
            "samples", "respectively", "content", "conditions", "paper", "highlighted",
            "conditions highlighted", "required", "structure", "molecules", "interaction", "function", "planes",
            "condition", "resistance", "observed", "presented", "distribution", "could observed", "processes",
            "data", "system", "determined", "couples", "point determined", "temperature", "temperatures",
            "described", "K", "size obtained", "solvent", "solvents", "state", "entities", "measurements",
            "species", "complex", "size", "essential", "get essential", "liquid", "technique", "°C",
            "results presented", "recent results presented", "found", "achieved", "also investigated", "also presented",
            "case", "cells", "layer", "alloys", "alloy", "purposes", "systems", "demonstrated", "seconds",
            "picoseconds", "per picoseconds", "separation", "water", "formation", "effect",
            "tests", "characteristics", "signal", "frequency", "cm−2", "mW cm−2", "cycling", "atmosphere", "type",
            "worldwide", "engineering", "arena", "application", "engineering applications", "engineering arena",
            "structures", "literature", "examined", "available literature", "conductors", "(", ")", "formed", "states",
            "collapse", ", respectively", "sites", "μM", "propagation", "agents", "material", "pulses", "separations",
            "studies", "bulging", "methods", "research", "maps", "strategies", "hypothesis", "systematically",
            "discussed systematically", "also discussed systematically", "study", "]", "[", "mechanism", "solution",
            "solutions", "diameters", "agent", "future", "problems", "method", "term", "parameters", "accuracy", "mode",
            "models", "specimens", "theory", "environment", "qualities", "reported", "analysis", "outcomes",
            "different outcomes", "rate", "variation", "Å", "tens Å", "developed", "g−1", "model", "L−1", "l−1",
            "monitoring", "test", "boundaries", "values", "cm−3", "concentration", "coefficient",
            "advanced applications", "various advanced applications", "materials various advanced applications",
            "occurs", "also discussed", "design", "design summarized", "summarized", "component", "regime",
            "also studied", "investigated detail", "interest", ""
            ]

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


def analyze_themes(response):
    phrases = {}
    for l in [5, 4, 3, 2, 1]:
        for hit in response['hits']['hits']:
            score = hit['_score']
            if score > 30:
                for phrase in tokenize(hit['_source']['abstract'], l):
                    if "." == phrase.split()[-1]:
                        phrase = " ".join(phrase.split()[0:-1])
                    if phrase not in unuseful and not any([k in phrase for k in killers]) and not phrase.isdigit():
                        if phrase not in phrases:
                            phrases[phrase] = score * (l ** 3)
                        else:
                            phrases[phrase] += score * (l ** 3)
    if len(phrases) > 0:
        sorted_phrases = sorted(phrases.items(), key=itemgetter(1), reverse=True)
    else:
        sorted_phrases = []
    return sorted_phrases