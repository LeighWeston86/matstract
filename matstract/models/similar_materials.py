import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from matminer.featurizers.composition import *
from matstract.extract.parsing import SimpleParser

class SimilarMaterials:
    def __init__(self):
        #Load the similarity array
        array_url = 'https://s3-us-west-1.amazonaws.com/materialsintelligence/matminer_array.npy'
        ds = np.DataSource()
        ds.open(array_url)
        self.matminer_array = np.load(ds.abspath(array_url))

        #Other data
        mat2index_url = 'https://s3-us-west-1.amazonaws.com/materialsintelligence/mat2index.p'
        index2mat_url = 'https://s3-us-west-1.amazonaws.com/materialsintelligence/index2mat.p'
        scaler_url = 'https://s3-us-west-1.amazonaws.com/materialsintelligence/scaler.p'
        self.mat2index = pickle.load(ds.open(mat2index_url, 'rb'))
        self.index2mat = pickle.load(ds.open(index2mat_url, 'rb'))
        self.scaler = pickle.load(ds.open(scaler_url, 'rb'))

        #Mat parser
        self.parser = SimpleParser()

    def get_mat_vector(self, mat):
        comp = Composition(mat)
        mat_vector = []

        # Add element property features
        ep_feat = ElementProperty.from_preset(preset_name="magpie")
        mat_vector += ep_feat.featurize(comp)

        # Oxidation state features
        comp_ox = comp.add_charges_from_oxi_state_guesses()
        os_feat = OxidationStates()
        mat_vector += os_feat.featurize(comp_ox)

        # Loop over other features
        featurizers = [
            AtomicOrbitals,
            BandCenter,
            Stoichiometry,
            ValenceOrbital,
            ElementFraction,
            TMetalFraction
        ]
        for featurizer in featurizers:
            feat = featurizer()
            mat_vector += feat.featurize(comp)

        mat_vector = np.array([el for el in mat_vector if type(el) != str]).reshape(1, -1)
        mat_vector = self.scaler.transform(mat_vector)

        return mat_vector

    def get_similar_mats(self, mat, num_mats = 10):
        normalized_mat = self.parser.matgen_parser(mat)
        mat_vector = self.get_mat_vector(normalized_mat)
        similarity_scores = cosine_similarity(mat_vector, self.matminer_array).flatten()
        most_similar = list(reversed([self.index2mat[idx] for idx in
                             np.argsort(similarity_scores)]))[:num_mats + 1]
        try:
            most_similar.remove(normalized_mat)
        except ValueError:
            most_similar = most_similar[:-1]
        return most_similar

if __name__ == '__main__':
    sm = SimilarMaterials()
    print(sm.get_similar_mats('LiFePO4'))