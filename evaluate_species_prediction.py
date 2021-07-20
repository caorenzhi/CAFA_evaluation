from pathlib import Path
from typing import Iterable
import json
import numpy as np
import pandas as pd


def main():
    prediction_filepath_str = (
        "data/ZhangFreddolinoLab/ZhangFreddolinoLab_1_7227_go_CCO.json"
    )
    benchmark_filepath_str = "data/benchmark/CCO_DROME_7227_benchmark.json"
    with open(prediction_filepath_str, "r") as prediction_handle:
        predictions = json.load(prediction_handle)

    with open(benchmark_filepath_str, "r") as benchmark_handle:
        benchmark = json.load(benchmark_handle)

    metrics_df = get_confusion_matrix_dataframe(
        prediction_dict=predictions, benchmark_dict=benchmark
    )
    return metrics_df


def initialize_proteins_and_thresholds_dataframe(
    proteins: Iterable, thresholds: Iterable
) -> pd.DataFrame:
    """ Creates a pandas.DataFrame that will have one row per protein/threshold pair.
    # It will only include the thresholds that actually exist in the prediction data and not a
    # complete range of possible thresholds:
    :param proteins:
    :param thresholds:
    :return:
    """

    matrix = np.zeros(((len(proteins) * len(thresholds)), 6))
    protein_and_threshold_df = pd.DataFrame(
        data=matrix, columns=("protein", "threshold", "tp", "fp", "fn", "tn")
    )
    df_datatypes = {
        "protein": "str",
        "threshold": "float",
        "tp": "int",
        "fp": "int",
        "fn": "int",
        "tn": "int",
    }
    protein_and_threshold_df = protein_and_threshold_df.astype(df_datatypes)

    # The DataFrame is empty. Next, populate the protein and threshold columns:
    benchmark_protein_index = -1

    for i in range(0, protein_and_threshold_df.shape[0]):
        threshold_index = i % len(thresholds)

        if threshold_index == 0:
            # for every complete loop of the threshold range,
            # increment the protein index:
            benchmark_protein_index += 1

        protein_and_threshold_df.iloc[i, 0] = proteins[benchmark_protein_index]
        protein_and_threshold_df.iloc[i, 1] = thresholds[threshold_index]

    protein_and_threshold_df.set_index(
        ["protein", "threshold"], drop=True, inplace=True
    )

    """ At this point, we have a DataFrame with this form:
    +------------------------+------+------+------+------+
    |                        |   tp |   fp |   fn |   tn |
    +========================+======+======+======+======+
    | ('T72270000115', 0.01) |    0 |    0 |    0 |    0 |
    +------------------------+------+------+------+------+
    | ('T72270000115', 0.02) |    0 |    0 |    0 |    0 |
    +------------------------+------+------+------+------+
    | ('T72270000115', 0.03) |    0 |    0 |    0 |    0 |
    +------------------------+------+------+------+------+
    | ('T72270000115', 0.05) |    0 |    0 |    0 |    0 |
    +------------------------+------+------+------+------+
    """
    return protein_and_threshold_df


def get_confusion_matrix_terms(predicted_terms: set, benchmark_terms: set) -> dict:
    """ For two given sets of terms, compute and return:
        * terms for the true positive set
        * terms for the false positive set
        * terms for the false_negative set
    """
    true_positive_terms = predicted_terms & benchmark_terms
    false_positive_terms = predicted_terms - benchmark_terms
    false_negative_terms = benchmark_terms - predicted_terms

    return {
        "TP": true_positive_terms,
        "FP": false_positive_terms,
        "FN": false_negative_terms,
    }

def calculate_weighted_confusion_matrix(predicted_terms: set, benchmark_terms: set, node_weights_df: pd.DataFrame) -> dict:
    ''' Calculates the weighted precision and recall for two sets of terms
    Weighted precision and recall rely on the information content (IC) of relevant terms (nodes).
    Here we retrieve the IC for the relevant nodes from the node_weights_df.
    '''
    cm_terms = get_confusion_matrix_terms(predicted_terms, benchmark_terms)


def calculate_confusion_matrix(predicted_terms: set, benchmark_terms: set) -> dict:
    """ Calculates true positive, false positive and false negative for two sets of terms.
    Does not calcuate true negative.
    """
    cm_terms = get_confusion_matrix_terms(predicted_terms, benchmark_terms)
    true_positive = len(cm_terms["TP"])
    false_positive = len(cm_terms["FP"])
    false_negative = len(cm_terms["FN"])

    return {"TP": true_positive, "FP": false_positive, "FN": false_negative}


