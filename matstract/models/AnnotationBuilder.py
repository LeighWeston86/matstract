from chemdataextractor.doc import Paragraph
from chemdataextractor import Document


class AnnotationBuilder:
    @staticmethod
    def get_tokens(paragraph):
        # getting all tokens
        all_tokens = Paragraph(paragraph).tokens
        tokens = []
        for sentence in all_tokens:
            for elem in sentence:
                tokens.append({"text": elem.text, "start": elem.start, "end": elem.end})

        # getting initial annotation
        cde_cem_starts = [cem.start for cem in Document(paragraph).cems]
        annotations = [{
            "id": "token-" + str(token["start"]) + "-" + str(token["end"]),
            "annotation": ('material' if token["start"] in cde_cem_starts else None)}
            for token in tokens]

        return tokens, annotations

    @staticmethod
    def prepare_annotation(doi, tokens, macro):
        annotation = {'doi': doi,
                      'tokens': tokens,
                      'tags': macro['tags'],
                      'type': macro['type'],
                      'category': macro['category']}
        return annotation

