from matstract.utils import open_db_connection


class MatstractSearch:
    """The class running all search queries"""
    def __init__(self):
        self._db = open_db_connection(db="matstract_db")

    def get_abstracts_by_material(self, material, ids=None):
        pipeline = list()
        pipeline.append({"$match": {"unique_mats": material}})
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
                              "link": "$abstracts.link",
                              "chem_mentions": "$unique_mats"}})
        pipeline.append({"$project": {"abstracts": 0}})
        if ids is not None:
            pipeline.append({"$match": {"_id": {"$in": ids}}})
        return self._db.mats_.aggregate(pipeline)
