from functools import lru_cache


@lru_cache(maxsize=1)
def create_embedding_model():
    from langchain_huggingface import HuggingFaceEmbeddings
    import torch
    import dotenv

    #to get HF_TOKEN from .env for HF hub faster access
    dotenv.load_dotenv()

    # Check if GPU is available else fallback to CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading embedding model on {device}...")

    # Load embedding model 
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": device}
    )

    return embedding_model