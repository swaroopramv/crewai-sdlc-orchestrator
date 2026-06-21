"""Manages human approval requests and decisions."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from models.approvals import ApprovalDecision, ApprovalRequest, ApprovalStatus
from models.artifacts import StageID


class ApprovalManager:
    def __init__(self, default_timeout_hours: int = 24):
        self._requests: dict[str, ApprovalRequest] = {}
        self._default_timeout = default_timeout_hours

    def request(
        self,
        pipeline_id: str,
        stage_id: StageID,
        requester: str,
        approvers: list[str],
        context: dict,
        artifact_ids: list[str],
        minimum_approvals: int = 1,
        timeout_hours: Optional[int] = None,
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            requester=requester,
            approvers=approvers,
            minimum_approvals=minimum_approvals,
            context=context,
            artifact_ids=artifact_ids,
            expires_at=datetime.utcnow() + timedelta(hours=timeout_hours or self._default_timeout),
        )
        self._requests[req.approval_id] = req
        return req

    def decide(
        self,
        approval_id: str,
        decided_by: str,
        decision: str,
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        req = self._get(approval_id)
        if decided_by not in req.approvers:
            raise PermissionError(f"{decided_by} is not an authorized approver for {approval_id}")
        if req.is_expired():
            req.status = ApprovalStatus.EXPIRED
            raise TimeoutError(f"Approval {approval_id} has expired")

        req.decisions.append(
            ApprovalDecision(
                approval_id=approval_id,
                decided_by=decided_by,
                decision=decision,
                comments=comments,
            )
        )
        req.status = req.resolve_status()
        return req

    def get_status(self, approval_id: str) -> ApprovalStatus:
        req = self._get(approval_id)
        if req.is_expired() and req.status == ApprovalStatus.PENDING:
            req.status = ApprovalStatus.EXPIRED
        else:
            req.status = req.resolve_status()
        return req.status

    def pending_for_pipeline(self, pipeline_id: str) -> list[ApprovalRequest]:
        return [
            r for r in self._requests.values()
            if r.pipeline_id == pipeline_id and r.status == ApprovalStatus.PENDING
        ]

    def _get(self, approval_id: str) -> ApprovalRequest:
        if approval_id not in self._requests:
            raise KeyError(f"Approval {approval_id} not found")
        return self._requests[approval_id]
