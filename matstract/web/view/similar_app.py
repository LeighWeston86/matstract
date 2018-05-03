import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from matstract.utils import open_db_connection, open_es_client
from matstract.models.search import MatstractSearch
from matstract.extract import parsing
from bson import ObjectId

db = open_db_connection(db = "matstract_db")
client = open_es_client()

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


def get_search_results(search=None, materials=None, max_results=100):
    if search is None and materials is None:
        return None
    else:
        search_engine = MatstractSearch()
        ids = None if search is None else find_similar(search, max_results)
        if materials is not None:
            max_results = 1000
            results = search_engine.get_abstracts_by_material(materials, ids=ids)
        else:
            results = sort_results(db.abstracts.find({"_id": {"$in": ids}}), ids)
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
    results = get_search_results(search, materials)
    if results is not None:
        print(len(results))
    if materials:
        df = pd.DataFrame(results[:max_rows])
        # if not df.empty:
        #     df = sort_df(df, materials)
    else:
        df = pd.DataFrame(results[0:100]) if results else pd.DataFrame()
    if not df.empty:
        format_authors = lambda author_list: ", ".join(author_list)
        df['authors'] = df['authors'].apply(format_authors)
        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(html.A(str(df.iloc[i][col]),
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
