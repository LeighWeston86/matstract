import requests
import json
import xml.etree.ElementTree as ET
from requests.exceptions import HTTPError
from elsapy.elsclient import ElsClient
from matstract.models.database import AtlasConnection
from elsapy.elssearch import ElsSearch
import datetime
from tqdm import tqdm
import re

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
              'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
              'ani': 'http://www.elsevier.com/xml/ani/common'}

config = json.load(open('matstract/config/db_creds.json', 'r'))["scopus"]
APIKEY = config["apikey"]

## Initialize client
CLIENT = ElsClient(config['apikey'], num_res=100)
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
    db = AtlasConnection(access='admin', db="test").db
    log = db.build_log
    entry = log.find({"year": year, "issn": issn})[0]
    if entry["status"] == "complete":
        return True
    elif entry["status"] == "incomplete":
        return False
    else:
        raise KeyError("Entry has no status!")


def build_scopus_query(year=None, issn=None):
    """ Builds a query from a given year and journal

    e.g.

    build_query(year=1994, issn="1234-5678") would return:

    "SUBJAREA(MATE) AND DOCTYPE(ar) AND LANGUAGE(english) AND PUBYEAR =1994 AND ISSN(1234-5678) OR EISSN(1234-5678)"

    Args:
        year (str): year of publication
        issn (str): ISSN of journal

    Returns:
        (str) scoupus query string

    """
    base = "SUBJAREA(MATE) AND DOCTYPE(ar) AND LANGUAGE(english)"
    y = " AND PUBYEAR = {}".format(year) if year else ''
    i = " AND ISSN({}) OR EISSN({})".format(issn, issn) if issn else ''

    return base + y + i


def find_articles(year=None, issn=None, get_all=True, id_type="doi", apikey=None):
    """
    Returns a list of the DOI's for all articles published in the specified year and journal.

    Args:
        year (str): year of publication
        issn (str): ISSN (or EISSN) of journal
        get_all (bool): Whether all results should be returned or just the 1st result. Default is True.
        id_type: (str) Return document eids or dois. Default is doi.

    Returns:
        ids (str): The eids/dois for all articles published in corresponding journal in the specified year

    """

    query = build_scopus_query(year=year, issn=issn)
    if apikey:
        CLIENT = ElsClient(apikey, num_res=10000)
    search = ElsSearch(query, index='scopus', )
    search.execute(els_client=CLIENT, get_all=get_all)
    if id_type == "doi":
        key = 'prism:doi'
    else:
        key = id_type
    ids = []
    for r in search.results:
        try:
            ids.append(r[key])
        except:
            continue
    return ids


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


def get_content(DOI, format="json", refresh=True, *args, **kwds):
    """ Helper function to read file content as xml.

    Args:
        input_doi (str): DOI of article
        *args:
        **kwds:

    Returns:
        Content of returned XML file

    """

    if not refresh:
        db = AtlasConnection().db
        elsevier = db.elsevier
        entries = elsevier.find({"doi": DOI})
        if len(entries):
            if len(entries) > 1:
                print("More than one entry for given DOI! Only using only first entry.")
            entry = entries[0]
            if entry["collected"]:
                content = entry["xml"]
                return content
    else:
        if format == "xml":
            content = download(*args, **kwds).text
            return content
        elif format == "json":
            content = download(*args, **kwds)
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


def clean_text(text):
    """ Cleans abstract text from scopus documents.

    Args:
        text (str): Unformatted abstract text.

    Returns:
        (str) Abstract text with formatting issues removed.

    """
    if text is None:
        return None
    try:
        cleaned_text = re.sub("© ([0-9])\w* The Author(s)*\.( )*", "", text)
        cleaned_text = re.sub("Published by Elsevier Ltd\.", "", cleaned_text)
        cleaned_text = re.sub("\n                        ", "", cleaned_text)
        cleaned_text = re.sub("\n                     ", "", cleaned_text)
        cleaned_text = " ".join("".join(cleaned_text.split("\n               ")).split())
        cleaned_text = cleaned_text.replace("Abstract ", '', 1)
        return cleaned_text
    except:
        return None


