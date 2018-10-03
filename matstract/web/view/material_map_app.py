import dash_html_components as html
import dash_core_components as dcc
from matstract.models.cluster_plot import ClusterPlot


cp = ClusterPlot()
plot_data = cp.get_plot_data(entity_type="materials", limit=-1, heatphrase=None, wordphrases=None)

# ee = EmbeddingEngine()
# embs = ee.embeddings / ee.norm
# # ds = np.DataSource()
#
# # # loading tsne matrix
# # tsne_matrix_url = "https://s3-us-west-1.amazonaws.com/matstract/material_map_tsne_5.npy"
# # ds.open(tsne_matrix_url)
# # tsne_matrix = np.load(ds.abspath(tsne_matrix_url))
#
# ds = np.DataSource()
# material_names_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/material_map_tsne_words.npy"
# material_coords_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/final_material_map_atl10_30_ee12_lr200.npy"
#
# ds.open(material_names_url)
# material_names = np.load(ds.abspath(material_names_url))
# ds.open(material_coords_url)
# material_coords = np.load(ds.abspath(material_coords_url))

# material_names = np.load(data_root+"/data/material_map_tsne_words.npy").item()
# material_map_tsne = np.load(data_root+"data/final_material_map_atl10_30_ee12_lr200.npy")



# response = urlopen("https://s3-us-west-1.amazonaws.com/matstract/material_map_10_mentions.json")
# data = response.read().decode("utf-8")
# tsne_data = json.loads(data)["data"][0]
# x = tsne_data["x"]
# y = tsne_data["y"]
# formulas = tsne_data["text"]
# formula_emb_indices = [ee.word2index[ee.dp.get_norm_formula(f)] for f in formulas]

# x = material_coords[:, 0]
# y = material_coords[:, 1]
# formulas = material_names.item()
# formula_emb_indices = [ee.word2index[f] if f in ee.word2index else None for f in formulas]

# formula_counts = [0] * len(ee.formulas_full)
# for i, formula in enumerate(ee.formulas_full):
#     for writing in ee.formulas_full[formula]:
#         formula_counts[i] += ee.formulas_full[formula][writing]
# min_count = 5
#
# formula_indices, formula_to_plot, formula_emb_indices, most_common_forms = [], [], [], []
# for i, f in enumerate(ee.formulas_full):
#     if formula_counts[i] >= min_count:
#         formula_indices.append(i)
#         formula_to_plot.append(f)
#         formula_emb_indices.append(ee.word2index[f])
#         if f in ee.dp.ELEMENTS:
#             most_common_forms.append(f)
#         else:
#             most_common_forms.append(max(ee.formulas_full[f].items(), key=operator.itemgetter(1))[0])

# x = tsne_matrix[formula_indices, 0]
# y = tsne_matrix[formula_indices, 1]

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

# data = [go.Scatter(
#     y=plot_data["y"],
#     x=plot_data["x"],
#     mode='markers',
#     text=plot_data["text"],
#     marker=dict(
#         size=5,
#         colorscale='BuPu',
#         showscale=False
#     ),
#     textposition="top"
# )]
# data = go.Scatter(plot_data)
# print(data)

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
