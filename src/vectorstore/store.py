

def create_record_manager(index_name, db_url="sqlite:///record_manager_cache.sql"):
    from langchain_classic.indexes import SQLRecordManager
    namespace = f"weaviate/{index_name}"
    record_manager = SQLRecordManager(namespace, db_url=db_url)
    record_manager.create_schema()
    return record_manager


def collection_is_empty(client, index_name):
    if not client.collections.exists(index_name):
        return True

    collection = client.collections.get(index_name)
    aggregate = collection.aggregate.over_all(total_count=True)
    return aggregate.total_count == 0


def store_vectors(chunks, embedding_model, batch_size, index_name="RAGDocs", force=False):
    from langchain_core.indexing import index
    from src.vectorstore.client import create_weaviate_client
    from src.vectorstore.vector_store import create_vectorstore
    import warnings

    warnings.filterwarnings(
        "ignore",
        message="Using SHA-1 for document hashing.*"
    )

    print("Connecting to Weaviate...")
    client = create_weaviate_client()
    try:
        vectorstore = create_vectorstore(client, embedding_model, index_name)

        record_manager = create_record_manager(index_name)
        force_update = force or collection_is_empty(client, index_name)

        if force_update:
            print("Forcing vector indexing because cache was bypassed or Weaviate is empty...")

        print("Indexing vectors into Weaviate...")

        result = index(
            chunks,
            record_manager,
            vectorstore,
            cleanup="incremental",
            batch_size=batch_size,
            source_id_key="source_id",
            force_update=force_update,
        )

        print("Indexing result:", result)

        return result
    finally:
        from src.vectorstore.client import disconnect_weaviate_client
        disconnect_weaviate_client(client)
