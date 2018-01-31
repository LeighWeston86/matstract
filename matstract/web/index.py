from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from matstract.web import search_app, trends_app, extract_app, similar_app, annotate_app
from matstract.web.app import app, cache

# Header and Intro text
header = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Img(src="https://s3-us-west-1.amazonaws.com/webstract/matstract_with_text.png",
             style={
                 'height': '100px',
                 'float': 'right',
                 'position': 'relative',
                 'bottom': '20px',
                 'left': '10px'
             },
             ),
    html.H2('Matstract db',
            style={
                'position': 'relative',
                'top': '0px',
                'left': '27px',
                'font-family': 'Dosis',
                'display': 'inline',
                'font-size': '6.0rem',
                'color': '#4D637F'
            }),
    html.Nav(
        style={
            'position': 'relative',
            'top': '0px',
            'left': '27px',
            'cursor': 'default'
        },
        children=[
            dcc.Link("Search", href="/search", ),
            html.Span(' • '),
            dcc.Link("Trends", href="/trends"),
            html.Span(' • '),
            dcc.Link("Extract", href="/extract"),
            html.Span(' • '),
            dcc.Link("Similar Abstracts", href="/similar"),
            html.Span(' • '),
            dcc.Link("Similar Abstracts", href="/annotate")
        ],
        id="nav_bar"),
    html.Br()
], className='row twelve columns', style={'position': 'relative', 'right': '15px'})


