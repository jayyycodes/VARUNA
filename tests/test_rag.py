"""
Tests for VARUNA RAG / Advisory Agent.
"""

import asyncio
from agents.rag_advisory.rag_agent import RAGAdvisoryAgent
from agents.rag_advisory.document_processor import DocumentProcessor
from agents.rag_advisory.vector_store import VectorStoreManager


def test_rag_agent_contract_shape():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("What is the monsoon ban?", query_run_id="test-run-123"))
    assert res["agent"] == "rag_advisory"
    assert res["query_run_id"] == "test-run-123"
    assert isinstance(res["answer"], str) and len(res["answer"]) > 0
    assert isinstance(res["citations"], list) and len(res["citations"]) > 0
    assert "confidence" in res
    assert "source" in res

    first_cite = res["citations"][0]
    assert "source" in first_cite
    assert "chunk" in first_cite
    assert "relevance_score" in first_cite


def test_rag_agent_monsoon_ban():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("When is the monsoon fishing ban on the west coast?"))
    assert any("DAHDF" in c["source"] or "Monsoon" in c["source"] for c in res["citations"])
    combined_text = (res["answer"] + " " + " ".join(c["chunk"] for c in res["citations"])).lower()
    assert "june" in combined_text or "61 days" in combined_text


def test_rag_agent_maharashtra_distance():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("How many nautical miles or fathoms are mechanized trawlers restricted in Maharashtra?"))
    assert any("Maharashtra" in c["source"] for c in res["citations"])
    combined_text = (res["answer"] + " " + " ".join(c["chunk"] for c in res["citations"])).lower()
    assert "5 nautical miles" in combined_text or "5 nm" in combined_text or "5 fathoms" in combined_text


def test_rag_agent_protected_wildlife():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("Are Olive Ridley turtles or whale sharks protected under Schedule I?"))
    assert any("Wildlife Protection Act" in c["source"] for c in res["citations"])
    combined_text = (res["answer"] + " " + " ".join(c["chunk"] for c in res["citations"])).lower()
    assert "turtle" in combined_text or "whale shark" in combined_text or "schedule i" in combined_text


def test_rag_agent_kerala_official_pdf():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("What does the Kerala Marine Fishing Regulation Act 1980 regulate?"))
    assert any("Kerala" in c["source"] for c in res["citations"])
    assert len(res["citations"]) > 0


def test_rag_agent_foreign_vessels_official_pdf():
    agent = RAGAdvisoryAgent(use_vector_store=True)
    res = asyncio.run(agent.answer_with_citations("Can foreign fishing vessels operate in the Indian maritime zone without a permit?"))
    assert any("Foreign Vessels" in c["source"] or "Maritime Zones" in c["source"] for c in res["citations"])
    assert len(res["citations"]) > 0


def test_document_processor():
    processor = DocumentProcessor(chunk_size=300)
    text = "Section 4: Regulation\n\nNo trawlers allowed within 5 nautical miles.\n\nSection 5: Traditional craft.\n\nReserved for non-mechanized."
    chunks = processor._chunk_content(text, source_name="Test MFRA", file_name="test.txt")
    assert len(chunks) >= 1
    assert any("5 nautical miles" in c.chunk for c in chunks)


def test_vector_store_memory_search():
    vs = VectorStoreManager()
    processor = DocumentProcessor()
    chunks = processor._chunk_content(
        "Trawlers are banned within 5 nautical miles in Maharashtra under Section 4.",
        source_name="Maharashtra Marine Fishing Regulation Act, 1981",
        file_name="mh.txt"
    )
    vs.add_chunks(chunks)
    results = vs.search("mechanized trawlers in Maharashtra")
    assert len(results) > 0
    assert "Maharashtra" in results[0]["source"]

