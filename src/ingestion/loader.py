import pickle
import os
import dotenv

dotenv.load_dotenv()
    
def load_pdf(source):
    print("Importing Libraries for PDF parsing...")
    print(source)
    from langchain_unstructured import UnstructuredLoader
    

    print("Parsing PDF document...")
    loader = UnstructuredLoader(
        file_path=str(source),
        partition_via_api=False,
        strategy="hi_res"
    )

    docs = list(loader.lazy_load())
    
    save_to_cache(docs)
    return docs


def save_to_cache(docs):
    with open("data\\parsed_docs.pkl", "wb") as f:

        pickle.dump(docs, f)

    
def load_pdf_from_cache(source, force=False):
    if not os.path.exists("data\\parsed_docs.pkl") or force:
        return load_pdf(source)
    else:
        print("Loading parsed documents from cache...")
        with open("data\\parsed_docs.pkl", "rb") as f:
            docs = pickle.load(f)
            print("Number of document objects parsed:", len(docs))
            return docs

