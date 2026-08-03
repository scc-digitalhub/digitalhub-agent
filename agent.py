from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware, ToolCallRequest
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from settings import DEPLOYED_URL, LLM_MODEL, LLM_API_KEY
from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT


def _on_tool_error(exc: Exception, request: ToolCallRequest) -> str:
    """Return the raw SDK exception message to the model so it can self-correct."""
    tool_name = request.tool_call["name"]
    return f"SDK Exception in tool '{tool_name}': {exc}"


def get_dh_agent(tools=None, model_name=None, base_url=None, api_key=None, system_prompt=None):
    """
    Build and return the DigitalHub Agent instance.
    """
    active_tools = tools if tools is not None else ALL_TOOLS
    model = model_name or LLM_MODEL
    url = base_url or DEPLOYED_URL
    key = api_key or LLM_API_KEY
    prompt = system_prompt or SYSTEM_PROMPT

    if not key:
        raise ValueError("LLM_API_KEY environment variable is required. Set it via: export LLM_API_KEY='your-key'")

    llm = ChatOpenAI(
        model=model,
        base_url=f"{url}/v1",
        api_key=key,
    )
    
    memory = MemorySaver()
    error_middleware = ToolErrorMiddleware(on_error=_on_tool_error)

    return create_agent(
        model=llm,
        tools=active_tools,
        system_prompt=prompt,
        checkpointer=memory,
        middleware=[error_middleware]
    )
