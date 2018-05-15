import dash_html_components as html
import dash_core_components as dcc
from matstract.utils import open_db_connection
from matstract.extract.parsing import SimpleParser
from matstract.nlp.theme_extractor import analyze_themes
import pandas as pd
from math import trunc
import nltk


def generate_table(dataframe, max_rows=100):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def gen_output(most_common, size, entity_type, width = '350px'):
    return html.Div(
        [html.Div([html.Label(entity_type)] + [html.Div(prop) for prop, score in most_common],
            style={'float':'left'}),
        html.Div([html.Label('Score')] + [html.Div('{:.2f}'.format(score/size)) for prop, score in most_common],
            style={'float':'right'})],)

def get_entities(material):
    db = open_db_connection(db="tri_abstracts", local=False)
    test_ne = db.test_ne
    #parser = SimpleParser()
    #material = parser.matgen_parser(material) #For now comment this out - put back in later
    #print("number of materials is", db.keywords.count())
    entities = list(test_ne.find({'mat': material}))
    num_entities = len(entities)
    if entities is not None:
        #Get the properties
        pro = [doc['PRO'] for doc in entities]
        pro = [p for pp in pro for p in pp if len(p) > 2]
        pro = nltk.FreqDist(pro).most_common(20)

        #Get the phase label
        spl = [doc['SPL'] for doc in entities]
        spl = [p for pp in spl for p in pp if len(p) > 2]
        spl = nltk.FreqDist(spl).most_common(3)

        #Get the synthesis method
        smt = [doc['SMT'] for doc in entities]
        smt = [p for pp in smt for p in pp if len(p) > 2]
        smt = nltk.FreqDist(smt).most_common(5)

        #Get the characterization method
        cmt = [doc['CMT'] for doc in entities]
        cmt = [p for pp in cmt for p in pp if len(p) > 2]
        cmt = nltk.FreqDist(cmt).most_common(10)

        return [
            html.Div([
                html.Div(gen_output(pro, num_entities, 'Property', '350px'), className="four columns"),
                html.Div(gen_output(spl, num_entities, 'Phase', '200px'), className="four columns"),
                html.Div(gen_output(smt, num_entities, 'Synthesis'), className="four columns")],
                    className='row'),
                html.Div([
                    html.Div(gen_output(cmt, num_entities, 'Characterization', '350px'), className="four columns"),
                    html.Div(html.Label('Application (coming soon...)'), className="four columns"),
                    html.Div(html.Label('Sample descriptor (coming soon...)'), className="four columns")],
                    className='row')]

    else:
        return "No keywords for the specified material"

layout = html.Div([
    html.Label('Enter formula for material summary'),
    html.Div("Demo only: search BaTiO3, GaN, or LiFePO4 (other materials won't work!)"),
    html.Div([
        dcc.Input(id='summary-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Search summary', id='summary-button'),
    ]),
    html.Div(style={"padding": "10px"}),
    html.Div("", id='summary-extrated'),
])
