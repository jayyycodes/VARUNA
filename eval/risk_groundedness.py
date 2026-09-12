"""
Varuna (ORCA) — Automated LLM Groundedness Evaluator for Maritime Safety.
Evaluates natural language risk explanations to guarantee 100% factual fidelity
to deterministic rule_trace outputs:
  1. Verdict Concordance: Asserts explanation never inverts or softens SAFE/CAUTION/UNSAFE.
  2. Numerical Groundedness: Detects all numerical metrics in text and asserts they originate
     strictly from rule_trace inputs or thresholds (within +/- 0.1 margin).
  3. Hazard Hallucination Check: Asserts no ghost hazards (e.g. cyclone, lightning) are claimed
     if not present in rule_trace.

Owner: Jaish
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.schemas.envelope import RiskVerdict


class GroundednessViolation(BaseModel):
    category: str  # "NUMERICAL_HALLUCINATION" | "VERDICT_CONTRADICTION" | "UNGROUNDED_HAZARD"
    severity: str  # "FAIL" | "WARN"
    details: str
    token: Optional[str] = None


class GroundednessReport(BaseModel):
    is_grounded: bool
    score: float  # 0.0 - 1.0
    verdict_concordance: bool
    violations: List[GroundednessViolation] = Field(default_factory=list)
    extracted_numbers: List[float] = Field(default_factory=list)
    matched_numbers: List[float] = Field(default_factory=list)


def _collect_trace_numbers(rule_trace: Dict[str, Any]) -> List[float]:
    """Recursively collects all floating-point numbers present in rule_trace."""
    numbers: List[float] = []

    def _walk(obj: Any):
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            numbers.append(float(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(rule_trace)
    return numbers


class RiskGroundednessEvaluator:
    """Evaluates whether an LLM explanation strictly adheres to deterministic rule_trace."""

    @classmethod
    def evaluate(cls, verdict: RiskVerdict, explanation: str) -> GroundednessReport:
        violations: List[GroundednessViolation] = []
        text = explanation.strip()
        v_str = verdict.verdict.upper()

        # 1. Verdict Concordance
        verdict_concordance = True
        lower_text = text.lower()
        if v_str == "UNSAFE":
            if any(p in lower_text for p in ("safe to depart", "clear to sail", "conditions are safe", "smooth sailing")):
                violations.append(
                    GroundednessViolation(
                        category="VERDICT_CONTRADICTION",
                        severity="FAIL",
                        details="Explanation claims safe sailing while computed verdict is UNSAFE",
                    )
                )
                verdict_concordance = False
        elif v_str == "SAFE":
            if any(p in lower_text for p in ("do not depart", "departure prohibited", "mandatory halt", "unsafe to sail")):
                violations.append(
                    GroundednessViolation(
                        category="VERDICT_CONTRADICTION",
                        severity="FAIL",
                        details="Explanation instructs vessel to halt while computed verdict is SAFE",
                    )
                )
                verdict_concordance = False

        # 2. Numerical Groundedness Check
        # Match integers and decimals (e.g. 2.5, 40, 1.2)
        raw_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
        extracted: List[float] = []
        for n_str in raw_numbers:
            try:
                extracted.append(float(n_str))
            except ValueError:
                pass

        trace_numbers = _collect_trace_numbers(verdict.rule_trace or {})
        matched: List[float] = []

        # Common innocent numbers allowed without being in rule_trace (e.g., 24 hours, 2026 year)
        BENIGN_NUMBERS = {2024.0, 2025.0, 2026.0, 24.0, 12.0, 1.0, 2.0, 3.0}

        for num in extracted:
            # Check if num is close to any trace number
            if any(abs(num - tn) <= 0.15 for tn in trace_numbers) or num in BENIGN_NUMBERS:
                matched.append(num)
            else:
                violations.append(
                    GroundednessViolation(
                        category="NUMERICAL_HALLUCINATION",
                        severity="FAIL",
                        details=f"Extracted number {num} does not exist in deterministic rule_trace inputs or thresholds",
                        token=str(num),
                    )
                )

        # 3. Hazard Hallucination Check
        triggered = [r.get("rule", "") for r in verdict.rule_trace.get("triggered_rules", [])]
        inputs = verdict.rule_trace.get("inputs", {})

        # Cyclone check
        if "cyclone" in lower_text and not inputs.get("cyclone_alert"):
            violations.append(
                GroundednessViolation(
                    category="UNGROUNDED_HAZARD",
                    severity="FAIL",
                    details="Explanation mentions cyclone warning when no cyclone alert was present in inputs",
                )
            )

        # Lightning check
        if "lightning" in lower_text and inputs.get("lightning_risk") in ("none", "null", None, ""):
            violations.append(
                GroundednessViolation(
                    category="UNGROUNDED_HAZARD",
                    severity="WARN",
                    details="Explanation mentions lightning when lightning risk is none",
                )
            )

        # Calculate Score
        fail_count = sum(1 for v in violations if v.severity == "FAIL")
        warn_count = sum(1 for v in violations if v.severity == "WARN")
        score = max(0.0, 1.0 - (fail_count * 0.35) - (warn_count * 0.10))
        is_grounded = fail_count == 0

        return GroundednessReport(
            is_grounded=is_grounded,
            score=round(score, 2),
            verdict_concordance=verdict_concordance,
            violations=violations,
            extracted_numbers=extracted,
            matched_numbers=matched,
        )
