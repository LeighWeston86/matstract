from chemdataextractor.doc import Paragraph
from chemdataextractor import Document
from matstract.utils import open_db_connection

class AnnotationBuilder:
    @staticmethod
    def get_tokens(paragraph):
        # getting all tokens
        all_tokens = Paragraph(paragraph).tokens
        raw_tokens = []
        for sentence in all_tokens:
            for elem in sentence:
                raw_tokens.append({"text": elem.text, "start": elem.start, "end": elem.end})

        # getting initial annotation
        cde_cem_starts = [cem.start for cem in Document(paragraph).cems]
        tokens = [{
            "id": "token-" + str(token["start"]) + "-" + str(token["end"]),
            "annotation": ('material' if token["start"] in cde_cem_starts else None),
            "text": token["text"],
            "start": token["start"],
            "end": token["end"]}
            for token in raw_tokens]

        return tokens

    @staticmethod
    def prepare_annotation(doi, tokens, macro):
        annotation = {'doi': doi,
                      'tokens': tokens,
                      'tags': macro['tags'],
                      'type': macro['type'],
                      'category': macro['category']}
        return annotation

    @staticmethod
    def insert_annotation(annotation):
        db = open_db_connection(local=True)
        db.annotations.insert_one(annotation)


