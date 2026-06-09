from langchain_weaviate import WeaviateVectorStore


def create_vectorstore(client, embedding_model, index_name="RAGDocs", text_key="text"):
    return WeaviateVectorStore(
        client=client,
        index_name=index_name,
        embedding=embedding_model,
        text_key=text_key,
    )
