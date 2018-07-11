from dash.dependencies import Input, Output, State
import numpy as np
from matstract.web.view.material_map_app import ee, embs, fig, x, y, formulas, formula_emb_indices
import plotly.graph_objs as go


def bind(app):
    # updates similar words
    @app.callback(
        Output('material_map', 'figure'),
        [Input('map_highlight_button', 'n_clicks')],
        [State('map_keyword', 'value')])
    def highlight_map(_, keywords):
        if keywords is not None and keywords != "":
            # the positive word vectors
            sentence = ee.phraser[ee.dp.process_sentence(keywords.split())[0]]

            avg_embedding = np.zeros(200)
            nr_words = 0
            for word in sentence:
                if word in ee.word2index:
                    avg_embedding += embs[ee.word2index[word]]
                    nr_words += 1
            avg_embedding = avg_embedding / nr_words

            similarities = np.dot(avg_embedding, embs[formula_emb_indices, :].T)

            fig["data"] = [go.Scatter(
                y=y,
                x=x,
                mode='markers',
                text=formulas,
                marker=dict(
                    size=5,
                    color=similarities.ravel(),
                    colorscale='Viridis',
                    showscale=False
                ),
                textposition="top"
            )]
            return fig

