import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n"],
    )
    chunks = splitter.split_documents(docs)

    for chunk_index, chunk in enumerate(chunks):
        page_number = chunk.metadata.get("page_number")
        chunk.metadata["chunk_label"] = f"page_{page_number}_chunk_{chunk_index}"

        normalized_text = " ".join(chunk.page_content.split())
        source_seed = f"{page_number}|{normalized_text}"
        stable_id = hashlib.sha1(source_seed.encode("utf-8")).hexdigest()

        chunk.metadata["source_id"] = stable_id
        chunk.metadata["element_id"] = stable_id

    return chunks
