import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from matstract.utils import open_db_connection, open_es_client
from matstract.extract import parsing
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Match, MultiMatch
from bson import ObjectId

db = open_db_connection()
client = open_es_client()

def sort_results(results, ids):
    results_sorted = sorted(results, key=lambda k: ids.index(k['_id']))
    return results_sorted

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
        ids = elastic_search(search, max_results)
        results = sort_results(db.abstracts.find({"_id":{"$in": ids[0:1000]}}), ids)
    elif search and material:
        ids = elastic_search(search, max_results)[0:1000]
        results = db.abstracts_leigh.aggregate([
            {"$match": {"_id": {"$in":ids}}},
            {"$match": {"normalized_cems": parser.matgen_parser(material)}}
        ])
    return list(results)


def elastic_search(search="", max_results=10000):
    if search is None:
        search = ''
    if search == '':
        return None

    query = {"query": {"simple_query_string": {"query": search}}}

    # hits = client.search(index="tri_abstracts", body=query, _source_include=["id"], size=max_results)["hits"]["hits"]
    hits = client.search(index="tri_abstracts", body=query, size=max_results)["hits"]["hits"]
    ids = [ObjectId(h["_id"]) for h in hits]
    return ids

def to_highlight(names_list, material):
    parser = parsing.SimpleParser()
    names = []
    for name in names_list:
        if 'names' in name.keys() and parser.matgen_parser(name['names'][0]) == parser.matgen_parser(material):
            return name['names'][0]


def generate_table(search='', materials='', columns=('title', 'authors', 'year', 'abstract'), max_rows=100):
    results = get_search_results(search, materials)
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
                               href=df.iloc[i]["html_link"], target="_blank")) if col == "title"
                else html.Td(
                    hm(str(df.iloc[i][col]), df.iloc[i]['to_highlight'] if materials else search)) if col == "abstract"
                else html.Td(df.iloc[i][col]) for col in columns])
                for i in range(min(len(df), max_rows))]
        )
    return html.Table("No Results")

# The Search app
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Welcome to the Matstract Database!')
        ], style={'margin-left': '10px'}),

        html.Label('Search for similar abstracts:):'),
        dcc.Textarea(id='search-box',
                     autoFocus=True,
                     spellCheck=True,
                     wrap=True,
                     style={"width": "100%"},
                     placeholder='Search: e.g. "Li-ion battery"'),
    ]),

    html.Div([
        dcc.Input(id='material-box',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Submit', id='search-button'),
    ]),
    # Row 2:
    html.Div([

        html.Div([

        ], className='nine columns', style=dict(textAlign='center')),

    ], className='row'),

    html.Div([
        html.Label(id='number_results'),
        html.Table(id='table-element')
    ], className='row', style={"overflow": "scroll"})
])
