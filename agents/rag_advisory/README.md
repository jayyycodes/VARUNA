# RAG / Statutory Advisory Agent
**Owner:** Prapti (Data Layer) + Jay / Adeey (Retrieval-Generation Loop)  
**Status:** MVP Complete ✅ | Next Phase: All Coastal States Corpus & pgvector Migration

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

## 2. Post-MVP & Production Tasks (Current Focus)
According to the root `README.md` (Sections 1.1, 3, 6, & 9), the next operational priorities are:

- [ ] **Comprehensive All-State MFRA Corpus Expansion**:
  - Ingest statutory gazetteers for all 9 coastal states and 4 union territories:
    - *Kerala Marine Fishing Regulation Act 1980*
    - *Gujarat Fisheries Act 2003*
    - *Odisha Marine Fishing Regulation Act 1982*
    - *Andhra Pradesh Marine Fishing Act 1994*
    - *Karnataka Marine Fishing Act 1986*
- [ ] **Automated Gazette Scraper & OCR Pipeline**:
  - Build automated ingestion for new DAHDF (Dept. of Fisheries) annual circulars and district collectorate safety orders.
- [ ] **pgvector Migration**:
  - Migrate in-memory index to Supabase PostgreSQL with `pgvector` and HNSW indexing for persistent semantic search.
- [ ] **Automated Retrieval & Faithfulness Evals (RAGAS)**:
  - Implement RAG evaluation suite measuring:
    - *Context Relevance* (> 0.85)
    - *Faithfulness* (1.0 — zero ungrounded claims)
    - *Answer Relevance* (> 0.90)
- [ ] **Cross-Lingual Regulatory Retrieval**:
  - Enable fishermen to query in Marathi, Tamil, Bengali, or Hindi and retrieve relevant English statutory gazettes with native language synthesis.

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
