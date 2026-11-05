"""
Rule layer data structures and outcome enums.
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class EvaluationOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class RuleVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class RuleItemEvaluation(BaseModel):
    rule_id: str
    rule_name: str
    source_reference: str
    rule_version: str
    verification_status: RuleVerificationStatus
    outcome: EvaluationOutcome
    applicable_criterion: str
    observed_value: str
    tolerance_limit: str
    explanation: str
    details: Optional[List[Dict[str, Any]]] = None


class RuleEvaluationSummary(BaseModel):
    overall_outcome: EvaluationOutcome
    rule_version: str
    rules_evaluated_count: int
    passed_count: int
    failed_count: int
    incomplete_count: int
    not_applicable_count: int
    pending_verification_count: int
    evaluations: List[RuleItemEvaluation]
    summary_text: str

