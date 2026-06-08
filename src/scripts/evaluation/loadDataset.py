from deepeval.dataset import EvaluationDataset

def load_dataset():
    dataset = EvaluationDataset()
    dataset.add_goldens_from_json_file("data/evaluation/goldenDatasets/cis_controls_v8_golden_dataset.json")
    return dataset