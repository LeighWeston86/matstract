import dash_html_components as html
import dash_core_components as dcc
import operator
from matstract.models.search import MatstractSearch
import plotly.graph_objs as go


def generate_trends_graph(search=None, material=None, layout=None):
    MS = MatstractSearch()
    results = list(MS.search(search, material, max_results=10000))
    hist = dict()
    if len(results) > 0:
        histdata = {}
        years = [int(r["year"]) for r in results]
        for year in years:
            if year in histdata.keys():
                histdata[year] += 1
            else:
                histdata[year] = 1
        for year in range(min(2000, min(histdata.keys())), 2017):
            if not year in histdata.keys():
                histdata[year] = 0
        histdata = sorted(histdata.items(), key=operator.itemgetter(0))
        hist["data"] = [{
            'x': [x[0] for x in histdata],
            'y': [x[1] for x in histdata]}]
    else:
        hist["data"] = [{'x': [], 'y': []}]
    if layout is not None:
        hist["layout"] = layout
    return hist


figure = {"data": [{
                'x': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
                          2011, 2012, 2013, 2014, 2015, 2016, 2017],
                'y': [0, 0, 1, 0, 1, 0, 0, 5, 5, 20, 76, 182, 381, 785, 724, 847, 672, 596]}]}

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


