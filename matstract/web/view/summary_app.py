import dash_html_components as html
import dash_core_components as dcc
from matstract.models.database import AtlasConnection
from matstract.extract.parsing import SimpleParser
import os
import pickle, _pickle
from matstract.nlp.theme_extractor import analyze_themes
from matstract.web.view import trends_app
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


def gen_output(most_common, size, entity_type, material, class_name="four columns"):
    # print([(prop, score) for prop, score in most_common])
    table = html.Table(
        [html.Tr([html.Th(entity_type), html.Th("score", style={"textAlign": "right", "fontWeight": "normal"})], className="summary-header")] +
        [html.Tr([
            html.Td(html.A(prop, href="/search/{}/{}".format(prop, material))),
            html.Td('{:.2f}'.format(score / size), style={"textAlign": "right"})]) for prop, score in most_common],
        className="summary-table")
    return html.Div(table, className="summary-div " + class_name)


def get_entities(mat, class_name="three columns"):
    # Normalize the material
    parser = SimpleParser()
    material = parser.matgen_parser(mat)

    # Open connection and get NEs associated with the material
    db = AtlasConnection(db="test").db
    dois = db.mats_.find({'unique_mats': material}).distinct('doi')
    print(dois)
    entities = list(db.ne.find({'doi': {'$in': dois}}))
    print(entities)
    num_entities = len(entities)

    # Extract the entities
    if entities is not None:
        apl, pro, spl, smt, cmt, dsc = [], [], [], [], [], []
        for doc in entities:
            # Get the properties
            pro.append(doc['PRO'])
            # Get the application
            apl.append(doc['APL'])
            spl.append(doc['SPL'])
            # Get the synthesis method
            smt.append(doc['SMT'])
            # Get the characterization method
            cmt.append(doc['CMT'])
            # Get the characterization method
            dsc.append(doc['DSC'])

        pro = [pro_dict[p] for pp in pro for p in pp if len(p) > 2 and p in pro_dict.keys()]
        pro = nltk.FreqDist(pro).most_common(20)
        apl = [apl_dict[p] for pp in apl for p in pp if len(p) > 2 and p in apl_dict.keys()]
        apl = nltk.FreqDist(apl).most_common(12)
        print(apl)
        apl = [(a, score) for a, score in apl if a not in ['coating', 'electrode']]
        print(apl)
        spl = [p for pp in spl for p in pp if len(p) > 2]
        spl = nltk.FreqDist(spl).most_common(3)
        smt = [smt_dict[p] for pp in smt for p in pp if len(p) > 2 and p in smt_dict.keys()]
        smt = nltk.FreqDist(smt).most_common(10)
        cmt = [cmt_dict[p] for pp in cmt for p in pp if len(p) > 2 and p in cmt_dict.keys()]
        cmt = nltk.FreqDist(cmt).most_common(10)
        dsc = [dsc_dict[p] for pp in dsc for p in pp if len(p) > 2 and p in dsc_dict.keys()]
        dsc = nltk.FreqDist(dsc).most_common(10)

        return html.Div([
            html.Div([
                html.Div(trends_app.display_trends_graph(material), className="six columns"),
                gen_output(pro, num_entities, 'Property', material, class_name),
                gen_output(apl, num_entities, 'Application', material, class_name)], className="row"),
            html.Div([
                gen_output(cmt, num_entities, 'Characterization', material, class_name),
                gen_output(smt, num_entities, 'Synthesis', material, class_name),
                gen_output(dsc, num_entities, 'Sample descriptor', material, class_name),
                gen_output(spl, num_entities, 'Phase', material, class_name)], className="row"),
        ])
    else:
        return "No entities for the specified material"


layout = html.Div([
    html.Div([
        dcc.Input(id='summary-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button(
            'Get Summary',
            id='summary-button',
            className="button-search",
            style={"display": "table-cell", "verticalAlign": "top"}),
    ]),
    html.Div(style={"padding": "10px"}),
    html.Div("", id='summary-extrated'),
])
