import dash_html_components as html
import dash_core_components as dcc


# The Extract App
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Matstract Extract: named entity extraction from text sources.')
        ], style={'margin-left': '10px'}),
        html.Label('Enter text for named entity extraction:'),
        html.Div(dcc.Textarea(id='extract-textarea',
                     style={"width": "100%"},
                     autoFocus=True,
                     spellCheck=True,
                     wrap=True,
                     placeholder='Paste abstract/other text here to extract named entity mentions.'
                     )),
        html.Div([html.Button('Extract Entities', id='extract-button'),
                  html.Button('Choose a random abstract', id = 'extract-random')]),
        html.Div(id='extract-highlighted'
        ),
        #html.Div(html.Label('Extracted:')),
        html.Div(id='extracted')
    ], className='twelve columns'),
])