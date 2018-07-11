import dash_html_components as html
import dash_core_components as dcc
import operator
import numpy as np

from matstract.models.word_embeddings import EmbeddingEngine
import plotly.graph_objs as go

ee = EmbeddingEngine()
embs = ee.embeddings / ee.norm
ds = np.DataSource()

# loading tsne matrix
tsne_matrix_url = "https://s3-us-west-1.amazonaws.com/matstract/material_map_tsne_5.npy"
ds.open(tsne_matrix_url)
tsne_matrix = np.load(ds.abspath(tsne_matrix_url))

formula_counts = [0] * len(ee.formulas_full)
for i, formula in enumerate(ee.formulas_full):
    for writing in ee.formulas_full[formula]:
        formula_counts[i] += ee.formulas_full[formula][writing]
min_count = 5

formula_indices, formula_to_plot, formula_emb_indices, most_common_forms = [], [], [], []
for i, f in enumerate(ee.formulas_full):
    if formula_counts[i] >= min_count:
        formula_indices.append(i)
        formula_to_plot.append(f)
        formula_emb_indices.append(ee.word2index[f])
        if f in ee.dp.ELEMENTS:
            most_common_forms.append(f)
        else:
            most_common_forms.append(max(ee.formulas_full[f].items(), key=operator.itemgetter(1))[0])

x = tsne_matrix[formula_indices, 0]
y = tsne_matrix[formula_indices, 1]

layout = {
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

data = [go.Scatter(
    y=y,
    x=x,
    mode='markers',
    text=most_common_forms,
    marker=dict(
        size=5,
        colorscale='Viridis',
        showscale=False
    ),
    textposition="top"
)]
fig=dict(data=data)
fig["layout"] = layout

graph = dcc.Graph(
        id='material_map',
        figure=fig,
    )

layout = html.Div([
    html.Div([
        dcc.Input(id='map_keyword',
                  placeholder='e.g. perovskite',
                  type='text'),
        html.Button(
            'Highlight',
            id='map_highlight_button',
            className="button-search",
            style={"display": "table-cell", "verticalAlign": "top"}),
    ], className="row"),
    graph]
)
