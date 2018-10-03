import dash_html_components as html
import dash_core_components as dcc
from matstract.models.cluster_plot import ClusterPlot


cp = ClusterPlot()
plot_data = cp.get_plot_data(entity_type="materials", limit=-1, heatphrase=None, wordphrases=None)

fig_layout = {
    'hovermode': 'closest',
    'showlegend': False,
    'height': 800,
    'xaxis': {
        "autorange": True,
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "ticks": '',
        "showticklabels": False
    },
    'yaxis': {
        "autorange": True,
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "ticks": '',
        "showticklabels": False
    }
}

fig = dict(data=[plot_data], layout=fig_layout)
layout = html.Div([
    html.Div([
        dcc.Input(id='map_keyword',
                  placeholder='e.g. battery',
                  type='text'),
        html.Button(
            'Highlight',
            id='map_highlight_button',
            className="button-search",
            style={"display": "table-cell", "verticalAlign": "top"}),
    ], className="row"),
    dcc.Graph(
        id='material_map',
        figure=fig,
    )]
)
