from dash.dependencies import Input, Output, State
from matstract.web.view import extract_app
from matstract.utils import open_db_connection
from matstract.extract.parsing import extract_materials, materials_extract

db = open_db_connection(local=True, db="matstract_db")


def bind(app):
    ### Extract App Callbacks ###
    @app.callback(
        Output('extract-results', 'value'),
        [Input('extract-button', 'n_clicks')],
        [State('extract-textarea', 'value')])
    def update_extract(n_clicks, text):
        if n_clicks is not None:
            if text is None:
                text = ''
            materials = extract_materials(text)
            materials = [m for m in materials if len(m) > 0]
            # return [{"name": m, "value": m} for m in materials]
            return ", ".join(materials)
        return ""

    @app.callback(
        Output('extract-highlighted', 'children'),
        [Input('extract-button', 'n_clicks')],
        [State('extract-textarea', 'value')])
    def highlight_extracted(n_clicks, text):
        if n_clicks is not None:
            parsed, missed = materials_extract(text)
            highlighted = extract_app.highlighter(text, parsed, missed)
            return highlighted
        return ""

    @app.callback(
        Output('highlight-random', 'children'),
        [Input('random-abstract', 'n_clicks')])
    def highlight_random(n_clicks):
        if n_clicks is not None:
            text = extract_app.random_abstract()
            parsed, missed = materials_extract(text)
            highlighted = extract_app.highlighter(text, parsed, missed)
            return highlighted
        return ""