def format_authors(author_dict):
    """ Reformats a dict of authors to a list"""
    authors = []
    for entry in author_dict:
        if not "ce:given-name" in entry:
            if entry['preferred-name']["ce:given-name"] is not None:
                entry["ce:given-name"] = entry['preferred-name']["ce:given-name"]
            else:
                continue
        if not "ce:surname" in entry:
            if entry['preferred-name']["ce:surname"] is not None:
                entry["ce:surname"] = entry['preferred-name']["ce:surname"]
            else:
                continue
        authors.append(entry["ce:surname"] + ", " + entry["ce:given-name"])
    return authors


def format_terms(term_dict):
    """ Extracts the keywords from term_dict to a list."""
    if term_dict is None:
        return None

    if term_dict:
        terms = []
        for entry in term_dict["mainterm"]:
            if isinstance(entry, dict):
                terms.append(entry["$"])
            elif isinstance(entry, str):
                terms.append(entry)
        return terms


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
        self.retrieval_url = url

        params = {'view': "FULL"}
        xml = ET.fromstring(get_content(input_doi, url=url, format="xml", refresh=refresh, params=params))

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

        # Scopus URL of article
        self.scopus_url = get_encoded_text(coredata, 'prism:url')

        # Scopus source_id of the article
        self.scopus_id = get_encoded_text(coredata, 'dc:identifier')

        # URL of article
        for link in get_encoded_text(coredata, 'link'):
            if not "self" in link.items()[1]:
                url = link.items()[0][1]
        self.url = url

        # EID of article
        self.eid = get_encoded_text(coredata, 'eid')

        # DOI of article
        self.doi = get_encoded_text(coredata, 'prism:doi')

        # Title of article
        self.title = get_encoded_text(coredata, 'dc:title')

        # Authors of Article
        self.authors = get_encoded_text(coredata, 'dc:creator')

        # Journal Name
        self.journal = get_encoded_text(coredata, 'prism:publicationName')

        # Date of publication
        self.cover_date = get_encoded_text(coredata, 'prism:coverDate')

        # Date of publication (cover)
        self.cover_display_date = get_encoded_text(coredata, 'prism:coverDisplayDate')

        # Journal ISSN (or EISSN, or both)
        self.issn = get_encoded_text(coredata, 'prism:issn')

        # Volume that article appears in
        self.volume = get_encoded_text(coredata, 'prism:volume')

        # Issue that article appears in.
        self.issue = get_encoded_text(coredata, 'prism:issueIdentifier')

        # Article number
        self.article_number = get_encoded_text(coredata, 'prism:number')

        # Page number of first page
        self.first_page = get_encoded_text(coredata, 'prism:startingPage')

        # Page number of last page
        self.last_page = get_encoded_text(coredata, 'prism:endingPage')

        # Page range of article
        self.page_range = get_encoded_text(coredata, 'prism:pageRange')

        # Format of Article
        self.format = get_encoded_text(coredata, 'dc:format')

        # Subjects of article
        self.subjects = get_encoded_text(coredata, 'dcterms:subject')

        # Copywrite info
        self.copyright = get_encoded_text(coredata, 'prism:copyright')

        # Name of publisher
        self.publisher = get_encoded_text(coredata, 'prism:publisher')

        # Name of issue
        self.issue_name = get_encoded_text(coredata, 'prism:IssueName')

        # Raw copy of abstract as returned by scopus
        self.raw_abstract = get_encoded_text(coredata, 'dc:description')

        # Cleaned abstract text
        self.abstract = clean_text(get_encoded_text(coredata, 'dc:description'))


