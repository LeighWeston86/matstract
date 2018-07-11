from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from bson import ObjectId
from collections import Iterable
from pymongo.command_cursor import CommandCursor

class MatstractSearch:
    """The class running all search queries"""

    VALID_FILTERS = ["material", "property", "application", "descriptor", "characterization", "synthesis", "phase"]
    FILTER_DICT = {
        "material": "MAT",
        "property": "PRO",
        "application": "APL",
        "descriptor": "DSC",
        "characterization": "CMT",
        "synthesis": "SMT",
        "phase": "SPL",
    }

    def __init__(self, local=False):
        self._ac = AtlasConnection(db="production", local=local)
        self._ec = ElasticConnection()
        self.filters = []

    def search(self, text=None, materials=None, max_results=1000, filters=None):
        print("searching for '{}' and {}".format(text, filters))
        pipeline = list()
        if filters:
            for f in filters:
                if f is not None:
                    search_filter = SearchFilter(filter_type=self.FILTER_DICT[f[0]], values=f[1].split(","))
                    for cond in search_filter.conditions:
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
        elif materials:  # if filters are supplied don't look at materials
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
        if len(pipeline) > 0:
            results = self._ac.db.ne_071018.aggregate(pipeline)
            ids = [str(entry["_id"]) for entry in results]
        else:
            ids = None
        if text and (ids is None or len(ids) > 0):
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


class SearchFilter(Filter):
    def __init__(self, filter_type, values):
        parser = parsing.SimpleParser()
        conditions = []
        if values is not None:
            include = set()
            exclude = set()
            for val in values:
                # if val[-1] == ",":
                #     val = val[0:-1]
                if val[0] == "-":
                    val = val[1::]
                    parsed = parser.parse(val) if filter_type == "MAT" else val
                    exclude.add(parsed if parsed else val)
                else:
                    parsed = parser.parse(val) if filter_type == "MAT" else val
                    include.add(parsed if parsed else val)
            if len(include) and len(exclude):
                conditions.append({
                    "$match": {
                        filter_type: {
                            "$or": {
                                {"$in": list(include)}, {"$nin": list(exclude)}
                            }
                        }
                    }})
            elif len(include):
                conditions.append({"$match": {filter_type: {"$in": list(include)}}})
            elif len(exclude):
                conditions.append({"$match": {filter_type: {"$nin": list(exclude)}}})
        super().__init__(conditions)

class DocumentFilter(Filter):

    def __init__(self, ids):
        conditions=[]
        if ids is not None:
            conditions.append({"$match": {"_id": {"$in": ids}}})
        super().__init__(conditions)
