def ingest_pdf(source, index, batch_size, force=False):
    from src.ingestion.loader import load_pdf_from_cache
    from src.ingestion.cleaner import clean_docs
    from src.ingestion.chunker import chunk_docs
    from src.embeddings.model import create_embedding_model
    from src.vectorstore.store import store_vectors
    from src.ingestion.cleaner import merge_by_page

    docs = load_pdf_from_cache(source, force=force)
    docs = clean_docs(docs)
    docs = merge_by_page(docs)
    chunks = chunk_docs(docs)
    embedding_model = create_embedding_model()
    store_vectors(chunks, embedding_model, batch_size, index_name=index, force=force)
    print("Ingestion complete. Ready for querying.")
