import datetime
import nltk
from nltk.chunk.util import ChunkScore


class Annotation:
    def __init__(self, doi, user=None):
        self.doi = doi
        self.user = user
        self.date = datetime.datetime.now().isoformat()
        self.authenticated = False

    def authenticate(self, db):
        """Authenticate the user"""
        if self.user is not None and db.user_keys.find({"user_key": self.user}).count() > 0:
            self.authenticated = True
        return self.authenticated


class MacroAnnotation(Annotation):
    """
    Used to annotate
    relevant:   true or false
    type:       experiment, theory or both
    flag:       strange, incomplete abstracts
    """
    def __init__(self, doi, relevant, flag, abs_type, user=None):
        Annotation.__init__(self, doi, user)
        self.relevant = relevant
        self.flag = flag
        self.abs_type = abs_type


class TokenAnnotation(Annotation):
    """
    Used to annotate each token of the abstract for named entity recognition
    and information retrieval
    tokens: every word in the text is considered a token. It is a dictionary with
            an annotation label, start/end and content (the actual token text)
    labels: a list of token labels that was used for that annotation
    tags:   a list of tags for the whole abstract, if one wants to add any extra info
    """
    def __init__(self, doi=None, tokens=None, labels=None, tags=None, user=None, annotation=None):
        if annotation is not None:
            self.from_dict(annotation)
        else:
            Annotation.__init__(self, doi, user)
            self.tokens = tokens
            self.labels = labels
            self.tags = tags

    def from_dict(self, dictionary):
        """Builds a TokenAnnotation object from a dictionary"""
        Annotation.__init__(self, dictionary["doi"], dictionary["user"])
        self.tokens = dictionary["tokens"]
        self.labels = dictionary["labels"]
        self.tags = dictionary["tags"]

    def to_iob(self):
        """
        Converts the annotation object to CoNNL IOB annotation text string, with
        each row corresponding to a single token.
        :return: the string in CoNNL IOB annotation format
        """
        iob = []
        iob_str = []
        for row_idx, tokenRow in enumerate(self.tokens):
            iob.append([])
            for idx, token in enumerate(tokenRow):
                if token["annotation"] is None:
                    label = "O"
                elif idx == 0 or tokenRow[idx - 1]["annotation"] != token["annotation"]:
                    label = "B-" + token["annotation"]
                else:
                    label = "I-" + token["annotation"]
                iob[row_idx].append((token["text"], token["pos"], label))
                iob_str.append(token["text"] + " " + token["pos"] + " " + label + "\n")
            iob_str.append("\n")
        return iob, "".join(iob_str)

    def to_agr_list(self):
        """
        Returns a list of tuples to be used with nltk.metrics.agreement
        :return: list of tuples ("annotator", "tokenId", "label")
        """
        counter = 0
        aggr_list = []
        for tokenRow in self.tokens:
            for token in tokenRow:
                aggr_tuple = (self.user, counter, token["annotation"])
                aggr_list.append(aggr_tuple)
                counter += 1
        return aggr_list

    def to_ann_list(self):
        """
        An ordered list of annotation labels, that can be used for building a confusion matrix
        :return:
        """
        ann_list = []
        for tokenRow in self.tokens:
            for token in tokenRow:
                ann_list.append(str(token["annotation"]))
        return ann_list

    def compare(self, ann2, labels=None):
        """
        Estimates the accuracy of annotation/prediction assuming the current
        Annotation is the gold standard
        :return: NLTK ChinkScore Object
        """
        if labels is None:
            labels = tuple(value for value in self.labels if value in ann2.labels)
        self_nltk = nltk.chunk.conllstr2tree(self.to_iob()[1], chunk_types=labels)
        ann2_nltk = nltk.chunk.conllstr2tree(ann2.to_iob()[1], chunk_types=labels)

        chunk_score = ChunkScore()
        chunk_score.score(self_nltk, ann2_nltk)

        return chunk_score
