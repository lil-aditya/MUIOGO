import json
import os
from datetime import datetime, timezone
from pathlib import Path
from Classes.Base import Config


class AuditLog:

    MAX_ENTRIES = 200

    @staticmethod
    def log(casename, action, param=None, details=None):
        log_path = Path(Config.DATA_STORAGE, casename, "audit_log.json")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entries = []
        if log_path.exists():
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, IOError):
                entries = []

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "action": action,
        }
        if param:
            entry["param"] = param
        if details:
            entry["details"] = details

        entries.append(entry)

        if len(entries) > AuditLog.MAX_ENTRIES:
            entries = entries[-AuditLog.MAX_ENTRIES:]

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

    @staticmethod
    def get_log(casename, limit=50):
        log_path = Path(Config.DATA_STORAGE, casename, "audit_log.json")
        if not log_path.exists():
            return []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
            return entries[-limit:]
        except (json.JSONDecodeError, IOError):
            return []