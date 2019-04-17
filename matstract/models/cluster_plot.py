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

        ds = np.DataSource()
        # material_names_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/material_map_tsne_words.npy"
        material_coords_url = "https://s3-us-west-1.amazonaws.com/materialsintelligence/final_material_map_atl10_30_ee12_lr200.npy"

        # ds.open(material_names_url)
        ds.open(material_coords_url)

        self.ee = EmbeddingEngine()
        self.embs = self.ee.embeddings / self.ee.norm
        # materials_json = urlopen("https://s3-us-west-1.amazonaws.com/matstract/material_map_10_mentions.json")
        # materials_data = materials_json.read().decode("utf-8")
        # self.materials_tsne_data = json.loads(materials_data)["data"][0]
        # self.norm_matnames = [self.ee.dp.get_norm_formula(m) for m in self.materials_tsne_data["text"]]
        # self.matname2index = dict()
        # for i, label in enumerate(self.norm_matnames):
        #     self.matname2index[label] = i

        self.materials_tsne_data = np.load(ds.abspath(material_coords_url))
        formula_counts = dict()
        for formula in self.ee.formulas_full:
            formula_counts[formula] = 0
            for elem in self.ee.formulas_full[formula]:
                formula_counts[formula] += self.ee.formulas_full[formula][elem]

        mat_counts = sorted(formula_counts.items(), key=lambda x: x[1], reverse=True)
        mat_counts = [mat_count for mat_count in mat_counts if mat_count[1] >= 10]

        self.norm_matnames = [m[0] for m in mat_counts]
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
                if limit == -1:
                    x = self.materials_tsne_data[:, 0]
                    y = self.materials_tsne_data[:, 1]
                else:
                    x = self.materials_tsne_data[:, 0][:limit]
                    y = self.materials_tsne_data[:, 1][:limit]
                labels = self.norm_matnames

            emb_indices = [self.ee.word2index[m] for m in labels]
            # print(emb_indices)

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
                x=x.tolist(),
                y=y.tolist(),
                mode='markers',
                text=[self.ee.most_common_forms[l] for l in labels],
                marker=dict(
                    size=7,
                    color=colors,
                    colorscale='Viridis',
                    showscale=False
                ),
                textposition="top center"
            )
        else:
            # TODO need TSNE for other entity types
            return dict()
