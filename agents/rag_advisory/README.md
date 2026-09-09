# RAG / Advisory Agent
**Owner:** Prapti (Data Layer) + Jay / Adeey (Retrieval-Generation Loop)

## Responsibility
Answers regulation, legal restriction, and policy questions (e.g. *"Can I use a purse seine net?"*, *"When is the monsoon fishing ban in Maharashtra?"*) grounded strictly in government acts and official gazetteers with verifiable citations.

---

## 1. Official Regulatory Document Corpus

All legal and advisory answers must ground into one of these statutory documents:

1. **Maharashtra Marine Fishing Regulation Act (MFRA) 1981**:
   - Section 4: Prohibition of mechanized fishing vessels within 5 nautical miles of the coastline.
2. **Tamil Nadu Marine Fishing Regulation Act 1983**:
   - Section 5: Reservation of inshore waters (within 3 nautical miles) exclusively for non-mechanized traditional catamarans and country craft.
3. **DAHDF Annual Monsoon Fishing Ban Notification (Govt. of India)**:
   - **West Coast (Arabian Sea)**: Total mechanized fishing ban annually from **June 1 to July 31** (61 days).
   - **East Coast (Bay of Bengal)**: Total mechanized fishing ban annually from **April 15 to June 14** (61 days).
4. **Wildlife Protection Act 1972 (Schedule I - Marine)**:
   - Absolute protection for Olive Ridley Sea Turtles, Dugongs (Sea Cows), Whale Sharks, and all species of Coral.

---

## 2. Copy-Paste Runnable Implementation

You can drop this directly into `agents/rag_advisory/rag_agent.py`:

```python
from backend.gateway.ai_gateway import call_llm

CORPUS = [
    {
        "source": "Maharashtra MFRA 1981, Section 4",
        "chunk": "No mechanized fishing vessel shall engage in fishing within the territorial waters measured from the baseline up to a distance of 5 nautical miles. Waters within 5 NM are reserved exclusively for non-mechanized traditional fishermen.",
        "keywords": ["maharashtra", "mechanized", "distance", "5 nautical miles", "trawler"]
    },
    {
        "source": "DAHDF Notification — Uniform Monsoon Ban",
        "chunk": "Fishing by mechanized and motorized fishing vessels is strictly prohibited in the Indian Exclusive Economic Zone along the West Coast (including Gujarat, Maharashtra, Goa, Karnataka, Kerala) from 1st June to 31st July (61 days) during the South-West Monsoon.",
        "keywords": ["monsoon ban", "west coast", "june", "july", "annual ban", "dates"]
    },
    {
        "source": "Wildlife Protection Act 1972, Schedule I",
        "chunk": "Sea turtles (Olive Ridley), Dugongs, and Whale Sharks are listed under Schedule I. Any accidental capture in fishing gear must be immediately freed and reported to the nearest forest/fisheries range office.",
        "keywords": ["turtle", "dugong", "whale shark", "protected species", "bycatch"]
    }
]

class RAGAdvisoryAgent:
    async def answer_with_citations(self, question: str) -> dict:
        q_lower = question.lower()
        
        # Keyword-density match (or vector DB embedding)
        scored_chunks = []
        for doc in CORPUS:
            score = sum(1 for kw in doc["keywords"] if kw in q_lower)
            if score > 0:
                scored_chunks.append((score, doc))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        relevant = [c[1] for c in scored_chunks[:2]] if scored_chunks else [CORPUS[0]]

        citations = [
            {
                "source": r["source"],
                "chunk": r["chunk"],
                "relevance_score": 0.90
            }
            for r in relevant
        ]

        # Grounded generation using LLM
        prompt = (
            f"Question: {question}\n\n"
            f"Context:\n" + "\n---\n".join(r['chunk'] for r in relevant) + "\n\n"
            "Answer the question concisely using ONLY the context provided above. Always cite the specific Act or Notification."
        )
        answer = await call_llm("rag", [{"role": "user", "content": prompt}])

        return {
            "agent": "rag_advisory",
            "answer": answer,
            "citations": citations,
            "confidence": 0.94
        }
```

---

## 3. How to Test Your Agent Locally

```powershell
python -c "import asyncio; from agents.rag_advisory.rag_agent import RAGAdvisoryAgent; r = RAGAdvisoryAgent(); res = asyncio.run(r.answer_with_citations('When is the monsoon fishing ban on the west coast?')); print(res['answer']); print(res['citations'])"
```
