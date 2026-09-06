"""
RAG / Advisory Agent — owner: Prapti (data layer) + Jay/Adeey (retrieval-generation loop)

Answers "why is this restricted" / regulation questions from government
advisories, MFRAs, and marine acts using citation-grounded RAG.

See agents/rag_advisory/README.md for full task breakdown (MVP + further stage).
"""


class RAGAdvisoryAgent:
    async def answer_with_citations(self, question: str) -> dict:
        raise NotImplementedError("TODO: retrieve from vector DB, generate grounded answer")
