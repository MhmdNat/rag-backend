from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset



def get_pdfs_from_directory(directory):
    import os
    pdf_files = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, filename))
    return pdf_files


def generate_goldens():
    synthesizer = Synthesizer("BAAI/bge-small-en-v1.5") 

    # Generate question–answer pairs from your source documents
    document_paths = get_pdfs_from_directory("data\\pdfs")

    print(f"Found {len(document_paths)} PDF documents for golden dataset generation.")

    goldens = synthesizer.generate_goldens_from_docs(
    document_paths=document_paths,
    include_expected_output=True, # generates reference answers
    )
    
    print(f"Generated {len(goldens)} golden examples from documents.")
    print("Sample golden example:", goldens[0] if goldens else "No goldens generated.")
    return goldens


def save_golden_dataset(golden_dataset):
    import json
    with open("data\\golden_dataset.json", "w") as f:
        json.dump(golden_dataset, f)


def create_dataset(goldens):
    dataset = EvaluationDataset()
    for golden in goldens:
        dataset.add_example(
            input=golden["question"],
            expected_output=golden["expected_output"],
            metadata={"source_doc": golden["source_doc"]}
        )
    return dataset

def main():
    goldens = generate_goldens()


if __name__ == "__main__":
    main()
