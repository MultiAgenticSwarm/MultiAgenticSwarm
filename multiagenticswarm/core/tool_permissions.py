import time

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolPermissions:
    """Manages permission and quota rules for tool usage per agent.

    - Stores allow/deny/conditional status and optional daily quotas
    - Evaluates permissions at runtime with simple quota enforcement
    - Records local audit logs and emits structured logs via project logger
    """

    def __init__(self):
        # {agent_id: {tool_id: {"status": str,
        #                       "quota": {"per_day": int, "calls": int, "last_reset": float}}}}
        self.permissions = {}
        self.logs = []
        logger.debug("Initialized ToolPermissions store")

    def set_permission(self, agent_id, tool_id, status="ALLOWED", quota=None):
        if isinstance(quota, int):
            quota = {"per_day": quota}

        self.permissions.setdefault(agent_id, {})[tool_id] = {
            "status": status,
            "quota": {
                "per_day": quota.get("per_day"),
                "calls": 0,
                "last_reset": time.time(),
            }
            if quota
            else None,
        }
        logger.info(
            "Permission set",
            extra={"mas_agent": agent_id, "mas_tool": tool_id, "mas_status": status, "mas_quota": quota},
        )

    def check_permission(self, agent_id, tool_id, context=None):
        """Check if agent has permission and within quota for tool usage"""
        record = self.permissions.get(agent_id, {}).get(tool_id)
        if not record:
            logger.warning(
                "Permission entry missing",
                extra={"mas_agent": agent_id, "mas_tool": tool_id},
            )
            return False, "No permission entry"

        status = record["status"]

        # === Step 1: Status-based check ===
        if status == "DENIED":
            logger.debug(
                "Permission denied by status",
                extra={"mas_agent": agent_id, "mas_tool": tool_id},
            )
            return False, "Permission denied"

        if status == "CONDITIONAL":
            if not (context and context.get("approved", False)):
                logger.debug(
                    "Permission conditional check failed",
                    extra={"mas_agent": agent_id, "mas_tool": tool_id},
                )
                return False, "Condition not satisfied"

        # === Step 2: Quota-based check ===
        quota = record.get("quota")
        if quota:
            now = time.time()

            # Reset quota every 24h
            if now - quota["last_reset"] > 86400:
                logger.debug("Resetting daily quota", extra={"mas_agent": agent_id, "mas_tool": tool_id})
                quota["calls"] = 0
                quota["last_reset"] = now

            if quota["per_day"] is not None and quota["calls"] >= quota["per_day"]:
                logger.warning(
                    "Daily quota exceeded",
                    extra={"mas_agent": agent_id, "mas_tool": tool_id, "mas_quota": quota["per_day"]},
                )
                return False, "Daily quota exceeded"

            quota["calls"] += 1

        # Passed all checks
        logger.debug("Permission granted", extra={"mas_agent": agent_id, "mas_tool": tool_id})
        return True, None

    def log(self, agent_id, tool_id, action, outcome, details=None):
        entry = {
            "agent": agent_id,
            "tool": tool_id,
            "action": action,
            "outcome": outcome,
            "details": details,
            "timestamp": time.time(),
        }
        self.logs.append(entry)
        logger.info(
            "Tool permission log entry",
            extra={
                "mas_agent": agent_id,
                "mas_tool": tool_id,
                "mas_action": action,
                "mas_outcome": outcome,
            },
        )

    def get_logs(self):
        return self.logs
