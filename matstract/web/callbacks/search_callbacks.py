from dash.dependencies import Input, Output, State
from matstract.web.view import search_app


def bind(app, cache):
    @cache.memoize(timeout=600)
    @app.callback(
        Output('search_results', 'children'),
        [Input('search-button', 'n_clicks')],
        [State('search-box', 'value'), State('material-box', 'value')])
    def update_table(n_clicks, search, material):
        if n_clicks is not None:
            # convert empty strings to None
            material = None if material == "" else material
            search = None if search == "" else search
            return search_app.generate_table(search, material)
        return ""

