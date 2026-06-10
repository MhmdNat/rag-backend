import asyncio
from functools import lru_cache
from langsmith import traceable

from src.embeddings.model import create_embedding_model
from src.vectorstore.client import create_weaviate_client  # ← sync, not async
from src.vectorstore.vector_store import create_vectorstore

_client = None
_vectorstore = None

def get_retriever_client():
    global _client
    if _client is None:
        _client = create_weaviate_client()  # sync connect_to_local()
    return _client

async def get_vectorstore(index_name="RAGDocs"):
    global _vectorstore
    if _vectorstore is None:
        client = get_retriever_client()
        embedding_model = create_embedding_model()
        _vectorstore = create_vectorstore(client, embedding_model, index_name)
    return _vectorstore

async def close_retriever_client():
    global _client, _vectorstore
    if _client is not None:
        _client.close()
        _client = None
    _vectorstore = None

@traceable(name="retrieve_top_k")
async def retrieve_top_k(query, index_name="RAGDocs", top_k=30):
    vectorstore = await get_vectorstore(index_name)
    retrieved_results = await vectorstore.asimilarity_search(query, k=top_k)

    print(f"\nRetrieved top {len(retrieved_results)} results for query: '{query}'")
    print("Top retrieved passage from retrieval step:")
    print(retrieved_results[0].page_content[:100] + '...' if retrieved_results else "No passages retrieved")

    return retrieved_results, get_retriever_client()