import asyncio
import json
from typing import Optional

from src.query.apiCommunication.sendToOllama import create_prompt, send_prompt_to_ollama
from src.query.reranker import extract_top_k_reranked, format_passages
from src.query.rewrite_query import rewrite_query
from src.query.retriever import retrieve_top_k
from langsmith import traceable

from src.api.service.message import save_message


@traceable(name="web_rag_pipeline")
async def run_web_rag_pipeline(
    query_text,
    index_name="RAGDocs",
    top_k=5,
    user_id=None,
    chat_id=None,
    query_id=None,
    parent_message_id: Optional[int] = None,   # set when this is a regeneration
):
    rewritten_query = await rewrite_query(query_text)
    retrieved_results, _ = await retrieve_top_k(rewritten_query, index_name=index_name, top_k=30)
    reranked_results = await extract_top_k_reranked(rewritten_query, retrieved_results, top_k=top_k)
    passages = format_passages(reranked_results)

    prompt = create_prompt(rewritten_query, passages)
    response_stream = await send_prompt_to_ollama(prompt, stream = True)

    full_answer = ""
    async for chunk in response_stream:
        token = chunk.response
        if token:
            full_answer += token
            payload = json.dumps({"t": token})
            yield f"event: token\ndata: {payload}\n\n"

    _, answer_id = await asyncio.to_thread(
        save_message,
        content=full_answer,
        user_id=user_id,
        chat_id=chat_id,
        role="assistant",
        parent_message_id=parent_message_id,   # None for first response, root id for regenerations
    )

    metadata_payload = {
        "query": query_text,
        "rewritten_query": rewritten_query,
        "answer": full_answer,
        "Context": "||PASSAGE||".join(passages),
        "chat_id": chat_id,
        "user_id": user_id,
        "query_message_id": query_id,
        "answer_message_id": answer_id,
        "parent_message_id": parent_message_id,  # frontend needs this to update the right message
    }
    yield f"event: metadata\ndata: {json.dumps(metadata_payload)}\n\n"
