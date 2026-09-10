"""
Vector Store Manager for VARUNA RAG / Advisory Agent.

Supports:
1. ChromaDB persistence with BGE embeddings (BAAI/bge-base-en-v1.5 or sentence-transformers)
2. In-memory semantic/keyword ranking fallback for fast zero-dependency operation
"""

from dataclasses import asdict
import logging
from pathlib import Path
import re
from typing import Any

from agents.rag_advisory.document_processor import DocumentChunk

logger = logging.getLogger("varuna.rag.vector_store")


class VectorStoreManager:
    """Manages document embeddings and similarity search."""

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
        self._memory_chunks: list[DocumentChunk] = []

        self._init_backend()

    def _init_backend(self):
        """Initialize ChromaDB if installed, otherwise prepare in-memory fallback."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            # Try loading BGE model via SentenceTransformerEmbeddingFunction
            try:
                self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model_name
                )
            except Exception as emb_err:
                logger.warning(
                    f"Could not load embedding model {self.embedding_model_name} ({emb_err}), "
                    "falling back to default embedding function."
                )
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
        """Add document chunks to vector store and in-memory cache."""
        if not chunks:
            return 0

        self._memory_chunks.extend(chunks)

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
        Search for most relevant chunks.
        Returns list of dicts with: source, chunk, relevance_score, metadata.
        """
        if not query.strip():
            return []

        # 1. Try ChromaDB semantic search
        if self._collection is not None:
            try:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(top_k, self._collection.count() or top_k),
                )
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    distances = results["distances"][0] if results.get("distances") else [0.2] * len(docs)

                    matched = []
                    for doc_text, meta, dist in zip(docs, metas, distances):
                        # Convert distance to normalized relevance score (higher is better)
                        score = max(0.5, round(1.0 - (dist / 2.0), 2)) if isinstance(dist, (int, float)) else 0.85
                        matched.append({
                            "source": meta.get("source", "Official Gazette"),
                            "chunk": doc_text,
                            "relevance_score": min(score, 0.98),
                            "metadata": meta,
                        })
                    return matched
            except Exception as e:
                logger.warning(f"ChromaDB search failed ({e}); falling back to memory ranker.")

        # 2. Fallback: In-memory keyword-density / lexical ranker
        return self._search_memory(query, top_k=top_k)

    def _search_memory(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self._memory_chunks:
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[float, DocumentChunk]] = []

        for chunk in self._memory_chunks:
            chunk_tokens = set(re.findall(r"\w+", chunk.chunk.lower()))
            overlap = query_tokens.intersection(chunk_tokens)
            
            # Boost score for matches in keywords or source title
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

        # If no keywords matched, return the top default chunk
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
        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._memory_chunks)
