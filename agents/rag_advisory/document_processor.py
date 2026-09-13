"""
Document Processor for VARUNA RAG / Advisory Agent.

Loads and chunks statutory documents (MFRAs, Government Gazetteers,
Monsoon Ban Notifications, Wildlife Protection Acts, INCOIS Advisories)
into retrieval-ready passages with full provenance metadata.
"""

from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import Any

logger = logging.getLogger("varuna.rag.document_processor")

OFFICIAL_DOCUMENT_NAMES: dict[str, str] = {
    "ind1390": "Kerala Marine Fishing Regulation Act, 1980",
    "ind169741": "Maharashtra Marine Fishing Regulation Order, 1983",
    "ind171176": "Maritime Zones of India (Regulation of Fishing by Foreign Vessels) Act, 1981",
    "ind188851": "Tamil Nadu Marine Fishing Regulation Rules, 1983",
    "ind20041": "Goa, Daman and Diu Marine Fishing Regulation Rules, 1980",
    "ind63779": "Karnataka Marine Fishing Regulation Act, 1986",
    "ind82115": "Kerala Marine Fishing Regulation (Amendment) Act, 1986",
    "ind85258": "Orissa Marine Fishing Regulation Rules, 1983",
    "ind85259": "Orissa Marine Fisheries Notification, 2005",
    "maharashtra_mfra_1981": "Maharashtra Marine Fishing Regulation Act, 1981",
    "dahdf_monsoon_ban_notification": "DAHDF Notification — Uniform Monsoon Ban",
    "wildlife_protection_act_marine_schedule1": "Wildlife Protection Act 1972, Schedule I",
    "incois_imd_marine_advisory_protocol": "INCOIS & IMD Marine Advisory Protocol",
}


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

    def _resolve_source_name(self, path: Path, text_preview: str = "") -> str:
        """Resolve canonical official legislative title from filename or gazette text."""
        stem_lower = path.stem.lower()
        if stem_lower in OFFICIAL_DOCUMENT_NAMES:
            return OFFICIAL_DOCUMENT_NAMES[stem_lower]

        for k, name in OFFICIAL_DOCUMENT_NAMES.items():
            if k in stem_lower:
                return name

        # Fallback to Title Cased filename
        return path.stem.replace("_", " ").title()

    def load_file(self, file_path: str | Path) -> list[DocumentChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() == ".pdf":
            return self._load_pdf(path)
        elif path.suffix.lower() in [".txt", ".md"]:
            return self._load_text(path)
        else:
            return self._load_text(path)

    def _load_text(self, path: Path) -> list[DocumentChunk]:
        content = path.read_text(encoding="utf-8", errors="ignore")
        source_name = self._resolve_source_name(path, text_preview=content[:200])
        return self._chunk_content(content, source_name=source_name, file_name=path.name)

    def _load_pdf(self, path: Path) -> list[DocumentChunk]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            chunks: list[DocumentChunk] = []
            preview_text = reader.pages[0].extract_text() if reader.pages else ""
            source_name = self._resolve_source_name(path, text_preview=preview_text)

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
        except Exception as e:
            logger.warning(f"Failed to read PDF {path.name}: {e}")
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
            # Check for statutory section headers
            header_match = re.match(r"^(Section\s+\d+|[0-9]+\.\s+[A-Za-z\s]+|Subject:|ORDER|CHAPTER\s+[IVX]+)", p)
            if header_match:
                current_section = header_match.group(0).strip()

            if len(current_text) + len(p) > self.chunk_size * 4 and current_text:
                chunk_id = f"{file_name}::p{page_number}_c{chunk_idx}"
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
            chunk_id = f"{file_name}::p{page_number}_c{chunk_idx}"
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
            "maharashtra", "tamil nadu", "kerala", "karnataka", "goa", "orissa", "odisha",
            "west coast", "east coast", "monsoon ban", "5 nautical miles", "3 nautical miles",
            "mechanized", "trawler", "inshore", "purse seine", "turtle", "olive ridley",
            "dugong", "whale shark", "coral", "june", "july", "april", "bycatch", "wave height",
            "cyclone", "incois", "imd", "safe", "caution", "unsafe", "squall", "foreign vessel",
            "licence", "license", "registration", "penalty", "fathoms", "prohibited", "traditional",
            "territorial waters", "exclusive economic zone", "eez", "schedule i"
        ]
        text_lower = text.lower()
        return [term for term in sample_terms if term in text_lower]

    @staticmethod
    def compute_file_hash(file_path: str | Path) -> str:
        """Compute SHA-256 checksum of a file for incremental change auditing."""
        import hashlib
        p = Path(file_path)
        if not p.exists():
            return ""
        sha = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def process_directory(self, dir_path: str | Path) -> list[DocumentChunk]:
        """Process all valid document files in a directory."""
        folder = Path(dir_path)
        if not folder.exists():
            return []

        all_chunks: list[DocumentChunk] = []
        for file_path in sorted(folder.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".pdf", ".md"]:
                chunks = self.load_file(file_path)
                all_chunks.extend(chunks)

        return all_chunks

    def process_directory_incremental(
        self,
        dir_path: str | Path,
        manifest: dict[str, Any] | None = None,
    ) -> tuple[list[DocumentChunk], dict[str, Any], list[str]]:
        """
        Incrementally process directory by comparing SHA-256 hashes.
        Returns:
            (new_or_modified_chunks, updated_manifest, skipped_files)
        """
        folder = Path(dir_path)
        if not folder.exists():
            return [], manifest or {}, []

        manifest = dict(manifest) if manifest else {}
        new_chunks: list[DocumentChunk] = []
        skipped_files: list[str] = []

        for file_path in sorted(folder.iterdir()):
            if not (file_path.is_file() and file_path.suffix.lower() in [".txt", ".pdf", ".md"]):
                continue

            current_hash = self.compute_file_hash(file_path)
            cached_entry = manifest.get(file_path.name, {})

            if cached_entry.get("sha256") == current_hash:
                skipped_files.append(file_path.name)
                continue

            # File is new or changed
            file_chunks = self.load_file(file_path)
            new_chunks.extend(file_chunks)
            manifest[file_path.name] = {
                "sha256": current_hash,
                "size_bytes": file_path.stat().st_size,
                "chunks_count": len(file_chunks),
            }

        return new_chunks, manifest, skipped_files
