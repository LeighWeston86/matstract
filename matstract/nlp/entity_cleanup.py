from pymongo import MongoClient
import json
from matstract.extract.parsing import SimpleParser
import nltk
from nltk.stem import PorterStemmer
import numpy as np
import re
import pickle

def stems_equal(word_1, word_2): #Add some functionality that checks the stems of all words (split on whitespace or hyphens)
    #Just stem the final word
    stemmer = PorterStemmer()
    stem_1 = stemmer.stem(word_1)
    stem_2 = stemmer.stem(word_2)
    if stem_1 == stem_2:
        return True
    else:
        return False

def redundant_word(word_1, word_2):
    redundant_list = [
        'method',
        'technique',
        'analysis',
        'route']
    word_1_split = word_1.split()
    word_2_split = word_2.split()
    if word_1_split[-1] in redundant_list and word_1_split[:-1] == word_2_split:
        return True
    elif word_2_split[-1] in redundant_list and word_2_split[:-1] == word_1_split:
        return True
    elif word_1_split[-1] in redundant_list and word_2_split[-1]  and word_2_split[:-1] == word_1_split[-1]:
        return True
    else:
        return False


def is_acronym(word_1, word_2):
    '''
    Check to see if word_1 is an acronym of word_2
    '''

    if not word_1.isupper() and len(word_1) > 2:
        return False
    else:
        # 1st, just split on whitespace
        word_2_acronym = ''.join([token[0].upper() for token in word_2.split() ]) #re.split(r'[\s-]+', word_2)])
        if word_2_acronym == word_1:
            return True
        # Try splitting on both whitespace and hyphens
        word_2_no_hyphen = word_2.replace('-', ' ')
        word_2_acronym = ''.join([token[0].upper() for token in word_2_no_hyphen.split() ])
        if word_2_acronym == word_1:
            return True

def compare_without_hyphens(word_1, word_2):
    word_1_no_hyphen = word_1.replace('-', ' ')
    word_2_no_hyphen = word_2.replace('-', ' ')
    word_1_split = word_1_no_hyphen.split()
    word_2_split = word_2_no_hyphen.split()
    if word_1_split == word_2_split:

        return True
    else:
        return False

def w2v_similar(word_1, word_2): pass

def clean_up(list_to_clean):
    fd = nltk.FreqDist(list_to_clean)
    cleaned_list = []
    cache = {}
    for entity_1 in list_to_clean:

        if entity_1 in cache.keys():
            cleaned_list.append(cache[entity_1])
            continue
        found_acronym = False
        equivalent_words = []
        for entity_2 in list_to_clean:
            #Compare the entities
            if entity_1 == entity_2:
                equivalent_words.append(entity_2)
                continue
            elif is_acronym(entity_1, entity_2):
                equivalent_words.append(entity_2)
                found_acronym = True
                continue
            elif compare_without_hyphens(entity_1, entity_2):
                equivalent_words.append(entity_2)
                continue
            elif stems_equal(entity_1, entity_2):
                equivalent_words.append(entity_2)
                continue
            elif redundant_word(entity_1, entity_2):
                equivalent_words.append(entity_2)

        equivalent_words = list(set(equivalent_words))
        if found_acronym:
            equivalent_words = [word for word in equivalent_words if word != entity_1]

        new_word = equivalent_words[np.argmax([fd[word] for word in equivalent_words])]
        cache[entity_1] = new_word

        if new_word != entity_1:
            print(entity_1, new_word)
            pass
        cleaned_list.append(new_word)

    return cleaned_list

