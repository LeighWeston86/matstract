from dash.dependencies import Input, Output, State
from matstract.web.view import summary_app


def bind(app):
    @app.callback(
        Output('summary-extrated', 'children'),
        [Input('summary-button', 'n_clicks')],
        [State('summary-material', 'value')])
    def summary_table(n_clicks, text):
        if text is not None and text != '':
            return summary_app.get_entities(text)
        else:
            return ""
