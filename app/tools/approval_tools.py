"""
Approval tools — proper CrewAI BaseTool wrappers around ApprovalManager.
Used by test_plan_reviewer and qa_signoff_agent to request and check approvals.
"""

from __future__ import annotations

import json
import logging

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class RequestApprovalTool(BaseTool):
    name: str = "request_approval"
    description: str = (
        "Request human approval for the current stage. "
        "Provide pipeline_id, stage_id, approvers (comma-separated), "
        "context_summary, and artifact_ids (comma-separated). "
        "Returns the approval_id to track the request."
    )
    _approval_manager: object = None

    def __init__(self, approval_manager):
        super().__init__()
        self._approval_manager = approval_manager

    def _run(
        self,
        pipeline_id: str,
        stage_id: str,
        approvers: str,
        context_summary: str,
        artifact_ids: str = "",
        minimum_approvals: int = 1,
        timeout_hours: int = 24,
    ) -> str:
        from models.artifacts import StageID
        approver_list = [a.strip() for a in approvers.split(",") if a.strip()]
        artifact_list = [a.strip() for a in artifact_ids.split(",") if a.strip()]

        try:
            stage = StageID(stage_id)
        except ValueError:
            return json.dumps({"error": f"Unknown stage_id: {stage_id}"})

        req = self._approval_manager.request(
            pipeline_id=pipeline_id,
            stage_id=stage,
            requester="agent",
            approvers=approver_list,
            context={"summary": context_summary},
            artifact_ids=artifact_list,
            minimum_approvals=minimum_approvals,
            timeout_hours=timeout_hours,
        )
        logger.info("Approval requested: %s for stage %s", req.approval_id, stage_id)
        return json.dumps({
            "approval_id": req.approval_id,
            "status": req.status,
            "approvers": approver_list,
            "expires_at": req.expires_at.isoformat() if req.expires_at else None,
        })


class CheckApprovalTool(BaseTool):
    name: str = "check_approval_status"
    description: str = (
        "Check the current status of an approval request by its approval_id. "
        "Returns status: pending / approved / rejected / expired."
    )
    _approval_manager: object = None

    def __init__(self, approval_manager):
        super().__init__()
        self._approval_manager = approval_manager

    def _run(self, approval_id: str) -> str:
        try:
            status = self._approval_manager.get_status(approval_id)
            req = self._approval_manager._get(approval_id)
            return json.dumps({
                "approval_id": approval_id,
                "status": status,
                "pending_approvers": req.pending_approvers(),
                "decisions_received": len(req.decisions),
                "minimum_required": req.minimum_approvals,
            })
        except KeyError:
            return json.dumps({"error": f"Approval {approval_id} not found"})


class GrantApprovalTool(BaseTool):
    name: str = "grant_approval"
    description: str = (
        "Grant approval for a pending approval request. "
        "Provide approval_id, decided_by (approver identity), and optional comments."
    )
    _approval_manager: object = None

    def __init__(self, approval_manager):
        super().__init__()
        self._approval_manager = approval_manager

    def _run(self, approval_id: str, decided_by: str, comments: str = "") -> str:
        try:
            req = self._approval_manager.decide(
                approval_id=approval_id,
                decided_by=decided_by,
                decision="approved",
                comments=comments or None,
            )
            logger.info("Approval %s granted by %s", approval_id, decided_by)
            return json.dumps({
                "approval_id": approval_id,
                "status": req.status,
                "decided_by": decided_by,
            })
        except PermissionError as e:
            return json.dumps({"error": str(e)})
        except TimeoutError as e:
            return json.dumps({"error": str(e)})
        except KeyError:
            return json.dumps({"error": f"Approval {approval_id} not found"})


class RejectApprovalTool(BaseTool):
    name: str = "reject_approval"
    description: str = (
        "Reject a pending approval request. "
        "Provide approval_id, decided_by (approver identity), and mandatory comments explaining the rejection."
    )
    _approval_manager: object = None

    def __init__(self, approval_manager):
        super().__init__()
        self._approval_manager = approval_manager

    def _run(self, approval_id: str, decided_by: str, comments: str) -> str:
        try:
            req = self._approval_manager.decide(
                approval_id=approval_id,
                decided_by=decided_by,
                decision="rejected",
                comments=comments,
            )
            logger.info("Approval %s rejected by %s: %s", approval_id, decided_by, comments)
            return json.dumps({
                "approval_id": approval_id,
                "status": req.status,
                "decided_by": decided_by,
                "comments": comments,
            })
        except PermissionError as e:
            return json.dumps({"error": str(e)})
        except KeyError:
            return json.dumps({"error": f"Approval {approval_id} not found"})


class ListPendingApprovalsTool(BaseTool):
    name: str = "list_pending_approvals"
    description: str = (
        "List all pending approval requests for a given pipeline_id. "
        "Returns a list of approval_ids, stage_ids, and approver lists awaiting decisions."
    )
    _approval_manager: object = None

    def __init__(self, approval_manager):
        super().__init__()
        self._approval_manager = approval_manager

    def _run(self, pipeline_id: str) -> str:
        pending = self._approval_manager.pending_for_pipeline(pipeline_id)
        result = [
            {
                "approval_id": r.approval_id,
                "stage_id": str(r.stage_id),
                "pending_approvers": r.pending_approvers(),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            }
            for r in pending
        ]
        return json.dumps(result)


def get_approval_tools(approval_manager) -> list:
    """
    Build all approval tool instances bound to the given ApprovalManager.
    Call this once during PipelineRunner setup and add to tools_registry['approval_tools'].
    """
    return [
        RequestApprovalTool(approval_manager),
        CheckApprovalTool(approval_manager),
        GrantApprovalTool(approval_manager),
        RejectApprovalTool(approval_manager),
        ListPendingApprovalsTool(approval_manager),
    ]
