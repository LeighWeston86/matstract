import os
import requests
import sys
import json
import xml.etree.ElementTree as ET
from requests.exceptions import HTTPError
from elsapy.elsclient import ElsClient
from matstract.utils import open_db_connection
from elsapy.elssearch import ElsSearch
import datetime
from tqdm import tqdm


# Namespaces for Scopus XML
namespaces = {'dtd': 'http://www.elsevier.com/xml/svapi/abstract/dtd',
              'dn': 'http://www.elsevier.com/xml/svapi/abstract/dtd',
              'ar': 'http://www.elsevier.com/xml/svapi/article/dtd',
              'ait': "http://www.elsevier.com/xml/ani/ait",
              'cto': "http://www.elsevier.com/xml/cto/dtd",
              'xocs': "http://www.elsevier.com/xml/xocs/dtd",
              'ce': 'http://www.elsevier.com/xml/ani/common',
              'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
              'xsi': "http://www.w3.org/2001/XMLSchema-instance",
              'dc': 'http://purl.org/dc/elements/1.1/',
              'dcterms': 'http://purl.org/dc/terms/',
              'atom': 'http://www.w3.org/2005/Atom',
              'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}

config = json.load(open('matstract/collect/scopus_config.json', 'r'))
APIKEY = config["apikey"]

## Initialize client
CLIENT = ElsClient(config['apikey'], num_res=1)
CLIENT.inst_token = config['insttoken']


def check_scopus_collection(year, issn):
    """
    Checks the scopus_log collection on MongoDB whether the data for a given year/journal combination
    has been collected.

    Args:
        year: (str) year
        issn: (str) issn of journal

    Returns:
        (bool) True if status of the year/journal pair is "complete"

    """
    db = open_db_connection()
    log = db.elsevier_log
    entry = log.find({"year": year, "issn": issn})[0]
    if entry["status"] == "complete":
        return True
    elif entry["status"] == "incomplete":
        return False
    else:
        raise KeyError("Entry has no status!")


def build_scopus_query(year=None, issn=None):
    """ Builds a query from a given year, volume, and letter (for author's 1st initial)

    e.g.

    build_query(1994) would return:

    "SUBJAREA(MATE) AND DOCTYPE(ar) AND LANGUAGE(english) AND PUBYEAR = 1994"

    """
    base = "SUBJAREA(MATE) AND DOCTYPE(ar) AND LANGUAGE(english)"
    y = " AND PUBYEAR = {}".format(year) if year else ''
    i = " AND ISSN({}) OR EISSN({})".format(issn, issn) if issn else ''

    return base + y + i


def find_articles(year=None, issn=None, get_all=True):
    """
    Returns a list of the DOI's for all articles published in the specified year and journal.

    Args:
        year: (str) year of publication
        issn: (str) ISSN (or EISSN) of journal
        get_all: (bool) Whether all results should be returned or just the 1st result. Default is True.

    Returns:
        dois: [str] The dois for all articles published in corresponding journal + year

    """

    query = build_scopus_query(year=year, issn=issn)
    search = ElsSearch(query, index='scopus')
    search.execute(els_client=CLIENT, get_all=get_all)
    dois=[]
    for r in search.results:
        try:
            dois.append(r['prism:doi'])
        except:
            continue
    return dois


def download(url, format='xml', params=None):
    """
    Helper function to download a file and return its content.

    Args:
        url: (str) The URL to be parsed.
        params: (dict, optional) Dictionary containing query parameters.  For required keys
            and accepted values see e.g.
            https://api.elsevier.com/documentation/AuthorRetrievalAPI.wadl

    Returns:
        resp : (byte-like object)
            The content of the file, which needs to be serialized.

    Raises:
        (HTTPError) If the status of the response is not ok.

    """

    header = {'Accept': 'application/{}'.format(format), 'X-ELS-APIKey': APIKEY}
    resp = requests.get(url, headers=header, params=params)
    resp.raise_for_status()

    return resp


def get_content(DOI, refresh=True, *args, **kwds):
    """Helper function to read file content as xml.

    Parameters
    ----------
    DOI : string
        DOI of article, for checking database.

    *args, **kwds :
        Arguments and keywords to be passed on to download().

    Returns
    -------
    content : str
        The content of the file.
    """
    if not refresh:
        db = open_db_connection()
        elsevier = db.elsevier
        entries = elsevier.find({"doi": DOI})
        if len(entries):
            if len(entries) > 1:
                print("More than one entry for given DOI! Only using only first entry.")
            entry = entries[0]
            if entry["collected"]:
                content = entry["xml"]
                return content
    content = download(*args, **kwds).text
    return content

def get_content_html(input_doi, *args, **kwds):
    """Helper function to read file content as xml.

    Parameters
    ----------
    DOI : string
        DOI of article, for checking database.

    *args, **kwds :
        Arguments and keywords to be passed on to download().

    Returns
    -------
    content : str
        The content of the file.
    """

    url = "https://api.elsevier.com/content/article/doi/{}".format(input_doi)
    content = download(url, format='html')
    return content


def get_encoded_text(container, xpath):
    """
    Returns contents of the element at xpath in the container xml if it is there.

    Args:
        container: (xml.etree.ElementTree.Element)
            The element to be searched in.
        xpath: (str) The path to be looked for.

    Returns:
        result: (str)

    """

    try:
        items = [i.text if i.text else i for i in container.findall(xpath, namespaces)]
        if len(items) == 1:
            return items[0]
        elif len(items) == 0:
            return None
        else:
            return items
    except AttributeError:
        return None
    except SyntaxError:
        print("Syntax error", xpath)
        return None


class ScopusArticle(object):

    def __init__(self, input_doi='', refresh=True):
        """
        A class that represents a Scopus article.

        Args:

            input_doi: (str) DOI of article

            refresh: (bool) Whether the article should be pulled from scopus or whether it should be
                    pulled from the mongodb.
        """

        url = "https://api.elsevier.com/content/article/doi/{}".format(input_doi)
        self._url = url

        params = {'view': "FULL"}
        xml = ET.fromstring(get_content(input_doi, url=url, refresh=refresh, params=params))

        # Remove default namespace if present
        remove = u'{http://www.elsevier.com/xml/svapi/article/dtd}'
        namespace_length = len(remove)
        for elem in xml.getiterator():
            if elem.tag.startswith(remove):
                elem.tag = elem.tag[namespace_length:]

        self.xml = xml
        if xml.tag == 'service-error':
            raise Exception('\n{0}\n{1}'.format(input_doi, self.xml))

        # Parse coredata
        coredata = xml.find('coredata', namespaces)
        self._eid = get_encoded_text(coredata, 'eid')
        self._doi = get_encoded_text(coredata, 'prism:doi')
        self._coverDate = get_encoded_text(coredata, 'prism:coverDate')
        self._coverDisplayDate = get_encoded_text(coredata, 'prism:coverDisplayDate')
        self._url = get_encoded_text(coredata, 'prism:url')
        self._links = get_encoded_text(coredata, 'link')
        self._identifier = get_encoded_text(coredata, 'dc:identifier')
        self._title = get_encoded_text(coredata, 'dc:title')
        self._publicationName = get_encoded_text(coredata, 'prism:publicationName')
        self._issn = get_encoded_text(coredata, 'prism:issn')
        self._isbn = get_encoded_text(coredata, 'prism:isbn')
        self._aggregationType = get_encoded_text(coredata, 'prism:aggregationType')
        self._edition = get_encoded_text(coredata, 'prism:edition')
        self._volume = get_encoded_text(coredata, 'prism:volume')
        self._issueIdentifier = get_encoded_text(coredata, 'prism:issueIdentifier')
        self._startingPage = get_encoded_text(coredata, 'prism:startingPage')
        self._endingPage = get_encoded_text(coredata, 'prism:endingPage')
        self._creator = get_encoded_text(coredata, 'dc:creator')
        self._authors = get_encoded_text(coredata, 'authors')
        self._format = get_encoded_text(coredata, 'dc:format')
        self._subjects = get_encoded_text(coredata, 'dcterms:subject')
        self._copyright = get_encoded_text(coredata, 'prism:copyright')
        self._publisher = get_encoded_text(coredata, 'prism:publisher')
        self._issueName = get_encoded_text(coredata, 'prism:IssueName')
        self._pageRange = get_encoded_text(coredata, 'prism:pageRange')
        self._number = get_encoded_text(coredata, 'prism:number')
        self._abstract = get_encoded_text(coredata, 'dc:description')

    @property
    def url(self):
        for link in self._links:
            if not "self" in link.items()[1]:
                return link.items()[0][1]

    @property
    def scopus_url(self):
        """URL to the scopus entry for the article."""
        return self._url

    @property
    def doi(self):
        """DOI of article."""
        return self._doi

    @property
    def eid(self):
        """ EID of article."""
        return self._eid

    @property
    def scopus_id(self):
        """Scopus source_id of the article."""
        return self._identifier

    @property
    def title(self):
        """Article title."""
        return self._title

    @property
    def authors(self):
        """The list of the article's authors"""
        return self._creator

    @property
    def abstract(self):
        """The abstract of the article."""
        return self._abstract

    @property
    def journal(self):
        """Name Journal the article is published in."""
        return self._publicationName

    @property
    def issn(self):
        """ISSN of the publisher.
        Note: If E-ISSN is known to Scopus, this returns both
        ISSN and E-ISSN in random order separated by blank space.
        """
        return self._issn

    @property
    def publisher(self):
        """Name of the publisher of the article."""
        return self._publisher

    @property
    def volume(self):
        """Volume for the article."""
        return self._volume

    @property
    def issue(self):
        """Issue number for article."""
        return self._issueIdentifier

    @property
    def article_number(self):
        """Article number."""
        return self._number

    @property
    def first_page(self):
        """Starting page."""
        return self._startingPage

    @property
    def last_page(self):
        """Ending page."""
        return self._endingPage

    @property
    def page_range(self):
        """Page range."""
        return self._pageRange

    @property
    def cover_date(self):
        """The date of the cover the article is in."""
        return self._coverDate

    @property
    def subjects(self):
        """List of subject areas of article.
        Note: Requires the FULL view of the article.
        """
        return self._subjects


def contribute(user_creds, max_entries=1000):
    """
    Gets a incomplete year/journal combination from elsevier_log, queries for the corresponding
    dois, and downloads the corresponding xmls for each to the elsevier collection.

    Args:
        user_creds: path to contributing user's write-permitted credential file.
        max_entries: maximum length of session (~1s/article)

    """

    user = json.load(open(user_creds, 'r'))["name"]
    db = open_db_connection(user_creds=user_creds)
    log = db.elsevier_log
    elsevier = db.elsevier

    target = log.find({"status": "incomplete", "num_articles": {"$lt": max_entries}}, ["year", "issn"]).limit(1)[0]

    date = datetime.datetime.now().isoformat()

    log.update_one({"year": target["year"], "issn": target["issn"], "status": "incomplete"},
                   {"$set": { "status": "in progress"}})

    dois = find_articles(year=target["year"], issn=target["issn"], get_all=True)
    new_entries = []

    for doi in tqdm(dois):
        date = datetime.datetime.now().isoformat()
        try:
            article = ScopusArticle(input_doi=doi)
            abstract = article.abstract
            if not isinstance(abstract, str):
                abstract = abstract.text
            new_entries.append({"doi": doi, "title":article.title, "abstract": abstract,
                                "authors": article.authors, "url": article.url, "subjects":article.subjects,
                                "journal": article.journal, "date": article.cover_date,
                                "completed": True, "pulled_on": date, "pulled_by": user})
        except HTTPError as e:
            new_entries.append({"doi": doi, "completed":False, "error": e,
                                "pulled_on": date, "pulled_by":user})

    for entry in new_entries:
        if elsevier.find({"doi":entry["doi"]}).count():
            elsevier.update_one({"doi":entry["doi"]}, {"$set": entry})
        else:
            elsevier.insert_one(entry)

    date = datetime.datetime.now().isoformat()
    log.update_one({"year": target["year"], "issn": target["issn"], "status": "in_progress"},
                   {"$set": { "status": "complete", "completed_by": user, "completed_on": date}})
