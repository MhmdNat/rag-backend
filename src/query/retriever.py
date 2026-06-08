from functools import lru_cache

from langsmith import traceable

from src.embeddings.model import create_embedding_model
from src.vectorstore.client import create_weaviate_client
from src.vectorstore.vector_store import create_vectorstore


client = None


def get_retriever_client():
    global client
    if client is None:
        client = create_weaviate_client()
    return client


@lru_cache(maxsize=1)
def get_vectorstore(index_name="RAGDocs"):
    embedding_model = create_embedding_model()
    return create_vectorstore(get_retriever_client(), embedding_model, index_name)


def close_retriever_client():
    global client
    if client is not None:
        client.close()
        client = None
    get_vectorstore.cache_clear()


@traceable(name="retrieve_top_k")
def retrieve_top_k(query, index_name="RAGDocs", top_k=50):
    vectorstore = get_vectorstore(index_name)
    retrieved_results = vectorstore.similarity_search(query, k=top_k)

    print(f"\nRetrieved top {len(retrieved_results)} results for query: '{query}'")
    print("Top retrieved passage from retrieval step:")
    print(retrieved_results[0].page_content[:100]+'...' if retrieved_results else "No passages retrieved")
    print()
    return retrieved_results, get_retriever_client()




