from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

RAG_SYSTEM_PROMPT = (
    "You are a careful assistant. Answer the user's question using ONLY the "
    "information in the provided context. If the context does not contain enough "
    "information, say you do not know and avoid guessing."
)


def _qa_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"{RAG_SYSTEM_PROMPT} \n\n Use the following context to answer the question: \n {{context}}",
            ),
            ("human", "{input}"),
        ]
    )
