import time


# TODO: Make the permission system more robust
class ToolPermissions:
    def __init__(self):
        # {agent_id: {tool_id: {"status": "ALLOWED"/"DENIED"/"CONDITIONAL",
        #                       "quota": {"per_day": int, "calls": int, "last_reset": float}}}}
        self.permissions = {}
        self.logs = []


    def set_permission(self, agent_id, tool_id, status="ALLOWED", quota=None):
        self.permissions.setdefault(agent_id, {})[tool_id] = {
            "status": status,
            "quota": {"per_day": quota, "calls": 0, "last_reset": time.time()} if quota else None
        }


    def _check_quota(self, agent_id, tool_id):
        record = self.permissions.get(agent_id, {}).get(tool_id)
        if not record or not record.get("quota"):
            return True, None

        q = record["quota"]
        now = time.time()

        # Reset quota every 24h
        if now - q["last_reset"] > 86400:
            q["calls"] = 0
            q["last_reset"] = now

        if q["per_day"] is not None and q["calls"] >= q["per_day"]:
            return False, "Daily quota exceeded"

        q["calls"] += 1
        return True, None


    def check_permission(self, agent_id, tool_id, context=None):
        record = self.permissions.get(agent_id, {}).get(tool_id)
        if not record:
            return False, "No permission entry"

        status = record["status"]

        if status == "ALLOWED":
            return True, None
        elif status == "DENIED":
            return False, "Permission denied"
        elif status == "CONDITIONAL":
            if context and context.get("approved", False):
                return True, None
            return False, "Condition not satisfied"
        return False, "Unknown status"


    def log(self, agent_id, tool_id, action, outcome, details=None):
        entry = {
            "agent": agent_id,
            "tool": tool_id,
            "action": action,
            "outcome": outcome,
            "details": details,
            "timestamp": time.time()
        }
        self.logs.append(entry)


    def get_logs(self):
        return self.logs
