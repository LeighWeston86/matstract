import os
from os import environ as env
import json
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import certifi

#Change this variable to True for easy offline testing.
local = True

class AtlasConnection(MongoClient):
    """ Class representing a connection to the Atlas cluster (MongoDB)"""

    def __init__(self, local=local, access="read_only", db="production"):
        """
        Args:
            local (bool): True to use local config file, False for environment variables. Default: False
            access (str): Level of access. e.g. "admin", "read_only", or "annotator"
            db (str): Desired database. e.g. "testing" or "production"

        Returns: pymongo Client.

        """

        if not local:
            env_vars = ["ATLAS_USER", "ATLAS_USER_PASSWORD", "ANNOTATOR_USER", "ANNOTATOR_PASSWORD", "ATLAS_REST"]
            if not all([ev in env for ev in env_vars]):
                raise ConnectionError("Required environment variables not found.")

            if access == "read_only":
                user_creds = {"user": os.environ["ATLAS_USER"],
                            "pass": os.environ["ATLAS_USER_PASSWORD"],
                            "rest": os.environ["ATLAS_REST"],
                            "db": db}
            elif access == "annotator":
                user_creds = {"user": os.environ["ANNOTATOR_USER"],
                            "pass": os.environ["ANNOTATOR_PASSWORD"],
                            "rest": os.environ["ATLAS_REST"],
                            "db": db}

        else:
            db_creds = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config/db_creds.json')
            user_creds = json.load(open(db_creds, "r"))["mongo"][access][db]

        uri = "mongodb://{user}:{pass}@{rest}".format(**user_creds)
        super(AtlasConnection, self).__init__(uri, connect=False)
        self.db = self[user_creds["db"]]


    def query(self, mongo_query):
        """
        Wrapper for pymongo db query that enforces correct db.

        Args:
            mongo_query (dict): pymongo style query

        Returns:

        """
        return self.db.query(mongo_query)


class ElasticConnection(Elasticsearch):
    """ Class representing a connection to the Elastic Cloud cluster (ElasticSearch)"""

    def __init__(self, local=local, access="read_only"):
        """
        Args:
            local (bool): True to use local config file, False for environment variables. Default: False
            access (str): Level of access. e.g. "admin", "read_only", or "annotator"
            db (str): Desired database. e.g. "testing" or "production"

        Returns: pymongo Client.

        """

        if not local:
            env_vars = ["ELASTIC_HOST", "ELASTIC_USER", "ELASTIC_PASS"]
            if not all([ev in env for ev in env_vars]):
                raise ConnectionError("Required environment variables not found.")
            if access == "read_only":
                hosts = [env['ELASTIC_HOST']]
                http_auth = (env['ELASTIC_USER'], env['ELASTIC_PASS'])
                super(ElasticConnection, self).__init__(hosts=hosts, http_auth=http_auth)
            else:
                raise PermissionError("Remote access to ES cluster is not allowed.")

        else:
            db_creds = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config/db_creds.json')
            user_creds = json.load(open(db_creds, 'r'))["elastic"][access]
            hosts = user_creds["hosts"]
            http_auth = (user_creds["user"], user_creds["pass"])

        super(ElasticConnection, self).__init__(hosts=hosts, http_auth=http_auth,
                                                use_ssl=True, ca_certs=certifi.where())