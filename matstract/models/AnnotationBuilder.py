from chemdataextractor.doc import Paragraph
from chemdataextractor import Document
from matstract.utils import open_db_connection
from matstract.models.Annotation import TokenAnnotation
import itertools


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
                      "10.1016/j.ceramint.2013.05.129",
                      '10.1016/j.matchemphys.2010.01.014',
                      '10.1016/0039-6028(94)90834-6',
                      '10.1016/S0039-6028(99)01211-X',
                      '10.1016/j.tsf.2009.03.029',
                      '10.1016/j.eurpolymj.2007.09.019',
                      '10.1016/j.matdes.2015.12.079',
                      '10.1016/j.polymertesting.2008.02.001',
                      '10.1016/j.jmmm.2003.12.329',
                      '10.1016/S0304-8853(01)00168-8',
                      '10.1016/0921-5093(96)10212-4',
                      '10.1016/S0257-8972(01)01041-6',
                      '10.1016/S0257-8972(96)03068-X',
                      '10.1016/S0040-6090(98)01453-9',
                      '10.1016/0032-3861(96)81619-3',
                      '10.1016/0038-1098(74)91124-7',
                      '10.1016/j.compstruct.2012.09.052',
                      '10.1016/j.mee.2013.01.042',
                      '10.1016/S0257-8972(03)00612-1',
                      '10.1016/j.jallcom.2010.06.111',
                      '10.1016/j.jssc.2010.01.006',
                      '10.1016/j.matdes.2008.09.017']

    LABELS = [
        {'text': 'Chemical mention', 'value': 'CHM'},
        {'text': 'Material of interest', 'value': 'MAT'},
        {'text': 'Material reference', 'value': 'REF'},
        {'text': 'Material class', 'value': 'MTC'},
        {'text': 'Property', 'value': 'PRO'},
        {'text': 'Property unit', 'value': 'PUT'},
        {'text': 'Property value', 'value': 'PVL'},
        {'text': 'Property class', 'value': 'PRC'},
        {'text': 'Condition', 'value': 'CON'},
        {'text': 'Condition unit', 'value': 'CUT'},
        {'text': 'Condition value', 'value': 'CVL'},
        {'text': 'Descriptor / Modifier', 'value': 'DSC'},
        {'text': 'Structure / Phase label', 'value': 'SPL'},
        {'text': 'Synthesis method', 'value': 'SMT'},
        {'text': 'Post processing method', 'value': 'PMT'},
        {'text': 'Characterization method', 'value': 'CMT'},
        {'text': 'Application / Device', 'value': 'APL'},
    ]

    def __init__(self, local=False):
        self._db = open_db_connection(access="annotator", local=local)

    def get_abstract(self, doi=None, good_ones=False):
        if doi is not None:
            return getattr(self._db, self.ABSTRACT_COLLECTION).find_one({"doi": doi})
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
            previous_annotation = getattr(self._db, self.ANNOTATION_COLLECTION).find({'doi': paragraph['doi'], 'user': user_key}).next()
            tokens = previous_annotation["tokens"]
            existing_labels = previous_annotation["labels"]
        except Exception as e:
            # if no previous annotaiton was found
            ttl_tokens = AnnotationBuilder.tokenize(paragraph["title"], cems)
            abs_tokens = AnnotationBuilder.tokenize(paragraph["abstract"], cems)
            tokens = ttl_tokens + abs_tokens
            existing_labels = []
        return tokens, existing_labels

    def get_diff_tokens(self, doi=None, user=None):
        if user is None or self.get_username(user) is None:
            return None, "Not Authenticated."
        else:
            annotations = self.get_annotations(doi=doi)
            if len(annotations) == 0:
                return None, "No annotations with this doi."
            else:
                return self.combine_annotations(annotations)

    def combine_annotations(self, annotations):
        def merge_anns(anns, cl=None):
            mg = set()  # empty set
            for ann in anns:
                if type(ann) is not list:  # if either a string or None
                    ann = list([ann])
                mg = mg.union(set(ann))  # union
                if cl is not None:
                    mg = mg.intersection(cl)  # only consider common labels
            if len(mg) <= 1:
                return None  # no disagreement
            else:
                return list(mg)

        paragraph = self.get_abstract(doi=annotations[0].doi)
        combined_toks, _ = self.get_tokens(paragraph, None, cems=False)
        if len(annotations) > 0:
            for pair in itertools.combinations(annotations, r=2):
                common_labels = set(pair[0].labels).intersection(pair[1].labels).union({None})
                for rowIdx, tokenRow in enumerate(pair[1].tokens):
                    for idx, token in enumerate(tokenRow):
                        token_ann = pair[0].tokens[rowIdx][idx]["annotation"]
                        merged = merge_anns([token_ann, token["annotation"]], common_labels)
                        combined_toks[rowIdx][idx]["annotation"] = merge_anns([
                            merged,
                            combined_toks[rowIdx][idx]["annotation"]])
            return combined_toks, "Success"
        else:
            return None, "No annotations."

    def get_annotations(self, user=None, doi=None):
        constraints = dict()
        if user is not None:
            constraints["user"] = user
        if doi is not None:
            constraints["doi"] = doi
        annotations = getattr(self._db, self.ANNOTATION_COLLECTION).find(constraints)
        return [TokenAnnotation(annotation=annotation) for annotation in annotations]


    @staticmethod
    def tokenize(text, cems=True):
        if cems:
            # getting initial annotation
            cde_cem_starts = [cem.start for cem in Document(text).cems]
        else:
            cde_cem_starts = []

        # getting all tokens
        cde_p = Paragraph(text)
        all_tokens = cde_p.tokens
        pos_tokens = cde_p.pos_tagged_tokens  # part of speech tagger
        # building the array for annotation
        tokens = []
        for row_idx, sentence in enumerate(all_tokens):
            tokens.append([])
            for idx, elem in enumerate(sentence):
                tokens[row_idx].append({
                    "id": "token-" + str(elem.start) + "-" + str(elem.end),
                    "annotation": ('CHM' if elem.start in cde_cem_starts else None),
                    "pos": pos_tokens[row_idx][idx][1],
                    "text": elem.text,
                    "start": elem.start,
                    "end": elem.end
                })
        return tokens

    def insert(self, annotation, collection):
        auth = annotation.authenticate(self._db)
        if auth:
            getattr(self._db, collection).replace_one({
                "doi": annotation.doi, "user": annotation.user},
                annotation.__dict__, upsert=True)
        else:
            print("Unauthorized annotation submitted!")
            getattr(self._db, collection).insert_one(annotation.__dict__)

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

    def get_leaderboard(self, user_key):
        if self.get_username(user_key) is not None:
            macro_counts = getattr(self._db, self.MACRO_ANN_COLLECTION).aggregate([
                {"$group": {"_id": "$user", "abstracts": {"$sum": 1}}},
            ])
            macro_counts = getattr(self._db, "macro_ann").aggregate([
                {"$group": {"_id": "$user", "abstracts": {"$sum": 1}}},
            ])
            leaderboard = dict()
            for user in macro_counts:
                leaderboard[user["_id"]] = {"macro_abstracts": user["abstracts"]}

            token_counts = getattr(self._db, "annotations").aggregate([
                {"$group":
                     {"_id": "$user",
                      "abstracts": {"$sum": 1},
                      "token_labels": {"$sum": {"$size": "$labels"}}}},
            ])
            for user in token_counts:
                if user["_id"] in leaderboard:
                    leaderboard[user["_id"]]["labels"] = user["token_labels"]
                    leaderboard[user["_id"]]["token_abstracts"] = user["abstracts"]
                else:
                    leaderboard[user["_id"]] = {
                        "token_abstracts": user["abstracts"],
                        "token_labels": user["token_labels"]
                    }
            return leaderboard
        return None

    @staticmethod
    def prepare_tag(tag):
        return {"tag": tag}
