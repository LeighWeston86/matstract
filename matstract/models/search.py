from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from bson import ObjectId
from collections import Iterable
from pymongo.command_cursor import CommandCursor

class MatstractSearch:
    """The class running all search queries"""

    VALID_FILTERS = ["material", "property", "application", "descriptor", "characterization", "synthesis", "phase"]

    def __init__(self, local=False):
        self._ac = AtlasConnection(db="production", local=local)
        self._ec = ElasticConnection()
        self.filters = []

    def search(self, text=None, materials=None, max_results=1000):
        print("searching for '{}' and {}".format(text, materials))
        pipeline = list()
        if materials:
            for material in materials:
                if material is not None:
                    material_filter = MaterialFilter(material.split(","))
                    for cond in material_filter.conditions:
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
            # pipeline.append({"$limit": max_results})
        if len(pipeline) > 0:
            results = self._ac.db.mats_.aggregate(pipeline)
            ids = [str(entry["_id"]) for entry in results]
        else:
            ids = []
        if text:
            ids = self._ec.query(text, ids=ids, max_results=max_results)
        return self._ac.get_documents_by_id(ids)


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
            include = set()
            exclude = set()
            for material in materials:
                if material[-1] == ",":
                    material = material[0:-1]
                if material[0] == "-":
                    material = material[1::]
                    parsed = parser.parse(material)
                    exclude.add(parsed if parsed else material)
                else:
                    parsed = parser.parse(material)
                    include.add(parsed if parsed else material)
            if len(include) and len(exclude):
                conditions.append({
                    "$match": {
                        "unique_mats": {
                            "$or": {
                                {"$in": list(include)}, {"$nin": list(exclude)}
                            }
                        }
                    }})
            elif len(include):
                conditions.append({"$match": {"unique_mats": {"$in": list(include)}}})
            elif len(exclude):
                conditions.append({"$match": {"unique_mats": {"$nin": list(exclude)}}})
        super().__init__(conditions)


class DocumentFilter(Filter):

    def __init__(self, ids):
        conditions=[]
        if ids is not None:
            conditions.append({"$match": {"_id": {"$in": ids}}})
        super().__init__(conditions)
