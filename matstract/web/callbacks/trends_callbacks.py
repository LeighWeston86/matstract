from dash.dependencies import Input, Output, State
from matstract.web.view import trends_app
from matstract.models.database import AtlasConnection

db = AtlasConnection().db

def bind(app, cache):
    @cache.memoize(timeout=600)
    @app.callback(
        Output('graph-label', 'children'),
        [Input('trends-button', 'n_clicks')],
        [State('trends-material-box', 'value'), State('trends-search-box', 'value')])
    def update_title(n_clicks, material, search):
        if n_clicks is not None:
            if material is None:
                material = ''
            if search is None:
                search = ''
            if len(search) == 0:
                return "Number of papers mentioning {} per year:".format(material)
            else:
                if len(material) > 0:
                    return "Number of papers related to '{}' mentioning {} per year:".format(search, material)
            return ''
        else:
            return "Number of papers mentioning {} per year:".format("graphene")

    @cache.memoize(timeout=600)
    @app.callback(
        Output('trend', 'figure'),
        [Input('trends-button', 'n_clicks')],
        [State('trends-material-box', 'value'),
         State('trends-search-box', 'value'),
         State('trend', 'figure')])
    def update_graph(n_clicks, material, search, current_figure):
        if n_clicks is not None:
            figure = trends_app.generate_trends_graph(search=search, material=material)
            figure["mode"] = "histogram"
            return figure
        else:
            return current_figure
