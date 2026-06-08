from src.query.pipeline import run_rag_pipeline

def query_command(query_text, index_name, k=5):
    result, weaviate_client = run_rag_pipeline(query_text, index_name=index_name, top_k=k)
    print(f"\n LLM's final answer: {result['answer'] or 'No response from Ollama'}")
    if weaviate_client:
        weaviate_client.close()
    return result
    