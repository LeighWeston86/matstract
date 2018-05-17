import dash_html_components as html
import dash_core_components as dcc
from matstract.models.database import AtlasConnection
from matstract.extract.parsing import SimpleParser
from matstract.nlp.theme_extractor import analyze_themes
import pandas as pd
from math import trunc


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
    db = AtlasConnection(db="test").db
    print(db.info)
    parser = SimpleParser()
    material = parser.matgen_parser(material)
    print("number of materials is", db.keywords.count())
    keywords = db.keywords.find_one({'material': material})
    if keywords is not None:
        tf = keywords['keywords_tf']
        tf_arranged = arrange_keywords(tf)
        tfidf = keywords['keywords_tfidf']
        tfidf_arranged = arrange_keywords(tfidf)
        df = pd.DataFrame()
        df['tf'] = tf_arranged
        df['tfidf'] = tfidf_arranged
        return generate_table(df)
    else:
        return "No keywords for the specified material"


def get_themes(text, es, score_cutoff=1000):
    query = {"query": {
        "more_like_this": {
            "fields": ['title', 'abstract'],
            "like": text
        }
    }
    }
    resp = es.search(index="tri_abstracts", body=query, size=100, request_timeout=60)
    themes_and_scores = analyze_themes(resp)

    if len(themes_and_scores):
        i=0
        while themes_and_scores[i][1]>score_cutoff:
            i+=1

        themes = [t[0] for t in themes_and_scores[0:i]]
        scores = [trunc(t[1]*1.1) if t[0] in text else trunc(t[1]) for t in themes_and_scores[0:i]]
        df = pd.DataFrame()
        df['related themes'] = themes
        df['score'] = scores
        return generate_table(df)
    else:
        return "No related themes found. "


def get_themes_in_original(text, es, num_themes=10):
    query = {"query": {
        "more_like_this": {
            "fields": ['title', 'abstract'],
            "like": text
        }
    }
    }
    resp = es.search(index="tri_abstracts", body=query, size=100, request_timeout=60)
    themes_and_scores = analyze_themes(resp)

    themes = []
    scores=[]
    while len(themes) < num_themes and len(themes_and_scores) > 0:
        themescore = themes_and_scores.pop(0)
        if themescore[0] in text:
            themes.append(themescore[0])
            scores.append(themescore[1])
    # themes = [t[0] for t in themes_and_scores]
    # scores = [trunc(t[1]) for t in themes_and_scores]
    df = pd.DataFrame()
    df['related themes'] = themes
    df['score'] = scores
    return generate_table(df)



layout = html.Div([
    html.Label('Enter formula for associated keywords'),
    html.Div([
        dcc.Input(id='keyword-material',
                  placeholder='Material: e.g. "LiFePO4"',
                  type='text'),
        html.Button('Search keywords', id='keyword-button'),
    ]),
    html.Div("", id='keywords-extrated'),
    html.Div(style={"padding": "10px"}),
    html.Label('Or get related themes for an abstract'),
    html.Div(dcc.Textarea(id='themes-textarea',
                          style={"width": "100%"},
                          autoFocus=True,
                          spellCheck=True,
                          wrap=True,
                          placeholder='Paste abstract/other text here to analyze themes.'
                          )),
    html.Div([html.Button('Analyze Themes', id='themes-button'),
              html.Button('Get a random abstract', id='themes-random-abstract')]),
    html.Div("", id='themes-extrated')
])
