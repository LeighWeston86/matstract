from dash.dependencies import Input, Output, State
from matstract.web.view import similar_app
from matstract.models.database import AtlasConnection

db = AtlasConnection().db


def bind(app, cache):
    @app.callback(
        Output('similar-textarea', 'value'),
        # Output('similar-textarea', 'value'),
        [Input("similar-random", 'n_clicks')])
    def get_random(n_clicks):
        if n_clicks is not None:
            text = similar_app.random_abstract()
            return text
        return ""


    @cache.memoize(timeout=600)
    @app.callback(
        Output('similar-table', 'children'),
        # [Input('search-box', 'value')])
        [Input('similar-button', 'n_clicks')],
        [State('similar-textarea', 'value'), State('similar-material-box', 'value')])
    def update_table(n_clicks, search, material):
        if material is not None:
            table = similar_app.generate_table(search, material)
        else:
            table = similar_app.generate_table(search)
        return table


