from typing import Optional
from langchain_core.tools import tool
import digitalhub as dh


@tool
def get_dh_run_logs(
    project: str,
    run_id: str,
    tail: Optional[int] = None,
) -> str:
    """Get human-readable execution logs (tracebacks) of a run, optionally limited to the last N lines."""
    run = dh.get_run(run_id, project=project)
    logs = "\n".join(l.text for l in (run.logs() or []) if getattr(l, "text", None)).strip()
    if tail and logs:
        return "\n".join(logs.splitlines()[-tail:])
    return logs or "No logs available."


LOG_TOOLS = [
    get_dh_run_logs,
]
