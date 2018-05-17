import dash_html_components as html
import dash_core_components as dcc
import operator
from matstract.models.search import MatstractSearch


def generate_trends_graph(search='', materials=''):
    MS = MatstractSearch()

    if search is None:
        search = ''
    if materials is None:
        materials = ''
    if len(search) and not len(materials):
        results = MS.text_search(search)
    else:
        ids = MS.text_search(search)
        method = "exclusive" if materials[0]!= "-" else "inclusive"
        results = MS.filter_by_material(ids, materials=materials, method=method)

    if len(results) > 0:
        histdata = {}
        years = [r["year"] for r in results]
        for year in years:
            if year in histdata.keys():
                histdata[year] += 1
            else:
                histdata[year] = 1
        for year in range(min(2000, min(histdata.keys())), max(histdata.keys())):
            if not year in histdata.keys():
                histdata[year] = 0
        histdata = sorted(histdata.items(), key=operator.itemgetter(0))
        hist = {
            'data': [
                {
                    'x': [x[0] for x in histdata],
                    'y': [x[1] for x in histdata],
                    'name': 'Hist 1',
                    'type': 'scatter',
                    'marker': {'size': 12}
                }]}
    else:
        hist = {
            'data': [
                {
                    'x': [],
                    'y': [],
                    'name': 'Hist 1',
                    'type': 'scatter',
                    'marker': {'size': 12}
                }]}
    return hist
#
figure = {'data': [{'x': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
                          2011, 2012, 2013, 2014, 2015, 2016, 2017],
                    'y': [0, 0, 1, 0, 1, 0, 0, 5, 5, 20, 76, 182, 381, 785, 724, 847, 672, 596],
                    'name': 'Hist 1', 'type': 'scatter', 'marker': {'size': 12}}]}

# The Trends app
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Matstract Trends: materials mentions over time.')
        ], style={'margin-left': '10px'}),
        dcc.Input(id='trends-material-box',
                  placeholder='Material: e.g. "graphene"',
                  value='',
                  type='text'),
        dcc.Input(id='trends-search-box',
                  placeholder='Topic/appication',
                  type='text'),
        html.Button('Submit', id='trends-button'),
        html.Div([
            html.Label(id="graph-label"),
            dcc.Graph(id='trend', figure=figure)]),
    ], className='twelve columns'),
])


