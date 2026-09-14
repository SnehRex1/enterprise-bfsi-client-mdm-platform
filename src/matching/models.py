from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class RecordRef:
    """
    Identifies one source record uniquely.
    """

    source_system: str
    source_id: str


@dataclass
class CandidatePair:
    """
    Represents two source records that are worth comparing.

    A candidate pair is NOT automatically a match.
    """

    left: RecordRef
    right: RecordRef
    blocking_keys: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """
    Final explainable result for a candidate pair.
    """

    left: RecordRef
    right: RecordRef

    match_score: float
    decision: str

    matching_rule: Optional[str] = None

    name_score: Optional[float] = None
    address_score: Optional[float] = None
    phone_score: Optional[float] = None
    email_score: Optional[float] = None
    dob_score: Optional[float] = None

    reason: Optional[str] = None