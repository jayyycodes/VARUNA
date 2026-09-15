"""
Tests for Tier 2 RAG Features:
  1. Automated Benchmark Evaluation
  2. Cross-Lingual Regulatory Retrieval (Marathi, Hindi)
  3. Incremental Ingestion Hash Auditing
  4. Observability & Latency Telemetry
"""

import asyncio
from pathlib import Path
import pytest

from agents.rag_advisory.rag_agent import RAGAdvisoryAgent
from agents.rag_advisory.document_processor import DocumentProcessor
from eval.rag_evals import RAGEvaluator, RAG_BENCHMARK_CASES


def test_rag_benchmark_hit_rate():
    """Verify that the RAG benchmark achieves >= 90% Recall@3 across all coastal states."""
    evaluator = RAGEvaluator()
    report = asyncio.run(evaluator.run_full_suite())
    assert report.hit_rate >= 0.90, f"Expected hit rate >= 0.90, got {report.hit_rate}"
    assert report.successful_hits >= 9


def test_cross_lingual_marathi_retrieval():
    """Verify that a Marathi query retrieves Maharashtra MFRA citations."""
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("महाराष्ट्रात ट्रॉलर्ससाठी किती अंतराची बंदी आहे?"))
    assert res["agent"] == "rag_advisory"
    assert any("Maharashtra" in c["source"] for c in res["citations"])
    assert res["metadata"]["detected_language"] == "mr"
    assert len(res["citations"]) > 0


def test_cross_lingual_hindi_retrieval():
    """Verify that a Hindi query retrieves Kerala or Monsoon ban citations."""
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("केरल में मछली पकड़ने के क्या नियम हैं?"))
    assert res["agent"] == "rag_advisory"
    assert any("Kerala" in c["source"] for c in res["citations"])
    assert res["metadata"]["detected_language"] == "hi"


def test_incremental_ingestion_hashing(tmp_path):
    """Verify that DocumentProcessor detects unchanged files via SHA-256 and skips them."""
    test_file = tmp_path / "test_act.txt"
    test_file.write_text("Section 4: Reserved inshore zone up to 5 nautical miles.", encoding="utf-8")

    processor = DocumentProcessor()
    # First pass: new file
    new_chunks, manifest, skipped = processor.process_directory_incremental(tmp_path, manifest={})
    assert len(new_chunks) == 1
    assert len(skipped) == 0
    assert "test_act.txt" in manifest

    # Second pass: unchanged file
    new_chunks2, manifest2, skipped2 = processor.process_directory_incremental(tmp_path, manifest=manifest)
    assert len(new_chunks2) == 0
    assert len(skipped2) == 1
    assert "test_act.txt" in skipped2


def test_rag_latency_and_observability_telemetry():
    """Verify that RAG responses carry latency and telemetry metadata for observability."""
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("What is the uniform monsoon fishing ban?"))
    meta = res.get("metadata", {})
    assert "retrieval_latency_ms" in meta
    assert "generation_latency_ms" in meta
    assert "total_latency_ms" in meta
    assert "detected_language" in meta
    assert meta["total_latency_ms"] >= 0
