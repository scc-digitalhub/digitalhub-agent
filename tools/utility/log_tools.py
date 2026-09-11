from typing import Optional
from langchain_core.tools import tool
import digitalhub as dh


def extract_error_context(log_text: str) -> str:
    """
    Extract log lines starting from the first line containing 'stderr'.
    If no 'stderr' marker is found, falls back to the full logs.
    """
    lines = log_text.splitlines()
    for i, line in enumerate(lines):
        if "stderr" in line.lower():
            extracted = lines[i:]
            return "\n".join(extracted)
    return "\n".join(lines)


@tool
def get_dh_run_logs(
    project: str,
    run_id: str,
) -> str:
    """
    Get execution logs of a run. Returns all lines starting from the first 'stderr' occurrence,
    If no 'stderr' marker is found, falls back to the full logs.

    """
    run = dh.get_run(run_id, project=project)
    logs = "\n".join(l.text for l in (run.logs() or []) if getattr(l, "text", None)).strip()
    return extract_error_context(logs)


LOG_TOOLS = [
    get_dh_run_logs,
]
