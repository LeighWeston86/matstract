import os
import json
from pymongo import MongoClient
from os import environ as env


def open_db_connection(user_creds=None, local=False, access="read_only"):
    if 'MATSTRACT_HOST' in env and local:
        uri = "mongodb://%s:%s/%s" % (
            env['MATSTRACT_HOST'], env['MATSTRACT_PORT'], env['MATSTRACT_DB'])
        db_creds = {'db': env['MATSTRACT_DB']}
    else:
        try:
            if user_creds is not None:
                db_creds_filename = user_creds
            else:
                db_creds_filename = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 'db_atlas.json')
            with open(db_creds_filename) as f:
                db_creds = json.load(f)
        except:
            if access == "read_only":
                db_creds = {"user": os.environ["ATLAS_USER"],
                            "pass": os.environ["ATLAS_USER_PASSWORD"],
                            "rest": os.environ["ATLAS_REST"],
                            "db": "tri_abstracts"}
            elif access == "annotator":
                db_creds = {"user": os.environ["ANNOTATOR_USER"],
                                     "pass": os.environ["ANNOTATOR_PASSWORD"],
                                     "rest": os.environ["ATLAS_REST"],
                                     "db": "tri_abstracts"}

        uri = "mongodb://{user}:{pass}@{rest}".format(**db_creds)

    mongo_client = MongoClient(uri, connect=False)
    db = mongo_client[db_creds["db"]]
    return db
