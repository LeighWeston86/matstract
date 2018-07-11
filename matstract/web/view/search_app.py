import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.extract import parsing
from matstract.models.search import MatstractSearch
import re

db = AtlasConnection(db="production").db
client = ElasticConnection()


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


def generate_nr_results(n, search=None, material=None, filters=None):
    if material or search or filters:
        if n == 0:
            return "No Results"
        elif n == 1000:
            return 'Showing {} of >{:,} results'.format(100, n)
        else:
            return 'Showing {} of {:,} results'.format(min(100, n), n)
    else:
        return ''


def generate_table(search=None, materials=None, filters=None,
                   columns=('title', 'authors', 'year', 'journal', 'abstract'),
                   max_rows=100):
    MS = MatstractSearch()
    results = list(MS.search(search, materials=materials, filters=filters))
    if results is not None:
        print("{} search results".format(len(results)))
    if materials:
        df = pd.DataFrame(results[:max_rows])
        # NOT Sorting by material mention count
        # if not df.empty:
        #     df = sort_df(df, materials)
    else:
        df = pd.DataFrame(results[0:100]) if results else pd.DataFrame()
    if not df.empty:
        format_authors = lambda author_list: ", ".join(author_list)
        df['authors'] = df['authors'].apply(format_authors)
        hm = highlight_material
        return [html.Label(generate_nr_results(len(results), search, materials, filters), id="number_results"), html.Table(
            # Header
            [html.Tr([html.Th(col) for col in columns])] +
            # Body
            [html.Tr([
                html.Td(html.A(str(df.iloc[i][col]),
                               href=df.iloc[i]["link"], target="_blank")) if col == "title"
                # else html.Td(
                #     hm(str(df.iloc[i][col]), df.iloc[i]['to_highlight'] if materials else search)) if col == "abstract"
                else html.Td(df.iloc[i][col]) for col in columns])
                for i in range(min(len(df), max_rows))],
            id="table-element")]
    return [html.Label(generate_nr_results(len(results), search, materials, filters), id="number_results"),
            html.Table(id="table-element")]


def serve_layout(path):
    if len(path) > len("/search"):
        path = path[len("/search")+1::]
        path = path.replace("%20", " ")
    else:
        path = None
    # The Search app
    layout = html.Div([
        html.Div([
            html.Label('Search the database ({:,} abstracts!):'.format(db.abstracts.find({}).count())),
            dcc.Textarea(id='search-box',
                         autoFocus=True,
                         spellCheck=True,
                         wrap=True,
                         style={"width": "100%"},
                         placeholder='Search text: e.g. "Li-ion battery"'),
        ]),

        html.Div([
            dcc.Input(id='material-box',
                      placeholder='Filter by material: e.g. "LiFePO4"',
                      style={"width": "200px"},
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
        ], className='row', style={"overflow": "ellipsis"}, id="search_results"),
        html.Div([html.Footer("Attribution Notice: This data was downloaded from the Scopus API between January-July\
         2018 via https://api.elsevier.com and https://www.scopus.com.",
                              style={"color":"grey", "text-align":"center", "font-size":"10pt"})]),
        html.Div([
            dcc.Textarea(id='linked_search_box',
                         value=path),
        ], className='row', style={"display": "none"}, id="search_invisible")
    ])
    return layout
