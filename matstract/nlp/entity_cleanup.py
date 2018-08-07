import nltk
from nltk.stem import PorterStemmer
import numpy as np
import pickle
from matstract.models.database import AtlasConnection
from sklearn.metrics.pairwise import cosine_similarity

def stems_equal(word_1, word_2):
    #Check for "ance" or "ivity" error
    if word_1[-5:] == 'ivity' and word_2[-4:] == 'ance':   #This doesn't seem to be working
        return False

    #Dont do stems if both end in "ance" or "ivity"
    stemmer = PorterStemmer()
    stem_1 = [stemmer.stem(token) for token in word_1.split()]
    stem_2 = [stemmer.stem(token) for token in word_2.split()]
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
    try:
        if word_1_split[-1] in redundant_list and word_1_split[:-1] == word_2_split:
            return True
        elif word_2_split[-1] in redundant_list and word_2_split[:-1] == word_1_split:
            return True
        elif word_1_split[-1] in redundant_list and word_2_split[-1]  and word_2_split[:-1] == word_1_split[-1]:
            return True
        else:
            return False
    except IndexError:
        return False

def is_acronym(word_1, word_2):
    '''
    Check to see if word_1 is an acronym of word_2
    '''

    if not word_1.isupper() and len(word_1) > 2:
            return False
    else:
        # 1st, just split on whitespace
        word_2_acronym = ''.join([token[0].upper() for token in word_2.split() ])
        if word_2_acronym == word_1:
            return True
        # Try splitting on both whitespace and hyphens
        word_2_no_hyphen = word_2.replace('-', ' ')
        word_2_acronym = ''.join([token[0].upper() for token in word_2_no_hyphen.split() ])
        if word_2_acronym == word_1:
            return True
        # Check for plural
        try:
            if     word_2[-1] == 's':
                _word_2 = word_2[:-1]
                # 1st, just split on whitespace
                word_2_acronym = ''.join([token[0].upper() for token in _word_2.split()])
                if word_2_acronym == word_1:
                    return True
                # Try splitting on both whitespace and hyphens
                word_2_no_hyphen = word_2.replace('-', ' ')
                word_2_acronym = ''.join([token[0].upper() for token in word_2_no_hyphen.split()])
                if word_2_acronym == word_1:
                    return True
        except IndexError:
            pass

def compare_without_hyphens(word_1, word_2):
    word_1_no_hyphen = word_1.replace('-', ' ')
    word_2_no_hyphen = word_2.replace('-', ' ')
    word_1_split = word_1_no_hyphen.split()
    word_2_split = word_2_no_hyphen.split()
    if word_1_split == word_2_split:

        return True
    else:
        return False

def sub_elements(): pass

def w2v_similarity(word_1, word_2, ev, w2i):
    try:
        cs  = cosine_similarity(ev[w2i[word_1]].reshape(1, -1), ev[w2i[word_2]].reshape(1, -1))
        return cs
    except KeyError:
        return 1



def clean_to_dict(list_to_clean, cutoff = 10):
    #Fd for the ents
    fd = nltk.FreqDist(list_to_clean)
    _set = [word for word, count in fd.items() if count > cutoff]
    print('{} entities to parse'.format(len(_set)))
    #Load w2v
    ev = np.load('normalized_embeddings.npy')
    w2i = pickle.load(open('word2index.p', 'rb'))
    entity_dict = {}
    for n, entity_1 in enumerate(_set):
        found_acronym = False
        equivalent_words = []
        for entity_2 in _set:
            #Get the w2v similarity
            w2v_sim = w2v_similarity(entity_1, entity_2, ev, w2i)
            #Compare the entities
            if entity_1 == entity_2:
                equivalent_words.append(entity_2)
                continue
            elif is_acronym(entity_1, entity_2) and w2v_sim > 0.7:
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

        if n % 1000 == 0:
            print(n)

    return entity_dict

def worker(docs, upper, lower):
    with open('{}.out'.format(upper), 'w+') as f:
        print('beginning...', file=f)
    nes = [ne for doc in docs for ne in doc[upper]]
    ne_dict = clean_to_dict(nes)
    return ne_dict

if __name__ == '__main__':
    db = AtlasConnection(db = 'test').db
    ne = db.ne_071918
    docs = list(ne.find(projection =  {'doi': 1, 'PRO' : 1, 'SMT': 1, 'CMT': 1, 'SPL': 1, 'APL': 1, 'DSC': 1} )[:1000])
    smt = [smt for doc in docs for smt in doc['SMT']]
    smt_dict = clean_to_dict(smt)
    print(smt_dict)
    pickle.dump(smt_dict, open('apl_dict.p', 'wb'))
