from dash.dependencies import Input, Output, State
from matstract.web.view import keyword_app
from matstract.utils import open_db_connection

db = open_db_connection(local=True)


def bind(app):
    @app.callback(
        Output('extract-keywords', 'children'),
        [Input('keyword-button', 'n_clicks')],
        [State('keyword-material', 'value')])
    def keywords_table(n_clicks, text):
        if text is not None and text != '':
            return keyword_app.get_keywords(text)
        else:
            return ""


# def highlight_extracted(n_clicks, text):
#    if n_clicks is not None:
#        results = [html.Div(word) for word in keyword_extraction.extract_keywords(text)]
#        return results
#    else:
#        return []