"""All Pydantic v2 schemas for the FOI multi-agent system."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Topic = Literal[
    "finance_spending",
    "staffing_hr",
    "procurement_commercial",
    "internal_deliberations",
    "personal_data",
    "other",
]
Complexity = Literal["low", "medium", "high"]
Recommendation = Literal["release", "partial_release", "withhold"]


class TriageResult(BaseModel):
    topic: Topic
    complexity: Complexity
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    clarification_recommended: bool = False
    clarification_reason: Optional[str] = None


class RetrievedChunk(BaseModel):
    text: str
    source: str  # policy filename
    section: Optional[str] = None  # statutory section this chunk covers, when section-aware
    chunk_index: int
    distance: float  # cosine DISTANCE (lower = closer); NOT a similarity


class Citation(BaseModel):
    section: str  # e.g. "s40"
    quote: str  # verbatim excerpt copied from a retrieved chunk
    source: str
    chunk_index: int


class ExemptionFinding(BaseModel):
    section: str
    kind: Literal["absolute", "qualified"]
    applies: bool
    rationale: str
    public_interest_test: Optional[str] = None  # required when kind == "qualified" (e.g. s36, s43)
    qualified_person_opinion_required: bool = False  # true for s36 (s36(5))
    citations: list[Citation] = Field(default_factory=list)


class ComplianceResult(BaseModel):
    exemptions: list[ExemptionFinding] = Field(default_factory=list)
    recommendation: Recommendation
    policy_sources: list[str] = Field(default_factory=list)
    # SIGNAL only (s41 / s40(2)); drives gate banner
    third_party_notification_required: bool = False
    notes: str = ""
    grounded: bool = True  # set False on empty retrieval / failed verification


class RedactionItem(BaseModel):
    category: str  # "name" | "email" | "phone" | "postcode" | "staff_number" | ...
    exemption_section: str  # usually "s40"
    reason: str


class RedactionResult(BaseModel):
    redacted_draft: str
    schedule: list[RedactionItem] = Field(default_factory=list)
    redaction_complete: bool = True
    needs_mandatory_review: bool = False


class ResponseDraft(BaseModel):
    letter: str
    exemptions_cited: list[str] = Field(default_factory=list)
    evidence_summary: str


class Modification(BaseModel):
    before: str
    after: str


class HumanDecision(BaseModel):
    decision: Literal["approve", "reject", "modify"]
    operator: str  # required, non-empty (validated; never a default)
    timestamp: str  # ISO 8601 UTC
    notes: str = ""
    original_recommendation: Recommendation
    modification: Optional[Modification] = None  # set when decision == "modify"
    rejection_reason: Optional[str] = None  # set when decision == "reject"
    evidence_refs: list[str] = Field(default_factory=list)  # "source#chunk_index"

    @field_validator("operator")
    @classmethod
    def operator_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("operator must be a non-empty, non-whitespace string")
        return v.strip()  # store stripped


class CostEntry(BaseModel):
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CaseRecord(BaseModel):
    request_id: str
    request_file: str
    request_text: str
    triage: Optional[TriageResult] = None
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    compliance: Optional[ComplianceResult] = None
    response: Optional[ResponseDraft] = None
    redaction: Optional[RedactionResult] = None
    decision: Optional[HumanDecision] = None
    costs: list[CostEntry] = Field(default_factory=list)
    status: Literal["processed", "rejected", "error", "pending"] = "pending"
    errors: list[str] = Field(default_factory=list)


class AuditEntry(BaseModel):
    timestamp: str
    request_id: str
    event_type: str  # "triage" | "compliance" | "redaction" | "decision" | "cost" | "error" | ...
    agent: Optional[str] = None
    operator: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
