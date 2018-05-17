import dash_html_components as html
import dash_core_components as dcc
from matstract.models.database import AtlasConnection
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


def gen_output(most_common, size, entity_type):
    return html.Div(
        [html.Div([html.Label(entity_type)] + [html.Div(prop) for prop, score in most_common],
            style={'float': 'left'}),
        html.Div([html.Label('Score')] + [html.Div('{:.2f}'.format(score/size)) for prop, score in most_common],
            style={'float': 'right'})], className="summary-float-div")

def get_entities(material):
    #Normalize the material
    parser = SimpleParser()
    material = parser.matgen_parser(material)

    #Open connection and get NEs associated with the material
    db = AtlasConnection(db="test").db
    test_ne = db.test_ne
    dois = db.mats_.find({'unique_mats': material}).distinct('doi')
    entities = list(db.test_ne.find({'doi': {'$in': dois}}))
    num_entities = len(entities)

    #Extract the entities
    if entities is not None:
        pro, spl, smt, cmt = [], [], [], []
        for doc in entities:
            # Get the properties
            pro .append(doc['PRO'])
            #Get the phase label
            spl.append(doc['SPL'])
            #Get the synthesis method
            smt.append(doc['SMT'])
            #Get the characterization method
            cmt.append(doc['CMT'])
        pro = [p for pp in pro for p in pp if len(p) > 2]
        pro = nltk.FreqDist(pro).most_common(20)
        spl = [p for pp in spl for p in pp if len(p) > 2]
        spl = nltk.FreqDist(spl).most_common(3)
        smt = [p for pp in smt for p in pp if len(p) > 2]
        smt = nltk.FreqDist(smt).most_common(5)
        cmt = [p for pp in cmt for p in pp if len(p) > 2]
        cmt = nltk.FreqDist(cmt).most_common(10)

        return html.Div([
            gen_output(pro, num_entities, 'Property'),
            gen_output(cmt, num_entities, 'Characterization'),
            gen_output(smt, num_entities, 'Synthesis'),
            gen_output(spl, num_entities, 'Phase'),
            gen_output([], num_entities, 'Application (coming soon...)'),
            gen_output([], num_entities, 'Sample descriptor (coming soon...)'),
        ])
    else:
        return "No entities for the specified material"

layout = html.Div([
    html.Label('Enter formula for material summary'),
    html.Div("Work in progress... needs more data!!!"),
    html.Div([
        dcc.Input(id='summary-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Search summary', id='summary-button'),
    ]),
    html.Div(style={"padding": "10px"}),
    html.Div("", id='summary-extrated'),
])
