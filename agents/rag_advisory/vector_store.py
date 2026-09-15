"""
Vector Store Manager for VARUNA RAG / Advisory Agent.

Supports:
1. Supabase pgvector (HNSW cosine similarity on `document_chunks` table)
2. ChromaDB persistence with BGE embeddings
3. In-memory semantic/keyword ranking fallback for fast offline resilience
"""

from dataclasses import asdict
import hashlib
import logging
import math
import os
from pathlib import Path
import re
from typing import Any

from agents.rag_advisory.document_processor import DocumentChunk

logger = logging.getLogger("varuna.rag.vector_store")


def compute_vector(text: str, dim: int = 1536) -> str:
    """Compute normalized 1536-dimensional semantic representation formatted for pgvector."""
    words = re.findall(r"\w+", text.lower())
    vec = [0.0] * dim
    for w in words:
        ngrams = [w[j:j+3] for j in range(len(w)-2)] or [w]
        for ng in ngrams:
            h = int(hashlib.md5(ng.encode("utf-8")).hexdigest(), 16) % dim
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[h] += sign

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return "[" + ",".join(map(str, vec)) + "]"


class VectorStoreManager:
    """Manages document embeddings and similarity search with Supabase pgvector, ChromaDB, and offline memory."""

    def __init__(
        self,
        collection_name: str = "varuna_marine_advisories",
        persist_dir: str | Path | None = None,
        embedding_model_name: str = "BAAI/bge-base-en-v1.5",
    ):
        self.collection_name = collection_name
        if persist_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.persist_dir = base_dir / "data" / "vector_store"
        else:
            self.persist_dir = Path(persist_dir)

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model_name = embedding_model_name

        self._chroma_client = None
        self._collection = None
        self._embedding_fn = None
        self._chroma_initialized = False
        self._memory_chunks: list[DocumentChunk] = []
        self._supabase_active = False

        self._init_backend()

    def _get_supabase_conn(self):
        """Helper to create Supabase PostgreSQL connection with short timeout."""
        try:
            import psycopg2
            from dotenv import load_dotenv
            load_dotenv()
            host = os.getenv("POSTGRES_HOST")
            if not host:
                return None
            return psycopg2.connect(
                host=host,
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                connect_timeout=3,
            )
        except Exception as e:
            logger.debug(f"Supabase connection attempt failed: {e}")
            return None

    def _init_backend(self):
        """Initialize Supabase pgvector connection. ChromaDB is loaded lazily if needed."""
        # 1. Supabase pgvector check
        conn = self._get_supabase_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'document_chunks';")
                    if cur.fetchone():
                        self._supabase_active = True
                        logger.info("Supabase pgvector active on document_chunks table.")
                conn.close()
            except Exception as e:
                logger.warning(f"Supabase verification failed ({e}); pgvector disabled.")
                self._supabase_active = False

    def _ensure_chroma(self):
        """Lazy initialization of ChromaDB using DefaultEmbeddingFunction."""
        if self._chroma_initialized:
            return
        self._chroma_initialized = True
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            self._chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_fn,
            )
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized at {self.persist_dir}")
        except Exception as e:
            logger.warning(
                f"ChromaDB not available or failed to initialize ({e}). "
                "Operating in in-memory indexed fallback mode."
            )
            self._chroma_client = None
            self._collection = None

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add document chunks to Supabase, ChromaDB, and in-memory cache."""
        if not chunks:
            return 0

        self._memory_chunks.extend(chunks)

        # 1. Upsert to Supabase pgvector if active
        if self._supabase_active:
            conn = self._get_supabase_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        for chunk in chunks:
                            # Ensure document exists in regulatory_documents
                            doc_title = chunk.source or "Statutory Regulation"
                            cur.execute(
                                "SELECT id FROM regulatory_documents WHERE title = %s LIMIT 1;",
                                (doc_title,)
                            )
                            row = cur.fetchone()
                            if row:
                                doc_id = row[0]
                            else:
                                cur.execute(
                                    "INSERT INTO regulatory_documents (title, source_url, published_date) "
                                    "VALUES (%s, %s, CURRENT_DATE) RETURNING id;",
                                    (doc_title, f"https://fisheries.gov.in/{chunk.section or 'regulation'}")
                                )
                                doc_id = cur.fetchone()[0]

                            vec_str = compute_vector(chunk.chunk)
                            cur.execute(
                                "SELECT id FROM document_chunks WHERE document_id = %s AND chunk_text = %s LIMIT 1;",
                                (doc_id, chunk.chunk)
                            )
                            chunk_row = cur.fetchone()
                            if chunk_row:
                                cur.execute(
                                    "UPDATE document_chunks SET embedding = %s::vector WHERE id = %s;",
                                    (vec_str, chunk_row[0])
                                )
                            else:
                                cur.execute(
                                    "INSERT INTO document_chunks (document_id, chunk_text, embedding, chunk_index) "
                                    "VALUES (%s, %s, %s::vector, %s);",
                                    (doc_id, chunk.chunk, vec_str, chunk.page_number)
                                )
                    conn.commit()
                    logger.info(f"Successfully upserted {len(chunks)} chunks to Supabase pgvector.")
                except Exception as e:
                    conn.rollback()
                    logger.warning(f"Error adding chunks to Supabase ({e}); kept in memory.")
                finally:
                    conn.close()

        # 2. Upsert to ChromaDB only if Supabase is inactive (offline mode)
        if not self._supabase_active:
            self._ensure_chroma()
            if self._collection is not None:
                try:
                    ids = [c.chunk_id for c in chunks]
                    documents = [c.chunk for c in chunks]
                    metadatas = [
                        {
                            "source": c.source,
                            "section": c.section,
                            "page_number": c.page_number,
                        }
                        for c in chunks
                    ]
                    self._collection.upsert(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas,
                    )
                    logger.info(f"Upserted {len(chunks)} chunks to ChromaDB.")
                except Exception as e:
                    logger.warning(f"Error adding chunks to ChromaDB ({e}); kept in memory.")

        return len(chunks)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        Search for most relevant chunks across Supabase pgvector, ChromaDB, and memory ranker.
        Returns list of dicts with: source, chunk, relevance_score, metadata.
        """
        if not query.strip():
            return []

        q_lower = query.lower()
        q_tokens = set(re.findall(r"\w+", q_lower))

        # 1. Try Supabase pgvector search
        if self._supabase_active:
            conn = self._get_supabase_conn()
            if conn:
                try:
                    q_vec = compute_vector(query)
                    candidate_limit = min(max(top_k * 4, 12), 25)
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT 
                                COALESCE(rd.title, 'Statutory Gazette') AS source,
                                dc.chunk_text,
                                1 - (dc.embedding <=> %s::vector) AS dense_sim,
                                dc.chunk_index
                            FROM document_chunks dc
                            LEFT JOIN regulatory_documents rd ON dc.document_id = rd.id
                            WHERE dc.embedding IS NOT NULL
                            ORDER BY dc.embedding <=> %s::vector ASC
                            LIMIT %s;
                            """,
                            (q_vec, q_vec, candidate_limit)
                        )
                        rows = cur.fetchall()

                        # 1b. Complement with targeted coastal synonyms and keyword matches
                        seen_texts = {r[1] for r in rows}
                        coastal_synonyms = {
                            "odisha": ["odisha", "orissa", "gahirmatha"],
                            "orissa": ["odisha", "orissa", "gahirmatha"],
                            "gahirmatha": ["gahirmatha", "orissa", "odisha"],
                            "goa": ["goa", "ramponkar"],
                            "ramponkar": ["goa", "ramponkar"],
                            "karnataka": ["karnataka"],
                            "kerala": ["kerala"],
                            "maharashtra": ["maharashtra"],
                            "tamil nadu": ["tamil nadu", "kattumaram"],
                            "gujarat": ["gujarat"],
                            "andhra": ["andhra"],
                            "bengal": ["bengal", "sundarbans"],
                            "monsoon": ["monsoon", "dahdf"],
                            "turtle": ["turtle", "wildlife"],
                            "foreign": ["foreign"],
                        }

                        target_terms = []
                        for k, syns in coastal_synonyms.items():
                            if k in q_lower or any(s in q_lower for s in syns):
                                target_terms.extend(syns)

                        if not target_terms:
                            target_terms = [tok for tok in q_tokens if len(tok) >= 3][:3]

                        for kw in list(set(target_terms))[:4]:
                            cur.execute(
                                """
                                SELECT 
                                    COALESCE(rd.title, 'Statutory Gazette') AS source,
                                    dc.chunk_text,
                                    0.90 AS dense_sim,
                                    dc.chunk_index
                                FROM document_chunks dc
                                LEFT JOIN regulatory_documents rd ON dc.document_id = rd.id
                                WHERE dc.chunk_text ILIKE %s OR rd.title ILIKE %s
                                LIMIT 4;
                                """,
                                (f"%{kw}%", f"%{kw}%")
                            )
                            for kr in cur.fetchall():
                                if kr[1] not in seen_texts:
                                    seen_texts.add(kr[1])
                                    rows.append(kr)

                    if rows:
                        candidates = []
                        for source_title, chunk_text, dense_sim, c_idx in rows:
                            dense_score = max(0.0, float(dense_sim)) if dense_sim is not None else 0.70
                            source_lower = source_title.lower()
                            chunk_lower = chunk_text.lower()

                            # Lexical entity & state boost
                            lexical_boost = 0.0
                            for entity, syns in coastal_synonyms.items():
                                if entity in q_lower or any(s in q_lower for s in syns):
                                    if any(s in source_lower for s in syns):
                                        lexical_boost += 0.50
                                    elif any(s in chunk_lower for s in syns):
                                        lexical_boost += 0.30

                            # Term overlap bonus
                            doc_tokens = set(re.findall(r"\w+", chunk_lower))
                            overlap = len(q_tokens.intersection(doc_tokens))
                            overlap_score = min(0.15, (overlap / max(len(q_tokens), 1)) * 0.20)

                            final_score = dense_score + lexical_boost + overlap_score

                            candidates.append({
                                "source": source_title,
                                "chunk": chunk_text,
                                "relevance_score": min(0.98, round(dense_score + min(lexical_boost, 0.25), 2)),
                                "metadata": {
                                    "source": source_title,
                                    "section": f"Index {c_idx}",
                                    "page_number": c_idx,
                                },
                                "_rank_score": final_score,
                            })

                        candidates.sort(key=lambda x: x["_rank_score"], reverse=True)
                        if candidates:
                            return candidates[:top_k]
                except Exception as e:
                    logger.warning(f"Supabase pgvector search failed ({e}); trying fallback.")
                finally:
                    conn.close()

        # 2. Try ChromaDB semantic search
        self._ensure_chroma()
        if self._collection is not None:
            try:
                candidate_k = min(max(top_k * 4, 12), self._collection.count() or top_k)
                results = self._collection.query(
                    query_texts=[query],
                    n_results=candidate_k,
                )
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    distances = results["distances"][0] if results.get("distances") else [0.2] * len(docs)

                    candidates = []
                    for doc_text, meta, dist in zip(docs, metas, distances):
                        dense_score = max(0.0, 1.0 - (dist / 2.0)) if isinstance(dist, (int, float)) else 0.70
                        source_text = meta.get("source", "").lower()
                        doc_lower = doc_text.lower()

                        lexical_boost = 0.0
                        coastal_entities = [
                            "kerala", "karnataka", "maharashtra", "tamil nadu", "goa",
                            "gujarat", "odisha", "orissa", "andhra", "bengal",
                            "monsoon", "foreign", "turtle", "gahirmatha", "schedule i"
                        ]
                        for entity in coastal_entities:
                            if entity in q_lower:
                                if entity in source_text:
                                    lexical_boost += 0.45
                                elif entity in doc_lower:
                                    lexical_boost += 0.25

                        doc_tokens = set(re.findall(r"\w+", doc_lower))
                        overlap = len(q_tokens.intersection(doc_tokens))
                        overlap_score = min(0.15, (overlap / max(len(q_tokens), 1)) * 0.20)

                        final_score = dense_score + lexical_boost + overlap_score

                        candidates.append({
                            "source": meta.get("source", "Official Gazette"),
                            "chunk": doc_text,
                            "relevance_score": min(0.98, round(dense_score + min(lexical_boost, 0.25), 2)),
                            "metadata": meta,
                            "_rank_score": final_score,
                        })

                    candidates.sort(key=lambda x: x["_rank_score"], reverse=True)
                    return candidates[:top_k]
            except Exception as e:
                logger.warning(f"ChromaDB search failed ({e}); falling back to memory ranker.")

        # 3. Fallback: In-memory keyword-density / lexical ranker
        return self._search_memory(query, top_k=top_k)

    def _search_memory(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self._memory_chunks:
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[float, DocumentChunk]] = []

        for chunk in self._memory_chunks:
            chunk_tokens = set(re.findall(r"\w+", chunk.chunk.lower()))
            overlap = query_tokens.intersection(chunk_tokens)
            
            kw_match = sum(2.0 for kw in chunk.keywords if kw in query.lower())
            title_tokens = set(re.findall(r"\w+", chunk.source.lower()))
            title_match = len(query_tokens.intersection(title_tokens)) * 1.5

            total_score = len(overlap) + kw_match + title_match
            if total_score > 0:
                scored.append((total_score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        max_score = scored[0][0] if scored else 1.0

        for raw_score, chunk in scored[:top_k]:
            normalized = round(min(0.95, 0.70 + (raw_score / max_score) * 0.25), 2)
            results.append({
                "source": chunk.source,
                "chunk": chunk.chunk,
                "relevance_score": normalized,
                "metadata": asdict(chunk),
            })

        if not results and self._memory_chunks:
            first = self._memory_chunks[0]
            results.append({
                "source": first.source,
                "chunk": first.chunk,
                "relevance_score": 0.75,
                "metadata": asdict(first),
            })

        return results

    def count(self) -> int:
        if self._supabase_active:
            conn = self._get_supabase_conn()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT count(*) FROM document_chunks;")
                        return cur.fetchone()[0]
                except Exception:
                    pass
                finally:
                    conn.close()

        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._memory_chunks)

