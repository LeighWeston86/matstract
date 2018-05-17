from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from bson import ObjectId
from collections import Iterable

class MatstractSearch:
    """The class running all search queries"""

    def __init__(self):
        self._ac = AtlasConnection(db="production")
        self._ec = ElasticConnection()
        self.filters = []

    def search(self, text='', materials=(), max_results=1000):
        print("searching for {} and {}".format(text, materials))
        pipeline = list()
        if materials:
            self.material_filter = MaterialFilter(materials)
            for cond in self.material_filter.conditions:
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
            pipeline.append({ "$limit": max_results})
        if text:
            ids = self._ec.query(text, max_results=max_results)
            self.document_filter = DocumentFilter(ids)
            if not materials or not len(materials):
                return self._ac.get_documents_by_id(ids)
            for cond in self.document_filter.conditions:
                pipeline.append(cond)
        return self._ac.db.mats_.aggregate(pipeline)

    def more_like_this(self, text='', materials=(), max_results=100):
        if text is None or text == '':
            return None

        query = {"query": {
            "more_like_this": {
                "fields": ['title', 'abstract'],
                "like": text
            }
        }}
        hits = self._ec.search(index="tri_abstracts", body=query, size=max_results, request_timeout=60)["hits"][
            "hits"]
        ids = [ObjectId(h["_id"]) for h in hits]
        return self._ac.get_documents_by_id(ids)


class Filter():
    """
    Parent class representing a filter to be applied to the database on search results. A search is a series of
    filters applied to the db to return only the desired results.
    """

    def __init__(self, conditions):
        self.conditions = conditions


class MaterialFilter(Filter):

    def __init__(self, materials):
        parser = parsing.SimpleParser()
        conditions = []
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
                    include.append(parsed if parsed else material)
            if len(include):
                conditions.append({"$match": {"unique_mats": {"$in": include}}})
            if len(exclude):
                conditions.append({"$match": {"unique_mats": {"$nin": exclude}}})
        super().__init__(conditions)


class DocumentFilter(Filter):

    def __init__(self, ids):
        conditions=[]
        if ids is not None:
            conditions.append({"$match": {"_id": {"$in": ids}}})
        super().__init__(conditions)
