import dash_html_components as html
import dash_core_components as dcc
from matstract.models.database import AtlasConnection
from matstract.extract.parsing import SimpleParser
import os
import pickle, _pickle
from matstract.nlp.theme_extractor import analyze_themes
import pandas as pd
from math import trunc
import nltk

# load in the entity dictionaries
cmt_location = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../../nlp/cmt_dict.p')
with open(cmt_location, 'rb') as f:
    cmt_dict = _pickle.load(f)

smt_location = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../../nlp/smt_dict.p')
with open(smt_location, 'rb') as f:
    smt_dict = _pickle.load(f)

pro_location = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../../nlp/pro_dict.p')
with open(pro_location, 'rb') as f:
    pro_dict = _pickle.load(f)

apl_location = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../../nlp/apl_dict.p')
with open(apl_location, 'rb') as f:
    apl_dict = _pickle.load(f)

dsc_location = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '../../nlp/dsc_dict.p')
with open(dsc_location, 'rb') as f:
    dsc_dict = _pickle.load(f)



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
    dois = db.mats_.find({'unique_mats': material}).distinct('doi')
    entities = list(db.ne.find({'doi': {'$in': dois}}))
    num_entities = len(entities)

    #Extract the entities
    if entities is not None:
        apl, pro, spl, smt, cmt, dsc = [], [], [], [], [], []
        for doc in entities:
            # Get the properties
            pro.append(doc['PRO'])
            # Get the application
            apl.append(doc['APL'])
            #Get the phase label
            spl.append(doc['SPL'])
            #Get the synthesis method
            smt.append(doc['SMT'])
            #Get the characterization method
            cmt.append(doc['CMT'])
            # Get the characterization method
            dsc.append(doc['DSC'])

        pro = [pro_dict[p] for pp in pro for p in pp if len(p) > 2 and p in pro_dict.keys()]
        pro = nltk.FreqDist(pro).most_common(20)
        apl = [apl_dict[p] for pp in apl for p in pp if len(p) > 2 and p in apl_dict.keys()]
        apl = nltk.FreqDist(apl).most_common(10)
        spl = [p for pp in spl for p in pp if len(p) > 2]
        spl = nltk.FreqDist(spl).most_common(3)
        smt = [smt_dict[p] for pp in smt for p in pp if len(p) > 2 and p in smt_dict.keys()]
        smt = nltk.FreqDist(smt).most_common(10)
        cmt = [cmt_dict[p] for pp in cmt for p in pp if len(p) > 2 and p in cmt_dict.keys()]
        cmt = nltk.FreqDist(cmt).most_common(10)
        dsc = [dsc_dict[p] for pp in dsc for p in pp if len(p) > 2 and p in dsc_dict.keys()]
        dsc = nltk.FreqDist(dsc).most_common(10)

        return html.Div([
            gen_output(pro, num_entities, 'Property'),
            gen_output(apl, num_entities, 'Application'),
            gen_output(cmt, num_entities, 'Characterization'),
            gen_output(smt, num_entities, 'Synthesis'),
            gen_output(spl, num_entities, 'Phase'),
            gen_output(dsc, num_entities, 'Sample descriptor'),
        ])
    else:
        return "No entities for the specified material"

#def get_topics(material):
#    docs = [doc['abstract'] for doc in get_search_results(material)]


layout = html.Div([
    html.Label('Enter formula for material summary'),
    #html.Div("Work in progress... needs more data!!!"),
    html.Div([
        dcc.Input(id='summary-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Search summary', id='summary-button'),
    ]),
    html.Div(style={"padding": "10px"}),
    html.Div("", id='summary-extrated'),
])
