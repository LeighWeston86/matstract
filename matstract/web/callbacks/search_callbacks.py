from dash.dependencies import Input, Output, State
from matstract.web.view import search_app


def bind(app, cache):
    @cache.memoize(timeout=600)
    @app.callback(
        Output('table-element', 'children'),
        # [Input('search-box', 'value')])
        [Input('search-button', 'n_clicks')],
        [State('search-box', 'value'), State('material-box', 'value')])
    def update_table(n_clicks, search, material):
        if material is not None:
            table = search_app.generate_table(search, material)
        else:
            table = search_app.generate_table(search)
        return table

    @cache.memoize(timeout=600)
    @app.callback(
        Output('number_results', 'children'),
        [Input('search-button', 'n_clicks')],
        [State('search-box', 'value'), State('material-box', 'value')])
    def update_num_results_label(n_clicks, search, material):
        results = search_app.get_search_results(search, material)
        if material or search:
            n = len(results)
            if n == 0:
                return "No Results"
            elif n == 1000:
                return 'Showing {} of >{:,} results'.format(100, n)
            else:
                return 'Showing {} of {:,} results'.format(min(100, n), n)
        else:
            return ''
