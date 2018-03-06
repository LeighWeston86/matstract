import dash_html_components as html
import dash_core_components as dcc
import random
from matstract.utils import open_db_connection

def highlight_multiple(text, materials, color = 'Yellow'):
    for mat in materials:
        text = text.replace(mat, "<s>html.Mark('{}')<s>".format(mat))
    split = text.split('<s>')
    for (idx, token) in enumerate(split):
        try:
            split[idx] = eval(token)
            split[idx].style = {'background-color': color}
        except:
            pass

    return split


def highlighter(text, parsed, missed):
    # sort both lists in order of increasing length
    # combine
    parsed = sorted(parsed, key=len, reverse=True)
    parsed = [(w, 'parsed') for w in parsed]
    missed = sorted(missed, key=len, reverse=True)
    missed = [(w, 'missed') for w in missed]
    chems = parsed + missed

    txt = [text]
    for (chem, key) in chems:
        tag_all = []
        for token in txt:
            if type(token) == str:
                color = 'Cyan' if key == 'parsed' else 'Orange'
                tag_all += highlight_multiple(token, [chem], color)
            else:
                tag_all.append(token)
        txt = tag_all

    return txt

def random_abstract():
    db = open_db_connection()
    count = db.abstracts_leigh.count()
    random_document = db.abstracts_leigh.find()[random.randrange(count)]
    return random_document['abstract']

# The Extract App
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Matstract Extract: materials extraction from text sources.')
        ], style={'margin-left': '10px'}),
        html.Label('Enter text for materials extraction:'),
        html.Div(dcc.Textarea(id='extract-textarea',
                     style={"width": "100%"},
                     autoFocus=True,
                     spellCheck=True,
                     wrap=True,
                     placeholder='Paste abstract/other text here to extract materials mentions.'
                     )),
        html.Div([html.Button('Extract Materials', id='extract-button'),
                  html.Button('Choose a random abstract', id = 'random-abstract')]),
        # dcc.Dropdown(id='extract-dropdown',
        #              multi=True,
        #              placeholder='Material: e.g. "LiFePO4"',
        #              # options=[{'label': i, 'value': i} for i in df['NAME'].tolist()]),
        #              ),
        dcc.Textarea(id='extract-results',
                     style={"width": "100%"},
                     autoFocus=False,
                     wrap=True,
                     value="",
                     readOnly=True,
                     ),
        html.Div(id='extract-highlighted'
        ),
        html.Div(id='highlight-random'
        ),
        # dcc.Input(id='trends-material-box',
        #           placeholder='Material: e.g. "LiFePO4"',
        #           value='',
        #           type='text'),
        # dcc.Input(id='trends-search-box',
        #           placeholder='optional search criteria',
        #           type='text'),
        # html.Button('Submit', id='trends-button'),
        # dcc.Graph(id='trends', figure={}),
    ], className='twelve columns'),
])
