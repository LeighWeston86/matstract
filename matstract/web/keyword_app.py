import dash_html_components as html
import dash_core_components as dcc
from matstract.utils import open_db_connection
from matstract.extract.parsing import SimpleParser
import pandas as pd

db = open_db_connection()

def arrange_keywords(kwds):
    unigrams = [unigram for unigram, count in kwds['unigrams']]
    bigrams = [' '.join(bigram) for bigram, count in kwds['bigrams']]
    trigrams = [' '.join(trigram) for trigram, count in kwds['trigrams']]
    return unigrams + bigrams + trigrams

def generate_table(dataframe, max_rows=100):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def get_keywords(material):
    db = open_db_connection()
    parser = SimpleParser()
    material = parser.matgen_parser(material)
    tf = db.keywords.find_one({ 'material' : material })['keywords_tf']
    tf_arranged = arrange_keywords(tf)
    tfidf = db.keywords.find_one({ 'material' : material })['keywords_tfidf']
    tfidf_arranged = arrange_keywords(tfidf)
    df = pd.DataFrame()
    df['tf'] = tf_arranged
    df['tfidf'] = tfidf_arranged
    return generate_table(df)

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