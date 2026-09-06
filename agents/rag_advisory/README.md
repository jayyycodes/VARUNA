# RAG / Advisory Agent
**Owner:** Prapti (data layer) — retrieval-generation loop wired in later by Jay/Adeey

## Responsibility
Answers "why is this restricted" / regulation questions from government
advisories, Marine Fishing Regulation Acts (MFRAs), and cyclone advisories,
with every claim grounded in a retrieved document.

## MVP Tasks — Prapti's scope (data layer)
- [ ] Collect PDFs: state-wise Marine Fishing Regulation Acts, PFZ advisory bulletins, cyclone advisories, disaster guidelines
- [ ] Chunk documents into reasonable passage sizes (~200-400 words per chunk)
- [ ] Generate embeddings for each chunk (use an embedding model — coordinate with Jay on which one)
- [ ] Load chunks + embeddings into the vector DB (Chroma or pgvector — see `document_chunks` table in DB schema)
- [ ] Write a basic retrieval test script: given a query, does it return the right chunk?

## MVP Tasks — retrieval-generation loop (Jay/Adeey, after data layer is ready)
- [ ] Build retrieval-then-generate flow: retrieve top-k chunks, generate answer grounded ONLY in retrieved text
- [ ] Enforce citation requirement: every claim in the response must trace to a specific retrieved chunk
- [ ] Reject/flag any generated sentence that can't be traced to a retrieved chunk

## Further Stage (Production)
- [ ] Retrieval eval: precision@k / recall@k against a labeled query→document test set
- [ ] Add more regional regulation sources as they're identified (state-specific fishing bans, seasonal closures)
- [ ] Re-embedding pipeline for when source documents are updated
- [ ] Multilingual retrieval (once the Language wrapper supports more than 2 languages)

## Interface Contract
Consumes: user question (text)
Produces: `{answer: str, citations: [{chunk_id, source_document, excerpt}]}`