def get_confusion_matrix_dataframe(
    prediction_dict: dict, benchmark_dict: dict
) -> pd.DataFrame:
    ''' Constructs a pandas DataFrame with a row for each protein/threshold pair.
    The proteins are sourced from the benchmark_dict and the thresholds are sourced
    from the prediction dict.
   
    The prediction_dict maps proteins to terms and threshold values and should have this form:
    {
        "T72270000115": {
            "GO:0000151": 0.01, "GO:0000228": 0.02, "GO:0000785": 0.02, "GO:0000790": 0.02, "GO:0005575": 0.3, ...
        },
        "T72270000700": {
            "GO:0000151": 0.01, "GO:0000307": 0.02, "GO:0000428": 0.02, "GO:0005575": 0.07, "GO:0005576": 0.01, ...
        },

    And the benchmark_dict should have this form:
    {
        "benchmark_taxon": "DROME",
        "benchmark_taxon_id": null,
        "benchmark_ontology": "bpo",
        "benchmark_ontology_term_count": 28678,
        "protein_annotations": {
            "T72270000015": ["GO:0007154", "GO:0007165", "GO:0007186", "GO:0007602", "GO:0007603", ...],
             "T72270000115": ["GO:0000003", "GO:0007276", "GO:0007283", "GO:0008150", "GO:0010468", ...],
        }
    }
    
    '''

    # Get all threshold values from the nested dictionaries in the prediction data:
    distinct_prediction_thresholds = sorted(
        list(
            {
                threshold
                for protein in prediction_dict.values()
                for threshold in protein.values()
            }
        )
    )

    # the benchmark json data should include this metadata:
    benchmark_ontology = benchmark_dict.get("benchmark_ontology")
    benchmark_ontology_term_count = benchmark_dict.get("benchmark_ontology_term_count")
    benchmark_taxon = benchmark_dict.get("benchmark_taxon")
    benchmark_taxon_id = benchmark_dict.get("benchmark_taxon_id")
    benchmark_annotations = benchmark_dict.get("protein_annotations")
    benchmark_proteins = list(benchmark_annotations.keys())

    # Next, create a pandas.DataFrame that will have one row per protein/threshold pair.
    # It will only include the thresholds that actually exist in the prediction data and not a
    # complete range of possible thresholds:

    protein_and_threshold_df = initialize_proteins_and_thresholds_dataframe(
        proteins=benchmark_proteins, thresholds=distinct_prediction_thresholds
    )

    # protein_and_threshold_df has keys (proteins and thresholds), but no values.
    # Next, populate the DataFrame with the confusion matrix values
    for threshold in distinct_prediction_thresholds:
        for protein in benchmark_proteins:
            predicted_terms = prediction_dict.get(protein, {})
            # Limit the predictions by the threshold at hand:
            predicted_annotations = {
                k for k, v in predicted_terms.items() if v >= threshold
            }
            benchmark_protein_annotation = set(benchmark_annotations.get(protein))

            conf_matrix = calculate_confusion_matrix(
                predicted_terms=predicted_annotations,
                benchmark_terms=benchmark_protein_annotation,
            )
            true_negative = benchmark_ontology_term_count - sum(conf_matrix.values())
            protein_and_threshold_df.loc[protein, threshold].tp = conf_matrix["TP"]
            protein_and_threshold_df.loc[protein, threshold].fp = conf_matrix["FP"]
            protein_and_threshold_df.loc[protein, threshold].fn = conf_matrix["FN"]
            protein_and_threshold_df.loc[protein, threshold].tn = true_negative

    # Lastly, add some metadata to each row:
    protein_and_threshold_df.insert(0, "taxon", benchmark_taxon)
    protein_and_threshold_df.insert(0, "taxon_id", benchmark_taxon_id)
    protein_and_threshold_df.insert(0, "ontology", benchmark_ontology)

    """ The final DataFrame has this form:
    +------------------------+------------+------------+---------+------+------+------+------+
    |                        | ontology   |   taxon_id | taxon   |   tp |   fp |   fn |   tn |
    +========================+============+============+=========+======+======+======+======+
    | ('T72270000115', 0.01) | CCO        |       7227 | DROME   |   10 |  102 |    0 | 3793 |
    +------------------------+------------+------------+---------+------+------+------+------+
    | ('T72270000115', 0.02) | CCO        |       7227 | DROME   |   10 |   44 |    0 | 3851 |
    +------------------------+------------+------------+---------+------+------+------+------+
    | ('T72270000115', 0.03) | CCO        |       7227 | DROME   |   10 |    3 |    0 | 3892 |
    +------------------------+------------+------------+---------+------+------+------+------+
    | ('T72270000115', 0.05) | CCO        |       7227 | DROME   |   10 |    3 |    0 | 3892 |
    +------------------------+------------+------------+---------+------+------+------+------+
    | ('T72270000115', 0.06) | CCO        |       7227 | DROME   |   10 |    3 |    0 | 3892 |
    +------------------------+------------+------------+---------+------+------+------+------+
    """
    return protein_and_threshold_df


if __name__ == "__main__":

    result = main()
    print(result)