"""
RAG Knowledge Base — AI Sage financial guidance retrieval.

Anti-hallucination role:
  The LLM is only allowed to provide guidance that is directly retrievable
  from reviewed knowledge documents. It cannot generate guidance
  from its pre-training knowledge alone.

In production: replace FAISS with Azure AI Search or Cosmos DB vector search
with UK data residency.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings

KNOWLEDGE_DOCS_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge_docs"
_vectorstore: FAISS | None = None


def _get_embeddings():
    """
    Use Azure OpenAI embeddings in production (UK data residency).
    Falls back to standard OpenAI for local development.
    """
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def build_knowledge_base() -> FAISS:
    """
    Load all .txt knowledge documents and build a FAISS vector index.
    Called once at startup.
    """
    global _vectorstore
    docs: list[Document] = []

    for doc_path in KNOWLEDGE_DOCS_DIR.glob("*.txt"):
        loader = TextLoader(str(doc_path), encoding="utf-8")
        raw_docs = loader.load()
        for d in raw_docs:
            d.metadata["source"] = doc_path.name
        docs.extend(raw_docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n---\n", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)

    embeddings = _get_embeddings()
    _vectorstore = FAISS.from_documents(chunks, embeddings)
    return _vectorstore


def get_knowledge_base() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = build_knowledge_base()
    return _vectorstore


def retrieve_guidance(query: str, k: int = 3) -> list[dict[str, Any]]:
    """
    Retrieve the most relevant guidance chunks for a user query.
    Returns a list of dicts with 'content' and 'source' keys.

    The LLM MUST base its response on these retrieved chunks, not
    on its own pre-training knowledge about financial products.
    """
    kb = get_knowledge_base()
    results = kb.similarity_search(query, k=k)
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "AI Sage Knowledge Base"),
        }
        for doc in results
    ]