class ScopusAbstract(object):

    def __init__(self, input_doi='', refresh=True):
        """
        A class that represents a Scopus article.

        Args:

            input_doi: (str) DOI of article

            refresh: (bool) Whether the article should be pulled from scopus or whether it should be
                    pulled from the mongodb.
        """

        url = "https://api.elsevier.com/content/abstract/doi/{}".format(input_doi)
        self.retrieval_url = url

        params = {'view': "FULL"}
        response = json.loads(download(url=url, format="json", params=params).text)
        response = response["abstracts-retrieval-response"]

        self.json = response

        # Parse coredata
        coredata = self.json["coredata"]

        # Scopus URL of article
        self.scopus_url = coredata.get("prism:url")

        # Scopus source_id of the article
        self.scopus_id = coredata.get('dc:identifier')

        # DOI of article
        self.doi = coredata.get('prism:doi')

        # URL of article
        url = "https://doi.org/"
        self.url = url + self.doi

        # EID of article
        self.eid = coredata.get('eid')

        # Title of article
        self.title = coredata.get('dc:title')

        # Authors of Article
        self.authors = format_authors(response["authors"]["author"])

        # Journal Name
        self.journal = coredata.get('prism:publicationName')

        # Date of publication
        self.cover_date = coredata.get('prism:coverDate')

        # Journal ISSN (or EISSN, or both)
        self.issn = coredata.get('prism:issn')

        # Volume that article appears in
        self.volume = coredata.get('prism:volume')

        # Issue that article appears in.
        self.issue = coredata.get('prism:issueIdentifier')

        # Article number
        self.article_number = coredata.get('prism:number')

        # Page number of first page
        self.first_page = coredata.get('prism:startingPage')

        # Page number of last page
        self.last_page = coredata.get('prism:endingPage')

        # Page range of article
        self.page_range = coredata.get('prism:pageRange')

        # Format of Article
        self.format = coredata.get('subtypeDescription')

        # Subjects of article
        self.subjects = format_terms(response.get('idxterms'))

        # Name of publisher
        # Not Avaliable in Abstract Retrieval view

        # Name of issue
        self.issue_name = coredata.get('prism:issueIdentifier')

        # Abstract
        self.raw_abstract = coredata.get('dc:description')
        self.abstract = clean_text(coredata.get('dc:description'))


class MiniAbstract(object):

    def __init__(self, entry):
        """
        A class that represents a Scopus article.

        Args:

            input_doi: (str) DOI of article

            refresh: (bool) Whether the article should be pulled from scopus or whether it should be
                    pulled from the mongodb.
        """

        # Scopus URL of article
        self.scopus_url = entry.get("prism:url")

        # Scopus source_id of the article
        self.scopus_id = entry.get('dc:identifier')

        # DOI of article
        self.doi = entry.get('prism:doi')

        # URL of article
        url = "https://doi.org/"
        self.url = url + self.doi

        # EID of article
        self.eid = entry.get('eid')

        # Title of article
        self.title = entry.get('dc:title')

        # Authors of Article
        authlist = entry.get("author", [])
        authors = []
        for author in authlist:
            if author["surname"] is not None and author["given-name"] is not None:
                authors.append(author["surname"] + ", " + author["given-name"])
            elif author["authname"] is not None:
                authors.append(author["authname"])
            else:
                continue
        self.authors = authors

        # Journal Name
        self.journal = entry.get('prism:publicationName')

        # Date of publication
        self.cover_date = entry.get('prism:coverDate')

        # Journal ISSN (or EISSN, or both)
        self.issn = entry.get('prism:issn')

        # Volume that article appears in
        self.volume = entry.get('prism:volume')

        # Issue that article appears in.
        self.issue = entry.get('prism:issueIdentifier')

        # Article number
        self.article_number = entry.get('article-number')

        # Number of Citations
        self.citations = entry.get('citedby-count')

        # Page range of article
        self.page_range = entry.get('prism:pageRange')

        # Format of Article
        self.format = entry.get('subtypeDescription')

        # Name of publisher
        # Not Avaliable in Search Complete view

        # Abstract
        self.raw_abstract = entry.get('dc:description')
        self.abstract = clean_text(entry.get('dc:description'))


