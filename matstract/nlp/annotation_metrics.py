import itertools

from sklearn.metrics import cohen_kappa_score, confusion_matrix
import numpy as np
from matstract.models.database import open_db_connection
from matstract.models.annotation import TokenAnnotation
from matstract.models.annotation_builder import AnnotationBuilder


class AnnotationMetrics:
    _db = None

    def __init__(self, local=False):
        self._db = open_db_connection(access="annotator", local=local)

    def similarity_matrix(self, labels=None, annotators=None, pairs=None):
        """
        Computes a similarity matrix across different annotators for different labels to
        give an idea which labels are the most similar ones, so maybe they can be merged or re-defined
        :param labels:      A list or set of labels to consider. If None, all occurring labels will
                            be considered, including the None label
        :param annotators:  A list of user_keys to consider. If none, all users will be considered.
        :param pairs:       You can specify the pairs of annotations manually if you don't want to connect to the db
                            [{"common_labels": ['MAT', ..], "ann_list": [['DSC', 'MAT', ..], ['DSC', 'CHM', ..]]}, ..]
        :return:            A numpy array as the similarity matrix, and an ordered list of existing labels
        """
        if pairs is None:
            pairs, existing_labels = self._annotation_pairs(labels=labels, annotators=annotators)
        else:
            existing_labels = set()
            for pair in pairs:
                # need to compute the existing labels if the pairs are manually supplied
                existing_labels = set().union(existing_labels, set(pair["ann_list"][0]), set(pair["ann_list"][1]))

        if labels is None:
            labels = list(existing_labels)
        else:
            labels = list(labels)

        nr_labels = len(labels)
        similarity_matrix = np.zeros([nr_labels, nr_labels])
        for pair in pairs:
            update_indices = np.array([i for i, e in enumerate(labels) if e in pair["common_labels"]])
            conf_mat = confusion_matrix(
                pair["ann_list"][0],
                pair["ann_list"][1],
                labels=[labels[i] for i in update_indices])
            similarity_matrix[update_indices[:, None], update_indices] += (conf_mat + conf_mat.T) / 2

        return similarity_matrix, labels

    def cohen_kappa(self, labels=None, annotators=None, pairs=None):
        """
        Computes cohen kappa for the given set of labels for all annotators pair-wise
        and returns the mean across all annotator pairs. Also returns the used labels.
        This is the overall metric of the agreement between annotators across the labels.
        :param labels:      A set of labels to consider. If None, all occurring labels will
                            be considered, including the None label
        :param annotators:  A list of user_keys to consider. If none, all users will be considered.
        :param pairs:       You can specify the pairs of annotations manually if you don't want to connect to the db
                            [{"common_labels": ['MAT', ..], "ann_list": [['DSC', 'MAT', ..], ['DSC', 'CHM', ..]]}, ..]
        :return:            mean of kappa, its standard deviation and existing labels (set)
        """
        existing_labels = set()
        pairs_supplied = True
        if pairs is None:
            pairs_supplied = False
            pairs, existing_labels = self._annotation_pairs(labels=labels, annotators=annotators)

        kappas = []
        for pair in pairs:
            # need to compute the existing labels if the pairs are manually supplied
            if pairs_supplied:
                existing_labels = set().union(existing_labels, set(pair["ann_list"][0]), set(pair["ann_list"][1]))

            # if one has specified specific labels, need to exclude everything else from common labels
            if labels is not None:
                pair_labels = list(pair["common_labels"].intersection(set(labels)))
            else:
                pair_labels = list(pair["common_labels"])

            # computing kappa for the given pair
            kappas.append(cohen_kappa_score(
                pair["ann_list"][0],
                pair["ann_list"][1],
                labels=pair_labels))

        return np.nanmean(kappas), np.nanstd(kappas), existing_labels

    def accuracies(self, labels=None, annotators=None, similarity_matrix=None):
        """
        Returns average accuracies for each label obtained from the similarity matrix
        by dividing the number on the diagonal with total occurrence count
        e.g. for 2 annotators, each labeled the item 2 times, but only 1 match is found,
        the accuracy would be 50%. If one of them labeled it 2 times, and the other one once
        but with a match, the accuracy would be 66%. If that one label did not match,
        the accuracy would be 0%, etc.
        :param labels:              A list of labels to consider. If None, all occurring labels will
                                    be considered, including the None label
        :param annotators:          A list of user_keys to consider. If none, all users will be considered.
        :param similarity_matrix:   A pre-computed similarity matrix. If provided, this will be used for
                                    the estimation of accuracies, otherwise, these will be computed from the
                                    database.
        :return:                    A dictionary of accuracies for each label
        """
        if similarity_matrix is None:
            similarity_matrix, labels = self.similarity_matrix(labels=labels, annotators=annotators)

        accuracies = dict()
        for i, label in enumerate(list(labels)):
            accuracies[label] = similarity_matrix[i, i] / np.nansum(similarity_matrix[i, :])

        return accuracies

    def _annotation_pairs(self, labels=None, annotators=None, doi=None):
        """
        Get's all annotation list pairs to be used for annotator agreement measures
        :param labels:              A set or list of labels to consider. If None, all occurring labels will
                                    A be considered, including the None label
        :param annotators:          A set of user_keys to consider. If none, all users will be considered.
        :return:                    list of tuples representing pairs of annotations and existing labels (set)
        """

        # only the specified labels and annotators
        constraints = dict()
        if labels is not None:
            constraints["labels"] = {"$in": list(labels)}
        if annotators is not None:
            constraints["user"] = {"$in": list(annotators)}
        if doi is not None:
            constraints["doi"] = {"$in": list(doi)}

        relevant_annotations = getattr(self._db, AnnotationBuilder.ANNOTATION_COLLECTION).find(constraints)

        # group by doi
        ann_groups = dict()
        for annotation in relevant_annotations:
            token_annotation = TokenAnnotation(annotation=annotation)
            ann_list = token_annotation.to_ann_list()
            if annotation["doi"] in ann_groups.keys():
                ann_groups[annotation["doi"]].append({"list": ann_list, "labels": token_annotation.labels})
            else:
                ann_groups[annotation["doi"]] = [{"list": ann_list, "labels": token_annotation.labels}]

        # generate pairs
        pairs = []
        existing_labels = set()
        for doi in ann_groups:
            if len(ann_groups[doi]) > 1:
                for pair in itertools.combinations(ann_groups[doi], r=2):
                    common_labels = set(pair[0]["labels"]).intersection(set(pair[1]["labels"])).union({str(None)})
                    existing_labels = set().union(existing_labels, set(pair[0]["list"]), set(pair[1]["list"]))
                    pairs.append({"common_labels": common_labels, "ann_list": [p["list"] for p in pair], "doi": doi})

        return pairs, existing_labels
