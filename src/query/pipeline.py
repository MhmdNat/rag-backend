from src.query.apiCommunication.sendToOllama import create_prompt, send_prompt_to_ollama
from src.query.reranker import extract_top_k_reranked, format_passages
from src.query.rewrite_query import rewrite_query
from src.query.retriever import retrieve_top_k


def run_rag_pipeline(query_text, index_name="RAGDocs", top_k=5):
    rewritten_query = rewrite_query(query_text)
    retrieved_results, weaviate_client = retrieve_top_k(rewritten_query, index_name=index_name, top_k=50)
    reranked_results = extract_top_k_reranked(rewritten_query, retrieved_results, top_k=top_k)
    passages = format_passages(reranked_results)

    prompt = create_prompt(rewritten_query, passages)
    response = send_prompt_to_ollama(prompt)

    return {
        "query": query_text,
        "rewritten_query": rewritten_query,
        "retrieved_results": retrieved_results,
        "retrieval_context": passages,
        "prompt": prompt,
        "response": response,
        "answer": response.get("response", ""),
    }, weaviate_client