def clean_to_dict(list_to_clean):
    fd = nltk.FreqDist(list_to_clean)
    _set = [word for word, count in fd.most_common(5000)]
    #_set = list(set(list_to_clean))
    entity_dict = {}
    for entity_1 in _set:

        found_acronym = False
        equivalent_words = []
        for entity_2 in _set:
            #Compare the entities
            if entity_1 == entity_2:
                equivalent_words.append(entity_2)
                continue
            elif is_acronym(entity_1, entity_2):
                equivalent_words.append(entity_2)
                found_acronym = True
                continue
            elif compare_without_hyphens(entity_1, entity_2):
                equivalent_words.append(entity_2)
                continue
            elif stems_equal(entity_1, entity_2):
                equivalent_words.append(entity_2)
                continue
            elif redundant_word(entity_1, entity_2):
                equivalent_words.append(entity_2)

        equivalent_words = list(set(equivalent_words))
        if found_acronym:
            equivalent_words = [word for word in equivalent_words if word != entity_1]

        new_word = equivalent_words[np.argmax([fd[word] for word in equivalent_words])]
        entity_dict[entity_1] = new_word

        if new_word != entity_1:
            print(entity_1, new_word)
            pass

    return entity_dict

def open_db(database = 'tri_abstracts'):  #This is temporary until creds are fixed
    db_creds = {"db": "tri_abstracts",
    "user": "lweston",
    "pass": "8AbCb7pu-L",
    "rest": "matstract-shard-00-00-kve41.mongodb.net:27017,matstract-shard-00-01-kve41.mongodb.net:27017,matstract-shard-00-02-kve41.mongodb.net:27017/test?ssl=true&replicaSet=matstract-shard-0&authSource=admin"}
    db_creds['db'] = database
    uri = "mongodb://{user}:{pass}@{rest}".format(**db_creds)
    mongo_client = MongoClient(uri, connect=False)
    db = mongo_client[db_creds["db"]]
    return db

def get_entities(material):
    #Normalize the material
    parser = SimpleParser()
    material = parser.matgen_parser(material)

    #Open connection and get NEs associated with the material
    db = open_db() #AtlasConnection(db="test").db
    test_ne = db.test_ne
    dois = db.mats_.find({'unique_mats': material}).distinct('doi')
    entities = list(db.test_ne.find({'doi': {'$in': dois}}))
    num_entities = len(entities)

    #Extract the entities
    if entities is not None:
        apl, pro, spl, smt, cmt, dsc = [], [], [], [], [], []
        for doc in entities:
            # Get the properties
            pro.append(doc['PRO'])
            # Get the application
            apl.append(doc['APL'])
            # Get the phase label
            spl.append(doc['SPL'])
            # Get the synthesis method
            smt.append(doc['SMT'])
            # Get the characterization method
            cmt.append(doc['CMT'])
            # Get the characterization method
            dsc.append(doc['DSC'])

        pro = [p for pp in pro for p in pp if len(p) > 2]
        #pro = nltk.FreqDist(pro).most_common(20)
        apl = [p for pp in apl for p in pp if len(p) > 2]
        #apl = nltk.FreqDist(apl).most_common(10)
        spl = [p for pp in spl for p in pp if len(p) > 2]
        #spl = nltk.FreqDist(spl).most_common(3)
        smt = [p for pp in smt for p in pp if len(p) > 2]
        #smt = nltk.FreqDist(smt).most_common(10)
        cmt = [p for pp in cmt for p in pp if len(p) > 2]
        #cmt = nltk.FreqDist(cmt).most_common(10)
        dsc = [p for pp in dsc for p in pp if len(p) > 2]
        #dsc = nltk.FreqDist(dsc).most_common(10)

        entities_dict = {}
        entities_dict['PRO'] = pro
        entities_dict['SPL'] = spl
        entities_dict['SMT'] = smt
        entities_dict['CMT'] = cmt
        entities_dict['APL'] = smt
        entities_dict['DSC'] = cmt

        return entities_dict


if __name__ == '__main__':
    #material = 'ZnO'
    #entities = get_entities(material)
    #entities['SMT'] = clean_up(entities['SMT'])
    #print(nltk.FreqDist(entities['SMT']2).most_common(20))
    db = open_db()
    ne = db.ne_071018
    docs = list(ne.find(projection =  {'doi': 1, 'PRO' : 1, 'SMT': 1, 'CMT': 1, 'SPL': 1, 'APL': 1, 'DSC': 1} ))
    smt = [smt for doc in docs for smt in doc['APL']]
    smt_dict = clean_to_dict(smt)
    print(smt_dict)
    pickle.dump(smt_dict, open('apl_dict.p', 'wb'))
