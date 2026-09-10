"""
RAG / Advisory Agent — owner: Prapti (data layer) + Jay/Adeey (retrieval-generation loop)

Answers "why is this restricted", legal restrictions, and marine policy questions
grounded strictly in official government acts, notifications, and gazetteers with verifiable citations.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from backend.gateway.ai_gateway import call_llm
from agents.rag_advisory.document_processor import DocumentProcessor
from agents.rag_advisory.vector_store import VectorStoreManager

logger = logging.getLogger("varuna.rag")

# ── Statutory Base Corpus (Guaranteed in-memory baseline from SIH specification) ──
CORPUS = [
    {
        "source": "Maharashtra MFRA 1981, Section 4",
        "chunk": (
            "No mechanized fishing vessel shall engage in fishing within the territorial "
            "waters measured from the baseline up to a distance of 5 nautical miles. Waters "
            "within 5 NM are reserved exclusively for non-mechanized traditional fishermen."
        ),
        "keywords": ["maharashtra", "mechanized", "distance", "5 nautical miles", "trawler", "inshore", "purse seine"],
    },
    {
        "source": "Tamil Nadu MFRA 1983, Section 5",
        "chunk": (
            "Inshore waters up to a distance of 3 nautical miles from the shoreline are strictly "
            "reserved for traditional non-mechanized craft (kattumarams, vallams). Mechanized "
            "trawlers are prohibited from operating within 3 nautical miles."
        ),
        "keywords": ["tamil nadu", "3 nautical miles", "catamaran", "kattumaram", "traditional", "mechanized"],
    },
    {
        "source": "DAHDF Notification — Uniform Monsoon Ban",
        "chunk": (
            "Fishing by mechanized and motorized fishing vessels is strictly prohibited in the "
            "Indian Exclusive Economic Zone along the West Coast (Gujarat, Maharashtra, Goa, Karnataka, Kerala) "
            "from 1st June to 31st July (61 days). On the East Coast (WB, Odisha, AP, TN), "
            "the ban operates from 15th April to 14th June (61 days)."
        ),
        "keywords": ["monsoon ban", "west coast", "east coast", "june", "july", "april", "annual ban", "dates", "closed season"],
    },
    {
        "source": "Wildlife Protection Act 1972, Schedule I",
        "chunk": (
            "Sea turtles (Olive Ridley, Green turtle), Dugongs (sea cows), and Whale Sharks are "
            "listed under Schedule I with absolute protection. Any accidental capture in fishing "
            "gear must be immediately released unharmed and reported to the forest/fisheries range office."
        ),
        "keywords": ["turtle", "olive ridley", "dugong", "whale shark", "protected species", "bycatch", "coral"],
    },
    {
        "source": "INCOIS & IMD Standard Operational Guidelines",
        "chunk": (
            "Wave height exceeding 2.5 metres or sustained winds above 40 km/h (22 knots) are "
            "classified as UNSAFE for small and artisanal crafts. Fishermen must heed ocean state "
            "forecast warnings regardless of Potential Fishing Zone (PFZ) productivity scores."
        ),
        "keywords": ["wave height", "wind", "safety threshold", "incois", "imd", "advisory", "pfz", "rough sea"],
    },
]


class RAGAdvisoryAgent:
    """
    RAG Advisory Agent providing citation-grounded answers to maritime regulation questions.
    """

    def __init__(self, use_vector_store: bool = True):
        self.use_vector_store = use_vector_store
        self.vector_store = None

        if self.use_vector_store:
            try:
                self.vector_store = VectorStoreManager()
                # If vector store is empty, load sample docs from data/rag_documents
                if self.vector_store.count() == 0:
                    docs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "rag_documents"
                    if docs_dir.exists():
                        processor = DocumentProcessor()
                        chunks = processor.process_directory(docs_dir)
                        if chunks:
                            self.vector_store.add_chunks(chunks)
                            logger.info(f"Loaded {len(chunks)} regulatory chunks into RAG vector store.")
            except Exception as e:
                logger.warning(f"Could not initialize VectorStoreManager: {e}. Using statutory CORPUS.")
                self.vector_store = None

    async def answer_with_citations(self, question: str, query_run_id: str = "") -> dict[str, Any]:
        """
        Retrieve relevant statutory chunks and generate a grounded answer with citations.

        Returns contract matching Planner and Adeey's visualization specs:
            {
                "agent": "rag_advisory",
                "query_run_id": str,
                "answer": str,
                "citations": list[dict],
                "confidence": float,
                "source": str,
            }
        """
        q_clean = question.strip()
        if not q_clean:
            return {
                "agent": "rag_advisory",
                "query_run_id": query_run_id,
                "answer": "Please ask a question regarding marine fishing regulations, zones, or safety advisories.",
                "citations": [],
                "confidence": 0.0,
                "source": "RAG Advisory Agent",
            }

        # 1. Retrieve top-k relevant chunks
        relevant_chunks: list[dict[str, Any]] = []

        if self.vector_store is not None:
            try:
                relevant_chunks = self.vector_store.search(q_clean, top_k=3)
            except Exception as e:
                logger.warning(f"Vector search failed ({e}), falling back to statutory corpus.")

        if not relevant_chunks:
            # Fallback to statutory CORPUS keyword matching
            q_lower = q_clean.lower()
            scored = []
            for doc in CORPUS:
                score = sum(1 for kw in doc["keywords"] if kw in q_lower)
                if score > 0:
                    scored.append((score, doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            relevant_docs = [c[1] for c in scored[:3]] if scored else [CORPUS[0]]

            relevant_chunks = [
                {
                    "source": r["source"],
                    "chunk": r["chunk"],
                    "relevance_score": 0.90,
                }
                for r in relevant_docs
            ]

        # Format citations
        citations = [
            {
                "source": r.get("source", "Official Regulation"),
                "chunk": r.get("chunk", ""),
                "relevance_score": r.get("relevance_score", 0.85),
            }
            for r in relevant_chunks
        ]

        # 2. Grounded generation using LLM
        context_text = "\n---\n".join(
            f"Source: {c['source']}\nContent: {c['chunk']}" for c in citations
        )

        prompt = (
            f"User Question: {q_clean}\n\n"
            f"Statutory Context:\n{context_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the question clearly and concisely using ONLY the provided Statutory Context.\n"
            "2. Always cite the specific Act, Section, or Notification name in your answer.\n"
            "3. If the context does not contain the answer, say: 'The official regulations in the database do not cover this specific question.'\n"
            "4. Do NOT invent regulations, penalties, or dates."
        )

        try:
            answer = await call_llm(
                "rag",
                [
                    {
                        "role": "system",
                        "content": "You are the Marine Regulation and Maritime Legal Advisory expert for India (VARUNA/ORCA). You provide evidence-grounded legal advice with exact statutory citations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=512,
            )
        except Exception as e:
            logger.warning(f"LLM call failed ({e}); synthesizing grounded answer directly from context.")
            # Deterministic fallback text from the highest-ranked chunk
            top_source = citations[0]["source"] if citations else "Marine Regulations"
            top_content = citations[0]["chunk"] if citations else "No context available."
            answer = f"According to {top_source}: {top_content}"

        avg_confidence = round(
            sum(c["relevance_score"] for c in citations) / len(citations) if citations else 0.85, 2
        )

        return {
            "agent": "rag_advisory",
            "query_run_id": query_run_id,
            "answer": answer.strip(),
            "citations": citations,
            "confidence": min(0.95, avg_confidence),
            "source": "Official Marine Regulations & Gazetteers",
        }
