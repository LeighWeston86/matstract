from dash.dependencies import Input, Output, State
from matstract.web.view.material_map_app import fig
from matstract.models.cluster_plot import ClusterPlot


def bind(app):
    cp = ClusterPlot()

    # updates similar words
    @app.callback(
        Output('material_map', 'figure'),
        [Input('map_highlight_button', 'n_clicks')],
        [State('map_keyword', 'value')])
    def highlight_map(_, keywords):
        plot_data = cp.get_plot_data(
            entity_type="materials",
            limit=-1,
            heatphrase=keywords,
            wordphrases=None)
        fig["data"] = plot_data
        return fig

