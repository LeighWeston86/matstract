from urllib.request import urlopen
import json
from matstract.models.word_embeddings import EmbeddingEngine
import numpy as np


class ClusterPlot:
    def __init__(self):
        """
        The constructor for the Cluster Plot object
        :param entity_type: 'all' or 'materials'
        :param limit: number of most common entities to plot
        :param heatphrase: color according to similarity to this phrase
        :param wordphrases: filter to show only the specified phrases
        """
        self.ee = EmbeddingEngine()
        self.embs = self.ee.embeddings / self.ee.norm
        materials_json = urlopen("https://s3-us-west-1.amazonaws.com/matstract/material_map_10_mentions.json")
        materials_data = materials_json.read().decode("utf-8")
        self.materials_tsne_data = json.loads(materials_data)["data"][0]
        self.norm_matnames = [self.ee.dp.get_norm_formula(m) for m in self.materials_tsne_data["text"]]
        self.matname2index = dict()
        for i, label in enumerate(self.norm_matnames):
            self.matname2index[label] = i

    def get_plot_data(self, entity_type, limit, heatphrase, wordphrases):
        if entity_type == "materials":
            if wordphrases:  # only display the specified materials
                labels = []
                normal_wordphrases = []
                for wp in wordphrases:
                    normal_wp = self.ee.dp.get_norm_formula(wp)
                    normal_wordphrases.append(normal_wp)
                    if normal_wp in self.norm_matnames:
                        labels.append(wp)
                wp_indices = [self.matname2index[mn] for mn in normal_wordphrases if mn in self.matname2index]
                x = [self.materials_tsne_data["x"][i] for i in wp_indices[:limit]]
                y = [self.materials_tsne_data["y"][i] for i in wp_indices[:limit]]
                labels = labels[:limit]
            else:
                x = self.materials_tsne_data["x"][:limit]
                y = self.materials_tsne_data["y"][:limit]
                labels = self.materials_tsne_data["text"][:limit]

            emb_indices = [self.ee.word2index[self.ee.dp.get_norm_formula(m)] for m in labels]

            # calculating the colors
            if heatphrase is not None and heatphrase != "":
                # the positive word vectors
                sentence = self.ee.phraser[self.ee.dp.process_sentence(heatphrase.split())[0]]

                avg_embedding = np.zeros(200)
                nr_words = 0
                for word in sentence:
                    if word in self.ee.word2index:
                        avg_embedding += self.embs[self.ee.word2index[word]]
                        nr_words += 1
                if nr_words > 0:
                    avg_embedding = avg_embedding / nr_words
                    colors = np.dot(avg_embedding, self.embs[emb_indices, :].T).ravel().tolist()
                else:
                    colors = [0] * len(emb_indices)
            else:
                colors = [0] * len(emb_indices)

            return dict(
                x=x,
                y=y,
                mode='markers',
                text=labels,
                marker=dict(
                    size=5,
                    color=colors,
                    colorscale='Viridis',
                    showscale=False
                ),
                textposition="top center"
            )
        else:
            # TODO need TSNE for other entity types
            return dict()
