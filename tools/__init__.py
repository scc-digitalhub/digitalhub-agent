from tools.project_tools import PROJECT_TOOLS
from tools.dataitem_tools import DATAITEM_TOOLS
from tools.function_tools import FUNCTION_TOOLS
from tools.workflow_tools import WORKFLOW_TOOLS
from tools.trigger_tools import TRIGGER_TOOLS
from tools.artifact_tools import ARTIFACT_TOOLS
from tools.model_tools import MODEL_TOOLS
from tools.knowledge_tools import KNOWLEDGE_TOOLS

ALL_TOOLS = (
    KNOWLEDGE_TOOLS
    + PROJECT_TOOLS
    + DATAITEM_TOOLS
    + FUNCTION_TOOLS
    + WORKFLOW_TOOLS
    + TRIGGER_TOOLS
    + ARTIFACT_TOOLS
    + MODEL_TOOLS
)

__all__ = [
    "KNOWLEDGE_TOOLS",
    "PROJECT_TOOLS",
    "DATAITEM_TOOLS",
    "FUNCTION_TOOLS",
    "WORKFLOW_TOOLS",
    "TRIGGER_TOOLS",
    "ARTIFACT_TOOLS",
    "MODEL_TOOLS",
    "ALL_TOOLS",
]
