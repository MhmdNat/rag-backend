from collections import defaultdict
from langchain_core.documents import Document

def merge_by_page(docs):
    pages = defaultdict(list)

    for doc in docs:
        page = doc.metadata.get("page_number")

        text = doc.page_content.strip()
        if text:
            pages[page].append(text)

    merged_docs = []

    for page_num in sorted(pages):
        merged_docs.append(
            Document(
                page_content="\n".join(pages[page_num]),
                metadata={"page_number": page_num}
            )
        )

    return merged_docs

def clean_docs(docs):
    print("Cleaning parsed documents...")
    cleaned = []

    for doc in docs:
        if not doc.page_content or doc.metadata.get("category") == "Image":
            # Could later add model to describe images and include those descriptions as text chunks
            continue

        # Remove unnecessary metadata that breaks weaviate
        doc.metadata.pop("coordinates", None)  
        if len(doc.page_content) <50:
            continue
        cleaned.append(doc)
    return cleaned
