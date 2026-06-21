"""Approval request and decision models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .artifacts import StageID


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ApprovalRequest(BaseModel):
    approval_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_id: str
    stage_id: StageID
    requester: str
    approvers: List[str]
    minimum_approvals: int = 1
    context: Dict[str, Any] = Field(default_factory=dict)
    artifact_ids: List[str] = Field(default_factory=list)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    decisions: List["ApprovalDecision"] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_approved(self) -> bool:
        approved_count = sum(1 for d in self.decisions if d.decision == "approved")
        return approved_count >= self.minimum_approvals

    def is_rejected(self) -> bool:
        return any(d.decision == "rejected" for d in self.decisions)

    def pending_approvers(self) -> List[str]:
        decided = {d.decided_by for d in self.decisions}
        return [a for a in self.approvers if a not in decided]

    def resolve_status(self) -> ApprovalStatus:
        if self.is_expired():
            return ApprovalStatus.EXPIRED
        if self.is_rejected():
            return ApprovalStatus.REJECTED
        if self.is_approved():
            return ApprovalStatus.APPROVED
        return ApprovalStatus.PENDING


class ApprovalDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    approval_id: str
    decided_by: str
    decision: str  # approved / rejected
    comments: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)
