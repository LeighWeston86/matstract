from chemdataextractor.doc import Paragraph
from chemdataextractor import Document
from matstract.utils import open_db_connection, authenticate
import datetime


class AnnotationBuilder:
    _db = None
    ANNOTATION_COLLECTION = "annotations"
    MACRO_ANN_COLLECTION = "macro_ann"
    LABELS = [
        {'text': 'Material', 'value': 'material'},
        {'text': 'Synthesis method', 'value': 'synthesis_method'},
        {'text': 'Characterization method', 'value': 'characterization_method'},
        {'text': 'Application', 'value': 'application'},
        {'text': 'Property', 'value': 'property'},
        {'text': 'Property unit', 'value': 'property_unit'},
        {'text': 'Property value', 'value': 'property_value'},
    ]

    def __init__(self):
        self._db = open_db_connection(access="annotator", local=True)

    @staticmethod
    def get_tokens(paragraph, pre_annotate=False):
        if pre_annotate:
            # getting initial annotation
            cde_cem_starts = [cem.start for cem in Document(paragraph).cems]
        else:
            cde_cem_starts = []

        # getting all tokens
        all_tokens = Paragraph(paragraph).tokens
        # building the array for annotation
        tokens = []
        for idx, sentence in enumerate(all_tokens):
            tokens.append([])
            for elem in sentence:
                tokens[idx].append({
                    "id": "token-" + str(elem.start) + "-" + str(elem.end),
                    "annotation": ('material' if elem.start in cde_cem_starts else None),
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
    def prep_macro_ann(doi, relevance, abs_type, user_key):
        """Macro Annotation (1. in the document)"""
        return {'doi': doi,
                'relevant': relevance,
                'type': abs_type,
                'user': user_key,
                'date': datetime.datetime.now().isoformat(),
                'authenticated': False}

    def insert(self, annotation, collection):
        if authenticate(self._db, annotation["user"]):
            annotation["authenticated"] = True
            getattr(self._db, collection).insert_one(annotation)
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
