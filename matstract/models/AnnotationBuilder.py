from chemdataextractor.doc import Paragraph
from chemdataextractor import Document


class AnnotationBuilder:
    def get_tokens(self, paragraph):
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
            "annotation": token["start"] in cde_cem_starts}
            for token in tokens]

        return tokens, annotations
