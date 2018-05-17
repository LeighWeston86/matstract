from matstract.utils import open_db_connection
from matstract.extract import parsing


class MatstractSearch:
    """The class running all search queries"""

    def __init__(self):
        self._db = open_db_connection(db="matstract_db", local=False)

    def get_abstracts_by_material(self, materials, ids=None):
        pipeline = list()
        for cond in self.construct_material_filer(materials):
            pipeline.append(cond)
        pipeline.append({"$lookup": {
            "from": "abstracts",
            "localField": "doi",
            "foreignField": "doi",
            "as": "abstracts"}})
        pipeline.append({"$match": {"abstracts": {"$ne": []}}})
        pipeline.append({"$unwind": "$abstracts"})
        pipeline.append({"$project": {
            "_id": "$abstracts._id",
            "doi": 1,
            "abstract": "$abstracts.abstract",
            "year": "$abstracts.year",
            "authors": "$abstracts.authors",
            "title": "$abstracts.title",
            "journal": "$abstracts.journal",
            "link": "$abstracts.link",
            "chem_mentions": "$unique_mats"}})
        pipeline.append({"$project": {"abstracts": 0}})
        if ids is not None:
            pipeline.append({"$match": {"_id": {"$in": ids}}})
        return self._db.mats_.aggregate(pipeline)

    def construct_material_filer(self, materials):
        parser = parsing.SimpleParser()
        if materials is not None:
            materials = materials.split()
            include = list()
            exclude = list()
            for material in materials:
                if material[-1] == ",":
                    material = material[0:-1]

                if material[0] == "-":
                    material = material[1::]
                    parsed = parser.parse(material)
                    exclude.append(parsed if parsed else material)
                else:
                    parsed = parser.parse(material)
                    print(parsed)
                    include.append(parsed if parsed else material)
            conditions = []
            if len(include):
                conditions.append({"$match": {"unique_mats": {"$in": include}}})
            if len(exclude):
                conditions.append({"$match": {"unique_mats": {"$nin": exclude}}})
            return conditions
        return []