def verify_access():
    """ Confirms that the user is connected to a network with full access to Elsevier.
    i.e. the LBNL Employee Network

    Raises:
        HTTPError: If user is not connected to network with full-text subscriber access to Elsevier content.

    """
    try:
        download("https://api.elsevier.com/content/article/doi/10.1016/j.actamat.2018.01.057?view=FULL")
    except HTTPError:
        raise HTTPError(" Cannot retreive full document from Elsevier API. \n \n"
                        "Please confrim that you're connected to the LBNL employee network or "
                        "the LBNL VPN.")


def collect_entries(dois, user, entry_type="abstract"):
    """ Collects the scopus entry for each DOI in dois and processes them for insertion into the Matstract database.

    Args:
        dois (list(str)): List of DOIs
        user: (dict): Credentials of user
        entry_type (str): "full_article" or "abstract". Default is "abstract"

    Returns:
        entries (list(dict)): List of entries to be inserted into database

    """

    entries = []
    for doi in tqdm(dois):
        date = datetime.datetime.now().isoformat()
        try:
            if entry_type == "full_article":
                article = ScopusArticle(input_doi=doi)
                abstract = article.abstract
                raw_abstract = article.raw_abstract

                if abstract is None or raw_abstract is None:
                    entries.append({"doi": doi, "completed": False, "error": "No Abstract!",
                                    "pulled_on": date, "pulled_by": user})
                else:
                    if not isinstance(raw_abstract, str):
                        raw_abstract = raw_abstract.text
                    entries.append({"doi": doi, "title": article.title, "abstract": abstract,
                                    "raw_abstract": raw_abstract, "authors": article.authors, "url": article.url,
                                    "subjects": article.subjects, "journal": article.journal,
                                    "date": article.cover_date, "full_xml": article.xml,
                                    "completed": True, "pulled_on": date, "pulled_by": user})

            elif entry_type == "abstract":
                article = ScopusAbstract(input_doi=doi)
                abstract = article.abstract
                raw_abstract = article.raw_abstract
                if abstract is None or raw_abstract is None:
                    entries.append({"doi": doi, "completed": False, "error": "No Abstract!",
                                    "pulled_on": date, "pulled_by": user})
                else:
                    entries.append({"doi": doi, "title": article.title, "abstract": abstract,
                                    "raw_abstract": raw_abstract, "authors": article.authors, "url": article.url,
                                    "subjects": article.subjects, "journal": article.journal,
                                    "date": article.cover_date,
                                    "completed": True, "pulled_on": date, "pulled_by": user})

        except HTTPError as e:
            entries.append({"doi": doi, "completed": False, "error": str(e),
                            "pulled_on": date, "pulled_by": user})
    return entries


def collect_entries_by_doi_search(dois, user, apikey=None):
    """ Collects the scopus entry for each DOI in dois and processes them for insertion into the Matstract database.

    Args:
        dois (list(str)): List of DOIs
        user: (dict): Credentials of user
        entry_type (str): "full_article" or "abstract". Default is "abstract"

    Returns:
        entries (list(dict)): List of entries to be inserted into database

    """

    entries = []
    miniblocks = [dois[x:x + 25] for x in range(0, len(dois), 25)]

    for miniblock in tqdm(miniblocks):

        query = " OR ".join(["DOI({})".format(doi) for doi in miniblock])
        search = ElsSearch(query=query, index="scopus")
        search._uri = search.uri + "&view=COMPLETE"
        if apikey:
            CLIENT = ElsClient(apikey, num_res=10000)

        search.execute(els_client=CLIENT, get_all=True)
        results = search.results

        for result in results:
            date = datetime.datetime.now().isoformat()
            doi = result['prism:doi']
            try:
                article = MiniAbstract(result)
                abstract = article.abstract
                raw_abstract = article.raw_abstract
                if abstract is None or raw_abstract is None:
                    entries.append({"doi": doi, "completed": False, "error": "No Abstract!",
                                    "pulled_on": date, "pulled_by": user})
                else:
                    entries.append({"doi": doi, "title": article.title, "abstract": abstract,
                                    "raw_abstract": raw_abstract, "authors": article.authors, "url": article.url,
                                    "subjects": [], "journal": article.journal,
                                    "date": article.cover_date, "citations": article.citations,
                                    "completed": True, "pulled_on": date, "pulled_by": user})

            except HTTPError as e:
                entries.append({"doi": doi, "completed": False, "error": str(e),
                                "pulled_on": date, "pulled_by": user})
    return entries


