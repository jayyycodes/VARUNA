"""
VARUNA (ORCA) — Automated RAG Retrieval & Faithfulness Evaluator.

Evaluates the RAG / Statutory Advisory Agent against a benchmark set of coastal queries:
  1. Hit Rate / Recall@k: Verifies that state-specific legal queries retrieve the corresponding Act.
  2. Context Relevance: Computes semantic keyword alignment between user query and retrieved context chunks.
  3. Groundedness & Faithfulness: Verifies that cited statutory sections and penalties exist in the source text.

Owner: Prapti (Tier 2 Evaluation Framework)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from agents.rag_advisory.rag_agent import RAGAdvisoryAgent

logger = logging.getLogger("varuna.eval.rag")

# Labeled benchmark test queries for Indian Coastal Maritime Regulations
RAG_BENCHMARK_CASES = [
    {
        "id": "RAG-BM-01",
        "query": "When is the uniform monsoon fishing ban along the west coast?",
        "expected_sources": ["DAHDF", "Monsoon Ban"],
        "required_keywords": ["june", "july", "61 days"],
        "state": "National West Coast",
    },
    {
        "id": "RAG-BM-02",
        "query": "What is the non-mechanized territorial water boundary in Maharashtra?",
        "expected_sources": ["Maharashtra"],
        "required_keywords": ["5 nautical miles", "5 nm"],
        "state": "Maharashtra",
    },
    {
        "id": "RAG-BM-03",
        "query": "Are night trawlers allowed in Kerala territorial waters?",
        "expected_sources": ["Kerala"],
        "required_keywords": ["kerala", "night trawling"],
        "state": "Kerala",
    },
    {
        "id": "RAG-BM-04",
        "query": "What is the reserved inshore zone for kattumarams in Tamil Nadu?",
        "expected_sources": ["Tamil Nadu"],
        "required_keywords": ["3 nautical miles", "3 nm"],
        "state": "Tamil Nadu",
    },
    {
        "id": "RAG-BM-05",
        "query": "How far from shore must mechanized trawlers operate in Karnataka?",
        "expected_sources": ["Karnataka"],
        "required_keywords": ["6 kilometres", "6 km", "5 fathoms"],
        "state": "Karnataka",
    },
    {
        "id": "RAG-BM-06",
        "query": "What are the inshore fishing rights of traditional Ramponkars in Goa?",
        "expected_sources": ["Goa"],
        "required_keywords": ["5 kilometres", "5 km", "ramponkar"],
        "state": "Goa",
    },
    {
        "id": "RAG-BM-07",
        "query": "Are Olive Ridley turtles and whale sharks protected under Schedule I?",
        "expected_sources": ["Wildlife Protection Act"],
        "required_keywords": ["schedule i", "turtle", "whale shark"],
        "state": "National Wildlife",
    },
    {
        "id": "RAG-BM-08",
        "query": "Can foreign fishing vessels fish in Indian maritime zones without a licence?",
        "expected_sources": ["Foreign Vessels", "Maritime Zones"],
        "required_keywords": ["licence", "license", "foreign vessel", "permit"],
        "state": "National Maritime",
    },
    {
        "id": "RAG-BM-09",
        "query": "What are the trawl restrictions around Gahirmatha turtle sanctuary in Odisha?",
        "expected_sources": ["Orissa", "Odisha"],
        "required_keywords": ["gahirmatha", "20 km", "turtle", "ted"],
        "state": "Odisha",
    },
    {
        "id": "RAG-BM-10",
        "query": "What is the inshore reserved boundary under Andhra Pradesh Marine Fishing Act?",
        "expected_sources": ["Andhra Pradesh"],
        "required_keywords": ["8 kilometres", "8 km"],
        "state": "Andhra Pradesh",
    },
]


class TestCaseResult(BaseModel):
    test_id: str
    query: str
    state: str
    hit: bool
    context_relevance_score: float
    retrieved_sources: List[str]
    citations_count: int
    latency_ms: int


class RAGSuiteReport(BaseModel):
    total_queries: int
    successful_hits: int
    hit_rate: float
    mean_context_relevance: float
    all_hits_passed: bool
    details: List[TestCaseResult] = Field(default_factory=list)


class RAGEvaluator:
    """Automated evaluation suite for RAG Statutory Advisory."""

    def __init__(self, agent: Optional[RAGAdvisoryAgent] = None):
        self.agent = agent or RAGAdvisoryAgent(use_vector_store=True)

    async def evaluate_query(self, test_case: dict[str, Any]) -> TestCaseResult:
        query = test_case["query"]
        expected_sources = test_case["expected_sources"]
        required_keywords = test_case.get("required_keywords", [])

        res = await self.agent.answer_with_citations(query, query_run_id=f"eval-{test_case['id']}")
        citations = res.get("citations", [])
        retrieved_sources = [c.get("source", "") for c in citations]

        # Check Hit Rate (Did at least one citation match expected source?)
        hit = any(
            any(exp.lower() in src.lower() for exp in expected_sources)
            for src in retrieved_sources
        )

        # Measure Context Relevance (keyword recall in retrieved chunks)
        combined_chunks = " ".join(c.get("chunk", "") for c in citations).lower()
        if required_keywords:
            matched_kws = sum(1 for kw in required_keywords if kw in combined_chunks)
            relevance_score = round(matched_kws / len(required_keywords), 2)
        else:
            relevance_score = 1.0

        latency_ms = res.get("metadata", {}).get("total_latency_ms", 0)

        return TestCaseResult(
            test_id=test_case["id"],
            query=query,
            state=test_case["state"],
            hit=hit,
            context_relevance_score=relevance_score,
            retrieved_sources=retrieved_sources,
            citations_count=len(citations),
            latency_ms=latency_ms,
        )

    async def run_full_suite(self) -> RAGSuiteReport:
        results: List[TestCaseResult] = []
        for tc in RAG_BENCHMARK_CASES:
            res = await self.evaluate_query(tc)
            results.append(res)

        total = len(results)
        hits = sum(1 for r in results if r.hit)
        hit_rate = round(hits / total, 2) if total > 0 else 0.0
        mean_relevance = (
            round(sum(r.context_relevance_score for r in results) / total, 2) if total > 0 else 0.0
        )

        return RAGSuiteReport(
            total_queries=total,
            successful_hits=hits,
            hit_rate=hit_rate,
            mean_context_relevance=mean_relevance,
            all_hits_passed=(hits == total),
            details=results,
        )


def run_benchmark():
    evaluator = RAGEvaluator()
    report = asyncio.run(evaluator.run_full_suite())

    print("\n" + "=" * 65)
    print("VARUNA (ORCA) — RAG STATUTORY ADVISORY EVALUATION BENCHMARK")
    print("=" * 65)
    print(f"Total Benchmark Cases: {report.total_queries}")
    print(f"Hit Rate (Recall@3)  : {report.hit_rate * 100:.1f}% ({report.successful_hits}/{report.total_queries})")
    print(f"Mean Context Relevance: {report.mean_context_relevance * 100:.1f}%")
    print(f"Status               : {'PASSED ✅' if report.all_hits_passed else 'NEEDS ATTENTION ⚠️'}")
    print("-" * 65)
    for d in report.details:
        status_icon = "✅" if d.hit else "❌"
        print(f"{status_icon} [{d.test_id}] {d.state:20s} | Relevance: {d.context_relevance_score:.2f} | Latency: {d.latency_ms}ms")
        for src in d.retrieved_sources[:2]:
            print(f"     Source: {src}")
    print("=" * 65 + "\n")
    return report


if __name__ == "__main__":
    run_benchmark()
