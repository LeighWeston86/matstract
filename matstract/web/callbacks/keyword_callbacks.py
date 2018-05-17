from dash.dependencies import Input, Output, State
from matstract.web.view import keyword_app
from matstract.models.database import AtlasConnection, ElasticConnection
from matstract.web.view.similar_app import random_abstract

db = AtlasConnection().db
es = ElasticConnection()


def bind(app):
    @app.callback(
        Output('keywords-extrated', 'children'),
        [Input('keyword-button', 'n_clicks')],
        [State('keyword-material', 'value')])
    def keywords_table(n_clicks, text):
        if text is not None and text != '':
            return keyword_app.get_keywords(text)
        else:
            return ""

    @app.callback(
        Output('themes-textarea', 'value'),
        [Input('themes-random-abstract', 'n_clicks')])
    def fill_random(n_clicks):
        print("filling random")
        return random_abstract()

    @app.callback(
        Output('themes-extrated', 'children'),
        [Input('themes-button', 'n_clicks')],
        [State('themes-textarea', 'value')])
    def themes(n_clicks, text):
        if text is not None and text != '':
            return keyword_app.get_themes(text, es)
        else:
            return ""


# def highlight_extracted(n_clicks, text):
#    if n_clicks is not None:
#        results = [html.Div(word) for word in keyword_extraction.extract_keywords(text)]
#        return results
#    else:
#        return []
