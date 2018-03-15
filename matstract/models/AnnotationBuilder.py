from chemdataextractor.doc import Paragraph
from chemdataextractor import Document
from matstract.utils import open_db_connection, authenticate
import datetime


class AnnotationBuilder:
    _db = None
    ANNOTATION_COLLECTION = "annotations"
    MACRO_ANN_COLLECTION = "macro_ann"
    ABSTRACT_COLLECTION = "elsevier"
    GOOD_ABSTRACTS = ["10.1016/S0025-5408(98)00200-1",
                      "10.1016/j.ceramint.2017.03.121",
                      "10.1016/j.matlet.2010.05.014",
                      "10.1016/0022-3115(90)90252-I",
                      "10.1016/j.solidstatesciences.2016.05.006",
                      "10.1016/0025-5408(68)90091-3",
                      "10.1016/S0022-0248(00)00957-X",
                      "10.1016/j.solmat.2014.11.015",
                      "10.1016/j.apsusc.2011.01.102",
                      "10.1016/j.eurpolymj.2008.06.017",
                      "10.1016/S0042-207X(05)80149-6",
                      "10.1016/j.matchemphys.2015.07.015",
                      "10.1016/j.jallcom.2015.02.012",
                      "10.1016/j.optmat.2010.01.028",
                      "10.1016/0038-1098(77)90369-6",
                      "10.1016/S0925-9635(02)00322-9",
                      "10.1016/0039-6028(73)90403-2",
                      "10.1016/j.actamat.2017.11.018",
                      "10.1016/0167-2738(96)00123-3",
                      "10.1016/j.ceramint.2013.05.129"]

    LABELS = [
        {'text': 'Chemical mention', 'value': 'CHM'},
        {'text': 'Material of interest', 'value': 'MAT'},
        {'text': 'Property', 'value': 'PRO'},
        {'text': 'Property unit', 'value': 'PUT'},
        {'text': 'Property value', 'value': 'PVL'},
        {'text': 'Condition', 'value': 'CON'},
        {'text': 'Condition unit', 'value': 'CUT'},
        {'text': 'Condition value', 'value': 'CVL'},
        {'text': 'Descriptor', 'value': 'DSC'},
        {'text': 'Structure / Phase label', 'value': 'SPL'},
        {'text': 'Synthesis method', 'value': 'SMT'},
        {'text': 'Post processing method', 'value': 'PMT'},
        {'text': 'Characterization method', 'value': 'CMT'},
        {'text': 'Application / Device', 'value': 'APL'},
    ]

    def __init__(self):
        self._db = open_db_connection(access="annotator", local=True)

    def get_abstract(self, good_ones=False):
        if good_ones:
            return getattr(self._db, self.ABSTRACT_COLLECTION).aggregate([
                {"$match": {"doi": {"$in": self.GOOD_ABSTRACTS}}},
                {"$sample": {"size": 1}}
            ]).next()
        else:
            return getattr(self._db, self.ABSTRACT_COLLECTION).aggregate([{"$sample": {"size": 1}}]).next()

    def get_tokens(self, paragraph, user_key, cems=True):
        try:
            # find annotation by the same user for the same doi
            previous_annotation = self._db.annotations.find({'doi': paragraph['doi'], 'user': user_key}).next()
            tokens = previous_annotation["tokens"]
            existing_labels = previous_annotation["labels"]
        except Exception as e:
            # if no previous annotaiton was found
            ttl_tokens = AnnotationBuilder.tokenize(paragraph["title"], cems)
            abs_tokens = AnnotationBuilder.tokenize(paragraph["abstract"], cems)
            tokens = ttl_tokens + abs_tokens
            existing_labels = []
        return tokens, existing_labels


    @staticmethod
    def tokenize(text, cems=True):
        if cems:
            # getting initial annotation
            cde_cem_starts = [cem.start for cem in Document(text).cems]
        else:
            cde_cem_starts = []

        # getting all tokens
        all_tokens = Paragraph(text).tokens
        # building the array for annotation
        tokens = []
        for idx, sentence in enumerate(all_tokens):
            tokens.append([])
            for elem in sentence:
                tokens[idx].append({
                    "id": "token-" + str(elem.start) + "-" + str(elem.end),
                    "annotation": ('CHM' if elem.start in cde_cem_starts else None),
                    "text": elem.text,
                    "start": elem.start,
                    "end": elem.end
                })
        return tokens


    @staticmethod
    def prepare_annotation(doi, tokens, macro, labels, user_key):
        date = datetime.datetime.now().isoformat()
        annotation = {'doi': doi,
                      'tokens': tokens,
                      'tags': macro['tags'],
                      'user': user_key,
                      'date': date,
                      'labels': labels,
                      'authenticated': False}
        return annotation

    @staticmethod
    def prep_macro_ann(doi, relevance, flag, abs_type, user_key):
        """Macro Annotation (1. in the document)"""
        return {'doi': doi,
                'relevant': relevance,
                'flag': flag,
                'type': abs_type,
                'user': user_key,
                'date': datetime.datetime.now().isoformat(),
                'authenticated': False}

    def insert(self, annotation, collection):
        if authenticate(self._db, annotation["user"]):
            annotation["authenticated"] = True
            getattr(self._db, collection).replace_one({
                "doi": annotation["doi"], "user": annotation["user"]},
                annotation, upsert=True)
        else:
            print("Unauthorized annotation submitted!")
            getattr(self._db, collection).insert_one(annotation)

    def update_tags(self, tags):
        current_tags = self._db.abstract_tags.find({})
        for tag in tags:
            if tags not in current_tags:
                try:
                    self._db.abstract_tags.insert_one(self.prepare_tag(tag))
                except Exception as e:
                    print(e)

    def get_username(self, user_key):
        user = self._db.user_keys.find_one({"user_key": user_key})
        if user is not None:
            return user["name"]
        return None

    @staticmethod
    def prepare_tag(tag):
        return {"tag": tag}
