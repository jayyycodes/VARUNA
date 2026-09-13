"""
Ingestion script for VARUNA RAG / Advisory Agent.

Loads statutory documents from `data/rag_documents/` (and any provided PDFs),
splits them into clean chunks, and indexes them incrementally into ChromaDB.

Features:
  - SHA-256 hash auditing (skips unmodified files)
  - --force-rebuild flag to wipe and re-index from scratch
  - --status flag to show vector store collection stats

Usage:
    python -m agents.rag_advisory.ingest
    python -m agents.rag_advisory.ingest --force-rebuild
    python -m agents.rag_advisory.ingest --status
    python -m agents.rag_advisory.ingest --docs data/rag_documents
"""

import argparse
import json
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

MANIFEST_PATH = ROOT_DIR / "data" / "vector_store" / "manifest.json"


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_manifest(manifest: dict):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def get_status() -> dict:
    vector_store = VectorStoreManager()
    manifest = _load_manifest()
    total_docs = len(manifest)
    total_chunks = vector_store.count()
    status_info = {
        "collection_name": vector_store.collection_name,
        "total_chunks_indexed": total_chunks,
        "indexed_files_count": total_docs,
        "manifest_files": list(manifest.keys()),
        "persist_dir": str(vector_store.persist_dir),
    }
    return status_info


def run_ingest(docs_dir: Path | None = None, force_rebuild: bool = False) -> int:
    target_dirs = [docs_dir] if docs_dir is not None else [
        ROOT_DIR / "data" / "rag_documents",
        ROOT_DIR / "data" / "rag_data",
    ]

    vector_store = VectorStoreManager()
    manifest = {} if force_rebuild else _load_manifest()

    if force_rebuild:
        logger.info("Force rebuild requested: clearing existing ChromaDB collection...")
        if vector_store._collection is not None:
            try:
                vector_store._chroma_client.delete_collection(vector_store.collection_name)
                vector_store._init_backend()
                logger.info("Collection recreated cleanly.")
            except Exception as e:
                logger.warning(f"Failed to reset collection: {e}")

    processor = DocumentProcessor(chunk_size=350, overlap=50)
    all_new_chunks = []
    total_skipped = 0

    for d in target_dirs:
        if d.exists():
            logger.info(f"Scanning documents in {d}...")
            new_chunks, manifest, skipped = processor.process_directory_incremental(d, manifest)
            all_new_chunks.extend(new_chunks)
            total_skipped += len(skipped)
            if skipped:
                logger.info(f"Skipped {len(skipped)} unmodified files in {d.name} (SHA-256 match).")

    if not all_new_chunks:
        logger.info(f"All files up to date. ({total_skipped} files skipped, 0 new chunks needed).")
        return 0

    logger.info(f"Generated {len(all_new_chunks)} new/modified document chunks.")
    indexed_count = vector_store.add_chunks(all_new_chunks)
    _save_manifest(manifest)
    logger.info(f"Successfully indexed {indexed_count} chunks into vector store. Total chunks in store: {vector_store.count()}")
    return indexed_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest regulatory documents into VARUNA RAG")
    parser.add_argument("--docs", type=str, default=None, help="Path to documents folder")
    parser.add_argument("--force-rebuild", action="store_true", help="Wipe and rebuild vector store from scratch")
    parser.add_argument("--status", action="store_true", help="Print vector store status and exit")
    args = parser.parse_args()

    if args.status:
        st = get_status()
        print("\n=== VARUNA RAG Vector Store Status ===")
        print(f"Collection : {st['collection_name']}")
        print(f"Storage Dir: {st['persist_dir']}")
        print(f"Total Chunks: {st['total_chunks_indexed']}")
        print(f"Files Tracked: {st['indexed_files_count']}")
        for f in st["manifest_files"]:
            print(f"  • {f}")
        print("=======================================\n")
        sys.exit(0)

    target_dir = Path(args.docs) if args.docs else None
    run_ingest(target_dir, force_rebuild=args.force_rebuild)
