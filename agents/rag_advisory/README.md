# RAG / Statutory Advisory Agent
**Owner:** Prapti (Data Layer) + Jay / Adeey (Retrieval-Generation Loop)  
**Status:** Tier 2 Production Ready ✅ | Supabase pgvector Live & All Coastal States Ingested

## Responsibility
Answers coastal fishing regulations, maritime law, gear restrictions, and monsoon ban queries grounded strictly in government acts, state gazette notifications, and maritime orders with verifiable legal citations.

> [!IMPORTANT]
> **Strict Legal Grounding**: The LLM is strictly prohibited from inventing regulations, fine amounts, or boundary rules. Answers must cite specific Sections and Notification dates from authoritative legal texts.

---

## 1. MVP Tasks (Completed ✅)
- [x] **Core Statutory Corpus Ingested**:
  - *Maharashtra Marine Fishing Regulation Act (MFRA) 1981* (Section 4: 5 NM non-mechanized zone).
  - *Tamil Nadu Marine Fishing Regulation Act 1983* (Section 5: 3 NM traditional catamaran reserve).
  - *DAHDF Uniform Annual Monsoon Fishing Ban* (West Coast: June 1 – July 31; East Coast: April 15 – June 14).
  - *Wildlife Protection Act 1972 (Schedule I)*: Strict ban on capture of Olive Ridley Turtles, Dugongs, and Whale Sharks.
- [x] **Document Ingestion Engine**: Built document processor (`ingest.py`) with chunking and token scoring.
- [x] **Vector Search Engine**: Implemented vector retrieval and keyword density scoring in `vector_store.py`.
- [x] **Authoritative Citation Generation**: Emits full legal provenance (`title`, `publisher`, `section`, `excerpt`, `relevance_score`) rendered in the frontend Citations tab.
- [x] **Automated Test Suite**: Full test coverage in `tests/test_rag.py` passing cleanly.

---

## 2. Tier 2 Production Features (Completed ✅)
According to the root `README.md` (Sections 1.1, 3, 6, & 9), all Tier 2 priorities are complete:

- [x] **Comprehensive All-State MFRA Corpus Expansion**:
  - Ingested official statutory gazetteers for all 9 coastal states into Supabase `document_chunks` (177 total chunks):
    - *Kerala Marine Fishing Regulation Act 1980* (`ind1390.pdf`, `ind82115.pdf`)
    - *Gujarat Fisheries Act 2003* (`THE-GUJARAT-FISHERIES-ACT-2003.pdf`)
    - *Odisha Marine Fishing Regulation Act 1982 & Rules 1983* (`ind85258.pdf`, `ind85259.pdf`)
    - *Andhra Pradesh Marine Fishing Act 1994* (`ind22415.pdf`)
    - *Karnataka Marine Fishing Act 1986* (`ind63779.pdf`)
    - *Maharashtra Marine Fishing Regulation Act 1981 & Order 1983*
    - *Goa, Daman & Diu Marine Fishing Regulation Rules 1980* (`ind20041.pdf`)
    - *Tamil Nadu Marine Fishing Regulation Rules 1983* (`ind188851.pdf`)
    - *West Bengal Marine Fishing Regulation Act 1993* (`West Bengal Marine Fishing Regulation Act, 1993.pdf`)
    - *Maritime Zones of India Foreign Vessels Act 1981* (`IND171176.pdf`)
    - *Wildlife Protection Act 1972 Schedule I Marine Species* (`append1_0.pdf`, `8_Indiawildlifeprotectionactandtheoceans.pdf`)
- [x] **pgvector Migration**:
  - Migrated vector index to Supabase PostgreSQL 17.6 with `pgvector` and HNSW cosine similarity index (`idx_chunks_embedding USING hnsw (embedding vector_cosine_ops)`) with seamless offline fallback.
- [x] **Automated Retrieval & Faithfulness Evals**:
  - Implemented automated evaluation suite (`eval/rag_evals.py` and `tests/test_rag_evals.py`) measuring:
    - *Recall@3 / Hit Rate* (100% across all 10 coastal state benchmark queries)
    - *Context Groundedness* (strict citation provenance)
    - *Telemetry & Latency Tracing*
- [x] **Cross-Lingual Regulatory Retrieval**:
  - Query expansion and retrieval in Indic languages (Marathi, Hindi) with native language synthesis.
- [x] **Incremental Ingestion Hash Auditing**:
  - SHA-256 change detection in `DocumentProcessor.process_directory_incremental` to avoid duplicate re-indexing.

---

## 3. Tier 3 Roadmap (Post-Hackathon)
- [ ] **Automated Web Gazette Scraper & OCR Pipeline**:
  - Periodic crawler for newly issued DAHDF annual circulars and district collectorate safety orders.

---

## 3. Verification & Testing
Run automated RAG test suite:
```powershell
pytest tests/test_rag.py -v
```
Or run quick command-line query:
```powershell
python -c "import asyncio; from agents.rag_advisory.rag_agent import RAGAdvisoryAgent; r = RAGAdvisoryAgent(); res = asyncio.run(r.answer_with_citations('When is the monsoon fishing ban in Maharashtra?')); print(res['answer']); print('Citations:', len(res['citations']))"
```
