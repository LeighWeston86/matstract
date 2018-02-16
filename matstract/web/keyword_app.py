import dash_html_components as html
import dash_core_components as dcc


def keyword_list(kw_array):
    key_words = [html.P(word) for word in kw_array]
    return key_words


layout = html.Div([
    html.Label('Enter formula for associated keywords'),
    html.Div([
        dcc.Input(id='keyword-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Search keywords', id='keyword-button'),
    ]),
    html.Div(id='extract-keywords')
])