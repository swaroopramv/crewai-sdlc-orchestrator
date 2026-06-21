"""Notification tools for Chat, email, and approval alerts."""

from crewai.tools import BaseTool
import json
import logging

logger = logging.getLogger(__name__)


class ChatNotifyTool(BaseTool):
    name: str = "chat_notify"
    description: str = "Send a Chat message to a room or person with a notification about a pipeline event"

    def _run(self, recipient: str, message: str, room_id: str = "") -> str:
        """
        Send Chat notification.
        In production: calls Chat REST API with bot token.
        """
        logger.info("CHAT → %s: %s", recipient, message)
        # Placeholder — replace with actual Chat API call
        return json.dumps({"status": "sent", "recipient": recipient})


class EmailNotifyTool(BaseTool):
    name: str = "email_notify"
    description: str = "Send an email notification to one or more recipients about a pipeline event"

    def _run(self, to: list[str], subject: str, body: str) -> str:
        """
        Send email notification.
        In production: calls SMTP or email service API.
        """
        logger.info("EMAIL → %s: %s", to, subject)
        # Placeholder — replace with actual email service call
        return json.dumps({"status": "sent", "recipients": to})


class ApprovalNotifyTool(BaseTool):
    name: str = "approval_notify"
    description: str = "Send an approval request notification to designated approvers via Chat and email"

    def _run(self, approval_id: str, approvers: list[str], stage_id: str, context_summary: str) -> str:
        """
        Notify approvers of a pending approval request.
        In production: sends rich Chat card with approve/reject buttons.
        """
        message = (
            f"[APPROVAL REQUIRED] Stage: {stage_id}\n"
            f"Approval ID: {approval_id}\n"
            f"Summary: {context_summary}\n"
            f"Please review and approve or reject."
        )
        for approver in approvers:
            logger.info("APPROVAL NOTIFY → %s for %s", approver, approval_id)
        # Placeholder
        return json.dumps({"status": "sent", "approval_id": approval_id, "notified": approvers})


notification_tools = [ChatNotifyTool(), EmailNotifyTool(), ApprovalNotifyTool()]