def contribute(user_creds="matstract/config/db_creds.json", max_block_size=100, num_blocks=1, apikey=None):
    """
    Gets a incomplete year/journal combination from elsevier_log, queries for the corresponding
    dois, and downloads the corresponding xmls for each to the elsevier collection.

    Args:
        user_creds ((:obj:`str`, optional)): path to contributing user's write-permitted credential file.
        max_block_size ((:obj:`int`, optional)): maximum number of articles in block (~1s/article). Defaults to 100.
        num_blocks ((:obj:`int`, optional)): maximum number of blocks to run in session. Defaults to 1.

    """
    # user = json.load(open(user_creds, "r"))["name"]

    user = json.load(open(user_creds, 'r'))["mongo"]["admin"]["test"]["name"]

    db = AtlasConnection(access="admin", db="production").db
    log = db.build_log
    build = db.build

    for i in range(num_blocks):
        # Verify access at start of each block to detect dropped VPN sessions.
        verify_access()

        # Get list of all available blocks sorted from largest to smallest.
        available_blocks = log.find({"status": "incomplete",
                                     "num_articles": {"$lt": max_block_size}},
                                    ["year", "issn", "journal"]).limit(1).sort("num_articles", -1)

        # Break if no remaining blocks smaller than max_block_size
        if available_blocks.count() == 0:
            print("No remaining blocks with size <= {}.".format(max_block_size))
            break
        else:
            print("Blocks remaining = {}".format(min(num_blocks - i, available_blocks.count())))

        target = available_blocks[0]
        date = datetime.datetime.now().isoformat()
        log.update_one({"year": target["year"], "issn": target["issn"], "status": "incomplete"},
                       {"$set": {"status": "in progress", "updated_by": user, "updated_on": date}})

        # Collect scopus for block
        if "journal" in target:
            print("Collecting entries for {}, {} (Block ID {})...".format(target.get("journal"),
                                                                          target.get("year"),
                                                                          target.get("_id")))
        else:
            print("Collecting entries for {}, {} (Block ID {})...".format(target.get("issn"),
                                                                          target.get("year"),
                                                                          target.get("_id")))
        dois = find_articles(year=target["year"], issn=target["issn"], get_all=True, apikey=apikey)
        new_entries = collect_entries_by_doi_search(dois, user, apikey=apikey)

        # Update log with number of articles for block
        num_articles = len(new_entries)
        log.update_one({"year": target["year"], "issn": target["issn"], "status": "in progress"},
                       {"$set": {"num_articles": num_articles}})

        # Insert entries into Matstract database
        print("Inserting entries into Matstract database...")
        for entry in tqdm(new_entries):
            if build.find({"doi": entry["doi"]}).count():
                build.update_one({"doi": entry["doi"]}, {"$set": entry})
            else:
                build.insert_one(entry)

        # Mark block as completed in log
        date = datetime.datetime.now().isoformat()
        log.update_one({"year": target["year"], "issn": target["issn"], "status": "in progress"},
                       {"$set": {"status": "complete", "completed_by": user, "completed_on": date,
                                 "updated_by": user, "updated_on": date, }})
