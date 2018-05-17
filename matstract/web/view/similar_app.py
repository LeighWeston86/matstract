import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from matstract.models.search import MatstractSearch
from bson import ObjectId

db = AtlasConnection(db="production").db
client = ElasticConnection()

def random_abstract():
    random_document = list(db.abstracts.aggregate([{ "$sample": {"size": 1}}]))[0]
    return random_document['abstract']


def sort_results(results, ids):
    results_sorted = sorted(results, key=lambda k: ids.index(k['_id']))
    return results_sorted


def highlight_material(body, material):
    highlighted_phrase = html.Mark(material)
    if len(material) > 0 and material in body:
        chopped = body.split(material)
        newtext = []
        for piece in chopped[:-1]:
            newtext.append(piece)
            newtext.append(highlighted_phrase)
        newtext.append(chopped[-1])
        return newtext
    return body


def get_search_results(search="", material="", max_results=10000):
    results = None
    if material is None:
        material = ''
    else:
        parser = parsing.SimpleParser()
    if search is None:
        search = ''
    if search == '' and material == '':
        return None
    if material and not search:
        results = db.abstracts_leigh.find({"normalized_cems": parser.matgen_parser(material)})
    elif search and not material:
        ids = find_similar(search, max_results)
        results = sort_results(db.abstracts.find({"_id": {"$in": ids[0:1000]}}), ids)
    elif search and material:
        ids = find_similar(search, max_results)[0:1000]
        results = db.abstracts_leigh.aggregate([
            {"$match": {"_id": {"$in": ids}}},
            {"$match": {"normalized_cems": parser.matgen_parser(material)}}
        ])
    return list(results)


def find_similar(abstract="", max_results=100):
    if abstract is None or abstract == '':
        return None

    query = {"query": {
            "more_like_this" : {
                "fields" : ['title', 'abstract'],
                "like" : abstract
                }
            }}

    hits = client.search(index="tri_abstracts", body=query, size=max_results, request_timeout=60)["hits"]["hits"]
    ids = [ObjectId(h["_id"]) for h in hits]
    print(len(ids))
    return ids


def to_highlight(names_list, material):
    parser = parsing.SimpleParser()
    names = []
    for name in names_list:
        if 'names' in name.keys() and parser.matgen_parser(name['names'][0]) == parser.matgen_parser(material):
            return name['names'][0]


def sort_df(test_df, materials):
    test_df['to_highlight'] = test_df['chem_mentions'].apply(to_highlight, material=materials)
    test_df['count'] = test_df.apply(lambda x: x['abstract'].count(x['to_highlight']), axis=1)
    test_df.sort_values(by='count', axis=0, ascending=False, inplace=True)
    return test_df


def generate_table(search='', materials='', columns=('title', 'authors', 'year', 'abstract'), max_rows=100):
    MS = MatstractSearch()
    results = MS.more_like_this(search, materials, max_results=max_rows)
    if results is not None:
        print(len(results))
    if materials:
        df = pd.DataFrame(results[:max_rows])
        if not df.empty:
            df = sort_df(df, materials)
    else:
        df = pd.DataFrame(results[0:100]) if results else pd.DataFrame()
    if not df.empty:
        format_authors = lambda author_list: ", ".join(author_list)
        df['authors'] = df['authors'].apply(format_authors)
        if len(materials.split(' ')) > 0:
            hm = highlight_material
        else:
            hm = highlight_material
        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(html.A(hm(str(df.iloc[i][col]), df.iloc[i]['to_highlight'] if materials else search),
                               href=df.iloc[i]["link"], target="_blank")) if col == "title"
                else html.Td(df.iloc[i][col]) for col in columns])
                for i in range(min(len(df), max_rows))]
        )
    return html.Table("No Results")


# The Similar app
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Matstract Doppelgängers: find similar abstracts.')
        ], style={'margin-left': '10px'}),
        html.Label('Enter an abstract to find similar entries:'),
        html.Div(dcc.Textarea(id='similar-textarea',
                              style={"width": "100%"},
                              autoFocus=True,
                              spellCheck=True,
                              wrap=True,
                              placeholder='Paste abstract/other text here.'
                              )),
        html.Div([
            dcc.Input(id='similar-material-box',
                      placeholder='Material: e.g. "LiFePO4"',
                      type='text')
        ]),
        html.Div([html.Button('Find Doppelgängers', id='similar-button'),
                  html.Button('Choose a random abstract', id='similar-random')]),
        html.Div([
            html.Table(id='similar-table')
        ], className='row', style={"overflow": "scroll"}),
    ], className='twelve columns'),
])
