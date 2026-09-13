"""
RAG / Advisory Agent — owner: Prapti (data layer) + Jay/Adeey (retrieval-generation loop)

Answers "why is this restricted", legal restrictions, and marine policy questions
grounded strictly in official government acts, notifications, and gazetteers with verifiable citations.

Features (Tier 2):
  - Comprehensive 9-state statutory coastal coverage + Union Territories
  - Cross-lingual queries (Hindi, Marathi, English) with native-language synthesis
  - Latency and chunk provenance telemetry for backend observability
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import time
from typing import Any

from backend.gateway.ai_gateway import call_llm
from backend.gateway.multilingual import detect_language
from agents.rag_advisory.document_processor import DocumentProcessor, DocumentChunk
from agents.rag_advisory.vector_store import VectorStoreManager

logger = logging.getLogger("varuna.rag")

# ── Statutory Base Corpus (Comprehensive 9 Coastal States & National Maritime Laws) ──
CORPUS = [
    # ── Maharashtra ──
    {
        "source": "Maharashtra Marine Fishing Regulation Act, 1981 (Section 4)",
        "chunk": (
            "No mechanized fishing vessel shall engage in fishing within the territorial "
            "waters measured from the baseline up to a distance of 5 nautical miles. Waters "
            "within 5 NM are reserved exclusively for non-mechanized traditional fishermen. "
            "The operation of purse seine gear is prohibited in territorial waters up to 12 nautical miles."
        ),
        "keywords": ["maharashtra", "mechanized", "distance", "5 nautical miles", "5 nm", "trawler", "inshore", "purse seine", "ratnagiri", "mumbai"],
    },
    # ── Tamil Nadu ──
    {
        "source": "Tamil Nadu Marine Fishing Regulation Act, 1983 (Section 5)",
        "chunk": (
            "Inshore waters up to a distance of 3 nautical miles from the shoreline along the entire "
            "coast of Tamil Nadu are strictly reserved for fishing exclusively by traditional, "
            "non-mechanized crafts (kattumarams, vallams). Mechanized trawlers are prohibited within 3 NM "
            "and must adhere to the 3-day / 4-day fishing schedule."
        ),
        "keywords": ["tamil nadu", "3 nautical miles", "3 nm", "catamaran", "kattumaram", "traditional", "mechanized", "chennai", "rameswaram"],
    },
    # ── Kerala ──
    {
        "source": "Kerala Marine Fishing Regulation Act, 1980 (Sections 4 & 5)",
        "chunk": (
            "Under the Kerala Marine Fishing Regulation Act 1980, inshore waters up to 10 kilometres "
            "(approx 5.4 NM) are reserved for traditional non-motorized and artisanal fishermen. "
            "Night trawling is strictly prohibited between 9:00 PM and 6:00 AM off the coast of Kerala. "
            "Pair trawling and pelagic trawling by mechanized vessels are totally banned."
        ),
        "keywords": ["kerala", "10 km", "night trawling", "pair trawling", "artisanal", "traditional", "cochin", "kochi", "kollam"],
    },
    # ── Karnataka ──
    {
        "source": "Karnataka Marine Fishing Regulation Act, 1986",
        "chunk": (
            "Under Section 3 of the Karnataka MFRA 1986, mechanized fishing boats and deep sea trawlers "
            "are prohibited from operating within 6 kilometres (or 5 fathoms depth, whichever is greater) "
            "from the shore. Inshore waters are reserved for traditional country crafts and motorized canoes."
        ),
        "keywords": ["karnataka", "6 km", "5 fathoms", "mangalore", "karwar", "inshore", "mechanized", "traditional"],
    },
    # ── Goa ──
    {
        "source": "Goa, Daman and Diu Marine Fishing Regulation Rules, 1980",
        "chunk": (
            "Under the Goa Marine Fishing Regulation Rules 1980, the area up to 5 kilometres from the coast "
            "is reserved exclusively for traditional non-mechanized fishermen (Ramponkars). Mechanized trawlers "
            "and purse-seine vessels are barred from operating within this 5 km inshore zone."
        ),
        "keywords": ["goa", "5 km", "ramponkar", "inshore", "trawler", "panaji", "vasco", "traditional"],
    },
    # ── Gujarat ──
    {
        "source": "Gujarat Fisheries Act, 2003",
        "chunk": (
            "The Gujarat Fisheries Act 2003 reserves the territorial waters up to 5 nautical miles "
            "(or 9 kilometres) exclusively for small non-mechanized boats. Trawling in the sensitive "
            "gulf waters of Kutch and Khambhat is strictly regulated, with seasonal breeding zone closures."
        ),
        "keywords": ["gujarat", "5 nautical miles", "9 km", "kutch", "saurashtra", "porbandar", "veraval", "trawling"],
    },
    # ── Odisha ──
    {
        "source": "Orissa Marine Fishing Regulation Act, 1982 & Rules 1983",
        "chunk": (
            "Mechanized fishing is prohibited within 5 kilometres of the Odisha coast. Furthermore, a 20 km "
            "offshore exclusion zone is enforced around the Gahirmatha Marine Sanctuary and river mouths "
            "(Dhamra, Devi, Rushikulya) from 1st November to 31st May to protect mass-nesting Olive Ridley turtles. "
            "All trawl nets must be fitted with Turtle Excluder Devices (TED)."
        ),
        "keywords": ["odisha", "orissa", "gahirmatha", "olive ridley", "turtle excluder", "ted", "5 km", "20 km", "paradeep"],
    },
    # ── Andhra Pradesh ──
    {
        "source": "Andhra Pradesh Marine Fishing (Regulation) Act, 1994",
        "chunk": (
            "Under the Andhra Pradesh Marine Fishing Regulation Act 1994, inshore waters up to 8 kilometres "
            "from the coast are reserved strictly for traditional non-mechanized craft. Mechanized vessels and "
            "motorized boats above 10 HP are banned within this 8 km coastal zone."
        ),
        "keywords": ["andhra pradesh", "8 km", "visakhapatnam", "kakinada", "non-mechanized", "traditional", "inshore"],
    },
    # ── West Bengal ──
    {
        "source": "West Bengal Marine Fishing Regulation Act, 1993",
        "chunk": (
            "Under the West Bengal MFRA 1993, waters up to 8 kilometres from the shoreline are reserved for "
            "non-mechanized traditional fishing vessels. Trawling within the Sundarbans Biosphere Reserve and "
            "estuarine waters is prohibited to protect mangrove nursery habitats."
        ),
        "keywords": ["west bengal", "8 km", "sundarbans", "digha", "estuarine", "mangrove", "mechanized ban"],
    },
    # ── National Monsoon Ban ──
    {
        "source": "DAHDF Notification — Uniform Monsoon Ban",
        "chunk": (
            "Fishing by mechanized and motorized fishing vessels is strictly prohibited in the "
            "Indian Exclusive Economic Zone along the West Coast (Gujarat, Maharashtra, Goa, Karnataka, Kerala) "
            "from 1st June to 31st July (61 days). On the East Coast (WB, Odisha, AP, TN), "
            "the ban operates from 15th April to 14th June (61 days). Traditional non-motorized craft are exempt."
        ),
        "keywords": ["monsoon ban", "west coast", "east coast", "june", "july", "april", "annual ban", "dates", "closed season", "61 days"],
    },
    # ── Wildlife Protection ──
    {
        "source": "Wildlife Protection Act 1972, Schedule I",
        "chunk": (
            "Sea turtles (Olive Ridley, Green turtle), Dugongs (sea cows), and Whale Sharks are "
            "listed under Schedule I with absolute protection. Any accidental capture in fishing "
            "gear must be immediately released unharmed and reported to the forest/fisheries range office. "
            "Violations carry 3 to 7 years imprisonment."
        ),
        "keywords": ["turtle", "olive ridley", "dugong", "whale shark", "protected species", "bycatch", "coral", "schedule i"],
    },
    # ── Foreign Fishing Vessels ──
    {
        "source": "Maritime Zones of India (Regulation of Fishing by Foreign Vessels) Act, 1981",
        "chunk": (
            "No foreign fishing vessel shall be used for fishing within any maritime zone of India except "
            "under and in accordance with a licence granted by the Central Government. Unauthorised foreign vessels "
            "are liable to immediate seizure, confiscation, and heavy monetary penalties under Section 13."
        ),
        "keywords": ["foreign vessels", "foreign fishing", "maritime zones", "permit", "licence", "unauthorised", "seizure", "eez"],
    },
    # ── INCOIS & IMD Safety Guidelines ──
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

# Lexical indicative translation keywords for cross-lingual query retrieval
INDIC_TERM_MAP: dict[str, str] = {
    "बंदी": "ban monsoon",
    "कधी": "when dates period",
    "मासेमारी": "fishing regulation act",
    "मछली": "fishing marine",
    "ट्रॉलर": "trawler mechanized vessel",
    "महाराष्ट्र": "maharashtra",
    "केरळ": "kerala",
    "केरल": "kerala",
    "कर्नाटक": "karnataka",
    "तामिळनाडू": "tamil nadu",
    "तामिलनाडु": "tamil nadu",
    "गोवा": "goa",
    "गुजरात": "gujarat",
    "ओडिशा": "odisha orissa",
    "अंतर": "distance nautical miles",
    "नियम": "regulation act section",
    "कासव": "turtle olive ridley",
    "कछुआ": "turtle olive ridley",
    "व्हेल": "whale shark",
    "विदेशी": "foreign vessel maritime zone",
}


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
                base_data = Path(__file__).resolve().parent.parent.parent / "data"
                processor = DocumentProcessor()
                all_chunks: list[DocumentChunk] = []

                # 1. Always prepare baseline statutory corpus (9 states + national laws)
                for idx, c in enumerate(CORPUS, 1):
                    all_chunks.append(
                        DocumentChunk(
                            chunk_id=f"statutory_corpus::c{idx}",
                            source=c["source"],
                            chunk=c["chunk"],
                            section=c["source"],
                            keywords=c.get("keywords", []),
                            page_number=1,
                            metadata={"type": "statutory_baseline"},
                        )
                    )

                # 2. If vector store has fewer records than base corpus, ingest full documents and seed
                if self.vector_store.count() < len(CORPUS):
                    for folder_name in ["rag_documents", "rag_data"]:
                        docs_dir = base_data / folder_name
                        if docs_dir.exists():
                            doc_chunks = processor.process_directory(docs_dir)
                            all_chunks.extend(doc_chunks)

                    if all_chunks:
                        self.vector_store.add_chunks(all_chunks)
                        logger.info(f"Loaded {len(all_chunks)} regulatory chunks into RAG vector store.")
                else:
                    # Keep baseline in memory cache for offline resilience
                    self.vector_store._memory_chunks.extend(all_chunks)
            except Exception as e:
                logger.warning(f"Could not initialize VectorStoreManager: {e}. Using statutory CORPUS.")
                self.vector_store = None

    def _augment_cross_lingual_query(self, query: str) -> str:
        """Enrich Indic queries with legal terminology for high semantic recall against English gazettes."""
        q_lower = query.lower()
        extra_terms = []
        for indic_kw, english_equiv in INDIC_TERM_MAP.items():
            if indic_kw in q_lower:
                extra_terms.append(english_equiv)

        if extra_terms:
            return f"{query} {' '.join(extra_terms)}"
        return query

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
                "metadata": dict,
            }
        """
        t0 = time.monotonic()
        q_clean = question.strip()
        if not q_clean:
            return {
                "agent": "rag_advisory",
                "query_run_id": query_run_id,
                "answer": "Please ask a question regarding marine fishing regulations, zones, or safety advisories.",
                "citations": [],
                "confidence": 0.0,
                "source": "RAG Advisory Agent",
                "metadata": {"latency_ms": 0},
            }

        # 1. Detect query language (Hindi, Marathi, English)
        lang = detect_language(q_clean)
        search_query = self._augment_cross_lingual_query(q_clean)

        # 2. Retrieve top-k relevant chunks
        t_retrieval_start = time.monotonic()
        relevant_chunks: list[dict[str, Any]] = []

        if self.vector_store is not None:
            try:
                relevant_chunks = self.vector_store.search(search_query, top_k=3)
            except Exception as e:
                logger.warning(f"Vector search failed ({e}), falling back to statutory corpus.")

        if not relevant_chunks:
            # Fallback to statutory CORPUS keyword matching
            sq_lower = search_query.lower()
            scored = []
            for doc in CORPUS:
                score = sum(1 for kw in doc["keywords"] if kw in sq_lower)
                # Boost if state name is in query
                for state in ["maharashtra", "kerala", "tamil nadu", "karnataka", "goa", "gujarat", "odisha", "andhra", "bengal"]:
                    if state in sq_lower and state in doc["source"].lower():
                        score += 3
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

        retrieval_ms = round((time.monotonic() - t_retrieval_start) * 1000)

        # Format citations
        citations = [
            {
                "source": r.get("source", "Official Regulation"),
                "chunk": r.get("chunk", ""),
                "relevance_score": r.get("relevance_score", 0.85),
            }
            for r in relevant_chunks
        ]

        # 3. Grounded generation using LLM
        t_gen_start = time.monotonic()
        context_text = "\n---\n".join(
            f"Source: {c['source']}\nContent: {c['chunk']}" for c in citations
        )

        lang_instruction = ""
        if lang == "mr":
            lang_instruction = "IMPORTANT: The user asked in Marathi. Respond in clear, polite Marathi (मराठी) while preserving official Act titles and Section numbers."
        elif lang == "hi":
            lang_instruction = "IMPORTANT: The user asked in Hindi. Respond in clear, polite Hindi (हिंदी) while preserving official Act titles and Section numbers."

        prompt = (
            f"User Question: {q_clean}\n\n"
            f"Statutory Context:\n{context_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the question clearly and concisely using ONLY the provided Statutory Context.\n"
            "2. Always cite the specific Act, Section, or Notification name in your answer.\n"
            "3. If the context does not contain the answer, say: 'The official regulations in the database do not cover this specific question.'\n"
            "4. Do NOT invent regulations, penalties, or dates.\n"
            f"{lang_instruction}"
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
            top_source = citations[0]["source"] if citations else "Marine Regulations"
            top_content = citations[0]["chunk"] if citations else "No context available."
            answer = f"According to {top_source}: {top_content}"

        gen_ms = round((time.monotonic() - t_gen_start) * 1000)
        total_ms = round((time.monotonic() - t0) * 1000)

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
            "metadata": {
                "detected_language": lang,
                "retrieval_latency_ms": retrieval_ms,
                "generation_latency_ms": gen_ms,
                "total_latency_ms": total_ms,
                "citations_count": len(citations),
            },
        }
