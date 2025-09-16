import time


class ToolPermissions:
    def __init__(self):
        # {agent_id: {tool_id: {"status": str,
        #                       "quota": {"per_day": int, "calls": int, "last_reset": float}}}}
        self.permissions = {}
        self.logs = []

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

    def check_permission(self, agent_id, tool_id, context=None):
        """Check if agent has permission and within quota for tool usage"""
        record = self.permissions.get(agent_id, {}).get(tool_id)
        if not record:
            return False, "No permission entry"

        status = record["status"]

        # === Step 1: Status-based check ===
        if status == "DENIED":
            return False, "Permission denied"

        if status == "CONDITIONAL":
            if not (context and context.get("approved", False)):
                return False, "Condition not satisfied"

        # === Step 2: Quota-based check ===
        quota = record.get("quota")
        if quota:
            now = time.time()

            # Reset quota every 24h
            if now - quota["last_reset"] > 86400:
                quota["calls"] = 0
                quota["last_reset"] = now

            if quota["per_day"] is not None and quota["calls"] >= quota["per_day"]:
                return False, "Daily quota exceeded"

            quota["calls"] += 1

        # Passed all checks
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

    def get_logs(self):
        return self.logs
