import requests
from ollama import chat
from langsmith import traceable

def create_prompt(query, passages_list):
    prompt = f"""You are a careful RAG assistant answering questions about the CIS Controls v8 document, a set of prioritized cybersecuritysafeguards organized into 18 controls and implementation groups.

    Use only the passages and information provided above in this prompt to answer. If the passages contain the answer in different words, synonyms, abbreviations, or an acronym expansion, treat that as supported evidence and answer directly.

    Answer style:
    - Give one short, direct answer by default.
    - Do not start with phrases like "Here are the answers", "Based on the passages", or similar lead-ins.
    - Use bullet points only if the user explicitly asks for a list or multiple items.
    - If the user asks "what are X", answer with the clearest concise definition of X.
    - If the question asks for a definition, give the definition in plain language.
    - If the answer is not in the passages, say exactly: I don't know.
    - Do not mention that you are using passages or context.

    Question: {query}

    Passages:
    """
    for i, passage in enumerate(passages_list):
        prompt += f"{i+1}. {passage}\n"

    return prompt


@traceable(name="send_prompt_to_ollama")
def send_prompt_to_ollama(prompt):
    response = requests.post(
    "http://127.0.0.1:11434/api/generate",
    json={
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": False
        }
    )
    return response.json()
