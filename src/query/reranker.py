from sentence_transformers import CrossEncoder
import torch
import dotenv
from functools import lru_cache
from langsmith import traceable
dotenv.load_dotenv()

model = None

@lru_cache(maxsize=1)
def get_model():
    global model
    if model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading reranker model on {device}...")
        model = CrossEncoder("BAAI/bge-reranker-v2-m3", device=device)
    return model


@traceable(name="rerank")
def rerank(query, passages):
    pairs = [(query, passage.page_content) for passage in passages]
    scores = get_model().predict(pairs)
    scored_passages = sorted(
        zip(passages, scores),
        key=lambda item: item[1],
        reverse=True,
    )
    
    return scored_passages

@traceable(name="extract_top_k_reranked")
def extract_top_k_reranked(query, passages, top_k=5):
    scored_passages = rerank(query, passages)
    top_k_passages = [passage for passage, _ in scored_passages[:top_k]]
    print("\nTop passage after reranking:")
    print(f"{top_k_passages[0].page_content[:100]}..." if top_k_passages else "No passages reranked")
    return top_k_passages


def format_passages(passages):
    results = []
    for i, passage in enumerate(passages):
        results.append(passage.page_content)
    return results
