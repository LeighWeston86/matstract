import unittest
import numpy as np
from matstract.nlp.annotation_metrics import AnnotationMetrics
from numpy.testing import assert_almost_equal


class TestAnnotationMetrics(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        """Creates the datasets for testing"""
        super(TestAnnotationMetrics, self).__init__(*args, **kwargs)
        self.am = AnnotationMetrics()

        self.all_pairs = []
        self.all_answers = []

        # the most basic example with perfect accuracies and similarity
        pairs1 = list()
        pairs1.append({
            "common_labels": {'CHM', 'DSC', 'MAT'},
            "ann_list": [['DSC', 'MAT', 'MAT'], ['DSC', 'MAT', 'MAT']],

        })
        pairs1.append({
            "common_labels": {'PRO', 'PVL', 'PUT', 'None'},
            "ann_list": [['None', 'None', 'PUT'], ['None', 'None', 'PUT']],

        })
        pairs1.append({
            "common_labels": {'MAT', 'PVL', 'PUT', 'None'},
            "ann_list": [['PUT', 'MAT'], ['PUT', 'MAT']],

        })
        pairs1.append({
            "common_labels": {'MAT', 'CHM', 'DSC', 'None'},  # the first annotator has not annotated PUT, so its 100%
            "ann_list": [['MAT', 'DSC', 'None', 'None'], ['MAT', 'DSC', 'None', 'PUT']],
        })
        answers1 = {"kappa": 1,
                    "kappa_std": 0,
                    "existing_labels": {'DSC', 'MAT', 'PUT', 'None'},
                    "accuracies": {"DSC": 1, "MAT": 1, "PUT": 1, "None": 1},
                    "similarity_matrix": np.array([
                        [2, 0, 0, 0],
                        [0, 4, 0, 0],
                        [0, 0, 2, 0],
                        [0, 0, 0, 3]]),
                    "similarity_labels": ['DSC', 'MAT', 'PUT', 'None']}

        self.all_pairs.append(pairs1)
        self.all_answers.append(answers1)

        # an example where some annotations and labels do not match
        pairs2 = list()
        pairs2.append({
            "common_labels": {'MAT', 'CHM', 'DSC', 'REF', 'None'},
            "ann_list": [['MAT', 'DSC', 'None', 'None'], ['MAT', 'DSC', 'None', 'REF']],
        })
        answers2 = {"kappa": 2/3,
                    "kappa_std": 0,
                    "existing_labels": {'DSC', 'MAT', 'REF', 'None'},
                    "accuracies": {"DSC": 1, "MAT": 1, "REF": 0, "None": 2/3},
                    "similarity_matrix": np.array([
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0, 0.5],
                        [0.0, 0.0, 0.5, 1.0]]),
                    "similarity_labels": ['MAT', 'DSC', 'REF', 'None']}

        # an example where some annotations and labels do not match
        pairs2 = list()
        pairs2.append({
            "common_labels": {'MAT', 'CHM', 'DSC', 'REF', 'None', 'PUT', 'PVL'},
            "ann_list": [['MAT', 'DSC', 'None', 'MAT', 'None', 'REF'], ['MAT', 'DSC', 'None', 'None', 'MAT', 'DSC']],
        })
        answers2 = {"kappa": 0.307692307,
                    "kappa_std": 0,
                    "existing_labels": {'DSC', 'MAT', 'REF', 'None'},
                    "accuracies": {"DSC": 2/3, "MAT": 0.5, "REF": 0, "None": 0.5},
                    "similarity_matrix": np.array([
                        [1.0, 0.0, 0.0, 1.0],
                        [0.0, 1.0, 0.5, 0.0],
                        [0.0, 0.5, 0.0, 0.0],
                        [1.0, 0.0, 0.0, 1.0]]),
                    "similarity_labels": ['MAT', 'DSC', 'REF', 'None']}

        self.all_pairs.append(pairs2)
        self.all_answers.append(answers2)

        # an example where some annotations and labels do not match
        pairs3 = list()
        pairs3.append({
            "common_labels": {'MAT', 'CHM', 'DSC', 'REF', 'None', 'PUT', 'PVL'},
            "ann_list": [['MAT', 'DSC', 'None', 'MAT', 'None', 'REF'], ['MAT', 'DSC', 'None', 'None', 'MAT', 'DSC']],
        })
        answers3 = {"kappa": 0.375,
                    "kappa_std": 0,
                    "existing_labels": {'DSC', 'MAT', 'REF', 'None'},
                    "accuracies": {"DSC": 1.0, "MAT": 0.5, "None": 0.5},
                    "similarity_matrix": np.array([
                        [1.0, 0.0, 1.0],
                        [0.0, 1.0, 0.0],
                        [1.0, 0.0, 1.0]]),
                    "similarity_labels": ['MAT', 'DSC', 'None']}

        self.all_pairs.append(pairs3)
        self.all_answers.append(answers3)

    def test_values(self):
        """Tests the performance of the algorithms using actual test values"""
        for i, pairs in enumerate(self.all_pairs):
            # testing the cohen kappa scores
            kappa, kappa_std, existing_labels = self.am.cohen_kappa(
                                                        pairs=pairs,
                                                        labels=self.all_answers[i]["similarity_labels"])
            self.assertAlmostEqual(kappa, self.all_answers[i]["kappa"])
            self.assertAlmostEqual(kappa_std, self.all_answers[i]["kappa_std"])
            self.assertCountEqual(existing_labels, self.all_answers[i]["existing_labels"])

            # testing similarity matrix
            similarity_matrix, similarity_labels = self.am.similarity_matrix(
                pairs=pairs,
                labels=self.all_answers[i]["similarity_labels"])
            self.assertCountEqual(similarity_labels, self.all_answers[i]["similarity_labels"])
            assert_almost_equal(similarity_matrix, self.all_answers[i]["similarity_matrix"])

            # testing the accuracies
            accuracies = self.am.accuracies(similarity_matrix=similarity_matrix, labels=similarity_labels)
            for key in accuracies:
                if np.isnan(accuracies[key]):
                    accuracies[key] = None
                assert_almost_equal(accuracies[key], self.all_answers[i]["accuracies"][key])

    def test_basic(self):
        """Tests the db connectivity and some basic data types and dimensions"""
        all_labels = [{"MAT", "CHM"}, ["MAT", "DSC", "CHM"], None]
        for labels in all_labels:
            pairs, existing_labels = self.am._annotation_pairs(labels=labels)
            if len(pairs) > 0:
                self.assertTrue(type(pairs[0]["common_labels"]) is set)
                self.assertTrue(type(pairs[0]["doi"]) is str)
                self.assertTrue(type(pairs[0]["ann_list"]) is list)
                self.assertTrue(len(pairs[0]["ann_list"]) == 2)

            # cohen kappa
            kappa, kappa_std, existing_labels = self.am.cohen_kappa()
            self.assertTrue(kappa >= 0)
            self.assertTrue(kappa_std >= 0)
            self.assertTrue(type(existing_labels) is set)

            # similarity matrix
            similarity_matrix, similarity_labels = self.am.similarity_matrix(labels=labels)
            self.assertTrue(type(similarity_labels) is list)
            if labels is not None:
                sim_shape = (len(labels), len(labels))
            else:
                sim_shape = (len(similarity_labels), len(similarity_labels))
            assert_almost_equal(similarity_matrix.shape, sim_shape)

            # accuracies
            accuracies = self.am.accuracies(labels=similarity_labels, similarity_matrix=similarity_matrix)
            self.assertEqual(len(accuracies), len(similarity_labels))
