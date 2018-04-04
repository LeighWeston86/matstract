from dash.dependencies import Input, Output, State
import dash_html_components as html
from matstract.web.view import extract_app
from matstract.utils import open_db_connection

db = open_db_connection(local=True, db="matstract_db")


def bind(app):
    ### Extract App Callbacks ###
    @app.callback(
        Output('extract-highlighted', 'children'),
        [Input('extract-button', 'n_clicks')],
        [State('extract-textarea', 'value')])
    def highlight_extracted(n_clicks, text):
        if n_clicks is not None:
            text, tags = extract_app.extract_ne(text)
            spaced_tags = []
            for tag in tags:
                #spaced_tags += [tag, html.Span()]
                span = html.Span(tag)
                span.style = {'padding-right': '15px' }
                spaced_tags.append(span)
            return html.Div(text), html.Br(), html.Div(html.Label('Extracted Entity tags:')), html.Div(spaced_tags)

    @app.callback(
        Output('extract-textarea', 'value'),
        # Output('similar-textarea', 'value'),
        [Input("extract-random", 'n_clicks')])
    def get_random(n_clicks):
        if n_clicks is not None:
            text = extract_app.random_abstract()
            return text
        return ""