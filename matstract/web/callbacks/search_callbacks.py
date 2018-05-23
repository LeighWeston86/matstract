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

    @cache.memoize(timeout=600)
    @app.callback(
        Output('search-button', 'n_clicks'),
        [Input('linked_search_box', 'value')],
        [State('search-button', 'n_clicks'),
         State('search-box', 'value'),
         State('material-box', 'value')])
    def update_search_box(linked_search, n_clicks, search_text, materials):
        print("performing update")
        if n_clicks is not None and linked_search is not None:
            return n_clicks+1
        if n_clicks is None and linked_search is None:
            return None
        return 1

    @cache.memoize(timeout=600)
    @app.callback(
        Output('search-box', 'value'),
        [Input('linked_search_box', 'value')])
    def update_search_box(linked_search):
        print("filling search", linked_search)
        if linked_search:
            items = linked_search.split("/")
            return items[0]
        else:
            return None

    @cache.memoize(timeout=600)
    @app.callback(
        Output('material-box', 'value'),
        [Input('linked_search_box', 'value')])
    def update_material_box(linked_search):
        print("filling materials", linked_search)
        if linked_search:
            items = linked_search.split("/")
            return items[1]
        else:
            return None