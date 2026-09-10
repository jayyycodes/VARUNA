"""
Document Processor for VARUNA RAG / Advisory Agent.

Loads and chunks statutory documents (MFRAs, Government Gazetteers,
Monsoon Ban Notifications, Wildlife Protection Acts, INCOIS Advisories)
into retrieval-ready passages with full provenance metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    source: str
    chunk: str
    section: str = ""
    keywords: list[str] = field(default_factory=list)
    page_number: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """Extracts text and generates clean chunks with metadata."""

    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_file(self, file_path: str | Path) -> list[DocumentChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() == ".pdf":
            return self._load_pdf(path)
        elif path.suffix.lower() in [".txt", ".md"]:
            return self._load_text(path)
        else:
            # Fallback to plain text read
            return self._load_text(path)

    def _load_text(self, path: Path) -> list[DocumentChunk]:
        content = path.read_text(encoding="utf-8", errors="ignore")
        source_name = path.stem.replace("_", " ").title()
        return self._chunk_content(content, source_name=source_name, file_name=path.name)

    def _load_pdf(self, path: Path) -> list[DocumentChunk]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            chunks: list[DocumentChunk] = []
            source_name = path.stem.replace("_", " ").title()

            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    page_chunks = self._chunk_content(
                        text,
                        source_name=source_name,
                        file_name=path.name,
                        page_number=page_idx + 1,
                    )
                    chunks.extend(page_chunks)
            return chunks
        except ImportError:
            # If pypdf is unavailable, read as text fallback if possible
            return []

    def _chunk_content(
        self,
        content: str,
        source_name: str,
        file_name: str,
        page_number: int = 1,
    ) -> list[DocumentChunk]:
        """Split content into semantic sections or paragraph clusters."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks: list[DocumentChunk] = []

        current_text = ""
        current_section = ""
        chunk_idx = 1

        for p in paragraphs:
            # Check for statutory section headers like "Section 4:", "1. West Coast:", etc.
            header_match = re.match(r"^(Section\s+\d+|[0-9]+\.\s+[A-Za-z\s]+|Subject:)", p)
            if header_match:
                current_section = header_match.group(0).strip()

            if len(current_text) + len(p) > self.chunk_size * 4 and current_text:
                chunk_id = f"{file_name}::c{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source=f"{source_name}{', ' + current_section if current_section else ''}",
                        chunk=current_text.strip(),
                        section=current_section,
                        keywords=self._extract_keywords(current_text),
                        page_number=page_number,
                        metadata={"file_name": file_name, "chunk_idx": chunk_idx},
                    )
                )
                chunk_idx += 1
                current_text = p
            else:
                current_text = f"{current_text}\n\n{p}".strip() if current_text else p

        if current_text:
            chunk_id = f"{file_name}::c{chunk_idx}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source=f"{source_name}{', ' + current_section if current_section else ''}",
                    chunk=current_text.strip(),
                    section=current_section,
                    keywords=self._extract_keywords(current_text),
                    page_number=page_number,
                    metadata={"file_name": file_name, "chunk_idx": chunk_idx},
                )
            )

        return chunks

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract key marine terms and numbers for indexing."""
        sample_terms = [
            "maharashtra", "tamil nadu", "west coast", "east coast", "monsoon ban",
            "5 nautical miles", "3 nautical miles", "mechanized", "trawler", "inshore",
            "purse seine", "turtle", "olive ridley", "dugong", "whale shark",
            "coral", "june", "july", "april", "bycatch", "wave height", "cyclone",
            "incois", "imd", "safe", "caution", "unsafe", "squall"
        ]
        text_lower = text.lower()
        return [term for term in sample_terms if term in text_lower]

    def process_directory(self, dir_path: str | Path) -> list[DocumentChunk]:
        folder = Path(dir_path)
        if not folder.exists():
            return []

        all_chunks: list[DocumentChunk] = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".pdf", ".md"]:
                chunks = self.load_file(file_path)
                all_chunks.extend(chunks)

        return all_chunks
