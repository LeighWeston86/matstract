from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from abc import ABCMeta, abstractmethod

class MatstractSearch:
    """The class running all search queries"""

    def __init__(self):
        self._db = AtlasConnection(db="production").db

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

class Filter(ABCMeta):
    """
    Abstract class representing a filter to be applied to the database on search results. A search is a series of
    filters applied to the db to return only the desired results.
    """
    def __init__(self, criteria):
        self.criteria = criteria
        super().__init__()

    @abstractmethod
    def apply(self):
        pass





class MaterialFilter(Filter):

    def __init__(self, materials):
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

class TextFilter:
    def __init__(self, text):
        if text is not None:

            include = list()
            exclude = list()

                conditions.append({"$match": {"unique_mats": {"$in": include}}})
            if len(exclude):
                conditions.append({"$match": {"unique_mats": {"$nin": exclude}}})
            return conditions
        return []
