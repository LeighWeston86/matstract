from dash.dependencies import Input, Output, State
from matstract.web.view.search_app import generate_table
from matstract.models.search import MatstractSearch


def bind(app):
    @app.callback(
        Output('search_results', 'children'),
        [Input('search_btn', 'n_clicks')],
        [State('search_filters', 'value'),
         State('search_input', 'value')])
    def show_filters(n_clicks, filter_val, text_val):
        if n_clicks is not None:
            text = text_val if text_val is not None else None
            filter_vals = [val["value"] for val in filter_val] if filter_val else None
            if text or filter_vals:
                valid_filters = []
                if filter_vals:
                    for filter_str in filter_vals:
                        split_filter = filter_str.split(":")
                        if len(split_filter) != 2:
                            pass  # invalid filter
                        else:
                            if split_filter[0].strip().lower() in MatstractSearch.FILTER_DICT:
                                valid_filters.append(
                                    (split_filter[0].strip().lower(),
                                     split_filter[1].strip())
                                )
                materials = []
                for m_filter in valid_filters:
                    if m_filter[0] == "material":
                        materials.append(m_filter[1])
                print("Search Text: {}".format(text))
                print("Valid filters: ", valid_filters)
                return generate_table(search=text, filters=valid_filters)
            else:
                return ""
        return ""
