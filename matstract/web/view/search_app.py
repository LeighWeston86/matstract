import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from matstract.utils import open_db_connection, open_es_client
from matstract.models.search import MatstractSearch
from matstract.extract import parsing
from bson import ObjectId

db = open_db_connection(db="matstract_db")
client = open_es_client()


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


def highlight_multiple_materials(body, materials):
    if len(materials) > 0 and any([material in body for material in materials]):
        newtext = []
        for material in materials:
            highlighted_phrase = html.Mark(material)
            if len(newtext) > 0:
                for body in newtext:
                    if type(body) == 'string' and len(material) > 0 and material in body:
                        chopped = body.split(material)
                        newnewtext = []
                        i = newtext.index(body)
                        for piece in chopped[:-1]:
                            newnewtext.append(piece)
                            newnewtext.append(highlighted_phrase)
                        newnewtext.append(chopped[-1])
                        newtext[i:i + 1] = newnewtext
            else:
                if len(material) > 0 and material in body:
                    chopped = body.split(material)
                    for piece in chopped[:-1]:
                        newtext.append(piece)
                        newtext.append(highlighted_phrase)
                    newtext.append(chopped[-1])
        return newtext
    return body


def search_for_material(material, search):
    db = open_db_connection()
    if search:
        results = db.abstracts.find({"$text": {"$search": search}, "chem_mentions.names": material}, ["year"])
    else:
        results = db.abstracts.find({"chem_mentions.names": material}, ["year"])
    return list(results)


def search_for_topic(search):
    db = open_db_connection(db="matstract_db")
    if search:
        results = db.abstracts.find({"$or": [{"title": {"$regex": ".*{}.*".format(search)}},
                                             {"abstract": {"$regex": ".*{}.*".format(search)}}]}, ["year"])
        print(results.count())
        return list(results)
    else:
        return []


def sort_results(results, ids):
    results_sorted = sorted(results, key=lambda k: ids.index(k['_id']))
    return results_sorted


def get_search_results(search=None, materials=None, max_results=1001):
    if search is None and materials is None:
        return None
    else:
        search_engine = MatstractSearch()
        ids = None if search is None else elastic_search(search, max_results)[:1000]
        if materials is not None:
            results = search_engine.get_abstracts_by_material(materials, ids=ids)
        else:
            results = sort_results(db.abstracts.find({"_id": {"$in": ids[:1000]}}), ids[:1000])
        return list(results)


def elastic_search(search=None, max_results=10000):
    if search is None:
        return None
    query = {"query": {"simple_query_string": {"query": search}}}
    # hits = client.search(index="tri_abstracts", body=query, _source_include=["id"], size=max_results)["hits"]["hits"]
    hits = client.search(index="tri_abstracts", body=query, size=max_results, request_timeout=30)["hits"]["hits"]
    ids = [ObjectId(h["_id"]) for h in hits]
    return ids


def to_highlight(names_list, material):
    parser = parsing.SimpleParser()
    for name in names_list:
        if parser.matgen_parser(name) == parser.matgen_parser(material):
            return material


def sort_df(test_df, materials):
    test_df['to_highlight'] = test_df['chem_mentions'].apply(to_highlight, material=materials)
    test_df['count'] = test_df.apply(lambda x: x['abstract'].count(x['to_highlight']), axis=1)
    test_df.sort_values(by='count', axis=0, ascending=False, inplace=True)
    return test_df


def generate_nr_results(n, search=None, material=None):
    if material or search:
        if n == 0:
            return "No Results"
        elif n == 1000:
            return 'Showing {} of >{:,} results'.format(100, n)
        else:
            return 'Showing {} of {:,} results'.format(min(100, n), n)
    else:
        return ''


# def generate_table(search=None, materials=None, columns=('title', 'authors', 'year', 'abstract'), max_rows=100):
#     results = get_search_results(search, materials)
#     if results is not None:
#         print("{} search results".format(len(results)))
#     if materials:
#         df = pd.DataFrame(results[:max_rows])
#         if not df.empty:
#             df = sort_df(df, materials)
#     else:
#         df = pd.DataFrame(results[0:100]) if results else pd.DataFrame()
#     if not df.empty:
#         format_authors = lambda author_list: ", ".join(author_list)
#         df['authors'] = df['authors'].apply(format_authors)
#         hm = highlight_material
#         return [html.Label(generate_nr_results(len(results), search, materials), id="number_results"), html.Table(
#             # Header
#             [html.Tr([html.Th(col) for col in columns])] +
#             # Body
#             [html.Tr([
#                 html.Td(html.A(hm(str(df.iloc[i][col]), df.iloc[i]['to_highlight'] if materials else search),
#                                href=df.iloc[i]["link"], target="_blank")) if col == "title"
#                 else html.Td(
#                     hm(str(df.iloc[i][col]), df.iloc[i]['to_highlight'] if materials else search)) if col == "abstract"
#                 else html.Td(df.iloc[i][col]) for col in columns])
#                 for i in range(min(len(df), max_rows))],
#             id="table-element")]
#     return [html.Label(generate_nr_results(len(results), search, materials), id="number_results"), html.Table(id="table-element")]


def generate_table(search=None, materials=None, columns=('title', 'authors', 'journal', 'year', 'abstract'), max_rows=100):
    results = get_search_results(search, materials)
    if results is not None:
        print("{} search results".format(len(results)))
    if materials:
        df = pd.DataFrame(results[:max_rows])
        if not df.empty:
            if isinstance(materials, list) and len(materials) == 1:
                df = sort_df(df, materials)
    else:
        df = pd.DataFrame(results[0:100]) if results else pd.DataFrame()
    if not df.empty:
        format_authors = lambda author_list: ", ".join(author_list)
        df['authors'] = df['authors'].apply(format_authors)
        return [html.Label(generate_nr_results(len(results), search, materials), id="number_results"), html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(html.A(str(df.iloc[i][col]),
                               href=df.iloc[i]["link"], target="_blank")) if col == "title"
                else html.Td(
                    str(df.iloc[i][col])) if col == "abstract"
                else html.Td(df.iloc[i][col]) for col in columns])
                for i in range(min(len(df), max_rows))],
            id="table-element")]
    return [html.Label(generate_nr_results(len(results), search, materials), id="number_results"), html.Table(id="table-element")]

# The Search app
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Welcome to the Matstract Database!')
        ], style={'margin-left': '10px'}),

        html.Label('Search the database ({:,} abstracts!):'.format(db.abstracts.find({}).count())),
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
    ], className='row', style={"overflow": "scroll"}, id="search_results")
])
