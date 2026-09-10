"""
Ingestion script for VARUNA RAG / Advisory Agent.

Loads statutory documents from `data/rag_documents/` (and any provided PDFs),
splits them into clean chunks, and indexes them into ChromaDB / VectorStoreManager.

Usage:
    python -m agents.rag_advisory.ingest
    python -m agents.rag_advisory.ingest --docs data/rag_documents
"""

import argparse
import logging
from pathlib import Path
import sys

# Ensure root dir is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.rag_advisory.document_processor import DocumentProcessor
from agents.rag_advisory.vector_store import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-5s  %(message)s")
logger = logging.getLogger("varuna.rag.ingest")


def run_ingest(docs_dir: Path | None = None) -> int:
    target_dirs = [docs_dir] if docs_dir is not None else [
        ROOT_DIR / "data" / "rag_documents",
        ROOT_DIR / "data" / "rag_data",
    ]

    processor = DocumentProcessor(chunk_size=350, overlap=50)
    all_chunks = []

    for d in target_dirs:
        if d.exists():
            logger.info(f"Scanning documents in {d}...")
            chunks = processor.process_directory(d)
            all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No valid documents found in specified directories.")
        return 0

    logger.info(f"Generated {len(all_chunks)} document chunks.")
    vector_store = VectorStoreManager()
    indexed_count = vector_store.add_chunks(all_chunks)
    logger.info(f"Successfully indexed {indexed_count} chunks into vector store.")
    return indexed_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest regulatory documents into VARUNA RAG")
    parser.add_argument("--docs", type=str, default=None, help="Path to documents folder")
    args = parser.parse_args()

    target_dir = Path(args.docs) if args.docs else None
    run_ingest(target_dir)
