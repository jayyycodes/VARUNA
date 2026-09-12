"""
Multilingual Gateway for VARUNA (ORCA)
Supports Hindi (हिंदी) and Marathi (मराठी) along with English.

Handles:
  1. Language identification (Devanagari script detection + vocabulary heuristics)
  2. Inbound translation (Indic -> English) for clean agent dispatch
  3. Outbound translation (English -> Indic) preserving markdown, safety verdicts,
     and deterministic numeric measurements.
"""

from __future__ import annotations

import re
import logging
from typing import Tuple
from backend.gateway.ai_gateway import call_llm

logger = logging.getLogger("varuna.multilingual")

# Devanagari Unicode Block: U+0900 to U+097F
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")

# Characteristic Marathi lexical patterns
MARATHI_KEYWORDS = [
    "आहे का", "कधी", "हवामान", "मासेमारी", "जाऊ शकतो", "जाऊ शकते",
    "सुरक्षित आहे का", "लाटा", "वारा", "सांगा", "माहिती", "कसे",
    "किती", "मदत", "किनारा", "बंदर", "पाऊस", "सावधानता"
]

# Characteristic Hindi lexical patterns
HINDI_KEYWORDS = [
    "क्या", "कब", "मौसम", "मछली", "पकड़ना", "जा सकते हैं", "जा सकता हूँ",
    "सुरक्षित है", "लहरें", "हवा", "बताओ", "जानकारी", "कैसे",
    "कितना", "मदद", "तट", "बारिश", "चेतावनी"
]


def detect_language(text: str) -> str:
    """
    Detects whether the input text is English ('en'), Hindi ('hi'), or Marathi ('mr').
    Uses Devanagari detection and vocabulary scoring.
    """
    if not text or not text.strip():
        return "en"

    # Count Devanagari characters
    devanagari_chars = len(DEVANAGARI_REGEX.findall(text))
    total_chars = len(text.strip())

    if devanagari_chars > 0 and (devanagari_chars / max(total_chars, 1)) > 0.15:
        # It is in Devanagari script
        text_lower = text.strip()
        marathi_score = sum(1 for kw in MARATHI_KEYWORDS if kw in text_lower)
        hindi_score = sum(1 for kw in HINDI_KEYWORDS if kw in text_lower)

        if marathi_score > hindi_score:
            return "mr"
        elif hindi_score > marathi_score:
            return "hi"
        else:
            # Fallback to Hindi if ambiguous Devanagari
            return "hi"

    # Check for Romanized / Latin script Indic phrases (e.g. "kya ratnagiri safe hai")
    lower = text.lower()
    if any(term in lower for term in ["kya", "shakto ka", "aahe ka", "machli", "mausam", "surakshit"]):
        if any(term in lower for term in ["aahe ka", "shakto ka", "sang"]):
            return "mr"
        return "hi"

    return "en"


async def translate_in(query: str) -> Tuple[str, str]:
    """
    Translates an incoming query into English if it is in an Indic language.
    Returns: (english_query, detected_language)
    """
    lang = detect_language(query)
    if lang == "en":
        return query, "en"

    lang_name = "Marathi" if lang == "mr" else "Hindi"
    prompt = (
        f"You are a specialized maritime translation engine for Indian fishermen and coastal authorities.\n"
        f"Translate the following {lang_name} user query into clear, concise English for maritime safety processing.\n"
        f"Maintain coastal location names (e.g., Ratnagiri, Malvan, Mumbai, Kochi, Visakhapatnam), distances, and temporal words ('tomorrow', 'today') accurately.\n"
        f"Return ONLY the plain English translation, with no explanation or conversational filler.\n\n"
        f"Query: {query}"
    )

    try:
        translated = await call_llm("intent", [{"role": "user", "content": prompt}], temperature=0.0)
        clean_text = translated.strip().strip('"').strip("'")
        logger.info(f"[multilingual] Translated IN ({lang} -> en): '{query}' -> '{clean_text}'")
        return clean_text, lang
    except Exception as err:
        logger.warning(f"[multilingual] translate_in failed ({err}), falling back to transliteration dictionary.")
        fallback_query = query
        _INDIC_FALLBACK_MAP = {
            "रत्नागिरीच्या": "Ratnagiri",
            "रत्नागिरी": "Ratnagiri",
            "मालवणला": "Malvan",
            "मालवण": "Malvan",
            "मुंबईच्या": "Mumbai",
            "मुंबई": "Mumbai",
            "कोची": "Kochi",
            "कोच्चि": "Kochi",
            "गोवा": "Goa",
            "मौसम": "weather",
            "हवामान": "weather",
            "सुरक्षित": "safe",
            "मछली": "fishing",
            "उद्या": "tomorrow",
            "कल": "tomorrow",
            "लाटा": "waves",
            "समुद्र": "sea",
        }
        for k, v in _INDIC_FALLBACK_MAP.items():
            fallback_query = fallback_query.replace(k, v)
        return fallback_query, lang


async def translate_out(response_text: str, target_lang: str) -> str:
    """
    Translates an English maritime intelligence summary into the target Indic language (Hindi / Marathi).
    Strictly preserves:
      - Markdown bolding and headers (**SAFE**, **CAUTION**, **UNSAFE**)
      - Technical telemetry numbers (e.g. '1.2 m', '14 knots', '28.6°C', '106 km', '57.3 NM', '7.2 hrs', '126 L')
      - Statutory citation references (e.g. Maharashtra MFRA 1981)
    """
    if target_lang == "en" or not response_text:
        return response_text

    lang_name = "Marathi (मराठी)" if target_lang == "mr" else "Hindi (हिंदी)"

    system_msg = (
        f"You are an expert translator specializing in Indian maritime weather and coastal fishing advisories.\n"
        f"Translate the provided maritime intelligence report into fluent, natural {lang_name}.\n\n"
        f"STRICT SAFETY & NUMERICAL RULES:\n"
        f"1. Preserve safety verdict tokens: **UNSAFE** (असुरक्षित), **CAUTION** (सावधान), **SAFE** (सुरक्षित).\n"
        f"2. Keep exact numeric values and units untouched (e.g., '1.2 m', '14 knots', '28.6°C', '0.58 mg/m³', '106 km', '57.3 NM', '7.2 hrs', '126 L').\n"
        f"3. Keep port names familiar (Ratnagiri, Malvan, Mumbai, Kochi, etc.).\n"
        f"4. Preserve markdown layout, bullet points, and citation names.\n"
        f"5. Return ONLY the translated markdown text."
    )

    try:
        translated = await call_llm(
            "synthesizer",
            [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": response_text},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        logger.info(f"[multilingual] Translated OUT (en -> {target_lang}) successfully.")
        return translated.strip()
    except Exception as err:
        logger.error(f"[multilingual] translate_out failed ({err}), returning original English.")
        return response_text
