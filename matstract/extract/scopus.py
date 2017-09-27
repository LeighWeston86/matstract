from elsapy.elsapy.elsclient import ElsClient
from elsapy.elsapy.elsprofile import ElsAuthor, ElsAffil
from elsapy.elsapy.elsdoc import FullDoc, AbsDoc
from elsapy.elsapy.elssearch import ElsSearch
import json
import os

## Load configuration
con_file = open("../../elsapy/config.json")  # elsapy must be located in the directory above matstract
config = json.load(con_file)
con_file.close()

## Initialize client
client = ElsClient(config['apikey'])
client.inst_token = config['insttoken']

matsearch = ElsSearch('SUBJAREA(MATE) AND DOCTYPE(ar)','scopus')
matsearch.execute(get_all = True, els_client=client)

class ScopusQuery:

    _defaultParams = {'count': 100,
                      'view': 'COMPLETE',
                      'httpAccept': 'application/json',
                      'subjarea':'mate',
                      'doctype':'ar'}
    # The complete view can only be seen by entities
    # subscribing to scopus so make sure to override it
    # in your params dictionary if you are not.

    _baseUrl = "http://api.elsevier.com/content/search/scopus?"

    def __init__(self, client, params, timeout=60):
        self._apiKey = key
        self._keys = None
        if type(key) == type([]):
            self._keys = key
            self._keyCount = 0
            self._apiKey = key[0]
        self._state = "empty"
        self._params = params
        self._data = []
        self._nextUrl = None
        self._i = 0
        self._count = 0
        self._timeout = timeout

class elsadoc:
    def __init__(self):
        self.


def format_abstract_and_metadata(elsadoc=None):
    if not elsadoc:
        raise TypeError("Document is empty.")
    else: