from __future__ import annotations

import asyncio

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.agents.llm import get_chat_model
from app.agents.prompts import _qa_prompt
from app.agents.retrieval import retrieval_pipeline


def _format_documents(documents: list[Document]) -> str:
    if not documents:
        return "No relevant context was found in the knowledge base."

    parts: list[str] = []
    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source") or document.metadata.get("sourceURL", "unknown")
        parts.append(f"[{index}] Source: {source}\n{document.page_content}")
    return "\n\n---\n\n".join(parts)


async def ask_agent(query: str) -> str:
    """Retrieve context from Qdrant, then generate an answer with Gemini."""

    documents = retrieval_pipeline(query)
    context = _format_documents(documents)

    chain = _qa_prompt() | get_chat_model() | StrOutputParser()
    return await chain.ainvoke({"input": query, "context": context})


if __name__ == "__main__":
    answer = asyncio.run(ask_agent("What is RAG?"))
    print(answer)
