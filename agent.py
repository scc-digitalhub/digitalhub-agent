from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware, ToolCallRequest
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from settings import DEPLOYED_URL, LLM_MODEL, LLM_API_KEY
from tools import ALL_TOOLS, DYNAMIC_REGISTRY
from prompts import SYSTEM_PROMPT


def _on_tool_error(exc: Exception, request: ToolCallRequest) -> str:
    """Return the raw SDK exception message with OKF troubleshooting guidance to the model for self-correction."""
    tool_name = request.tool_call["name"]
    # Infer entity topic from tool name (e.g. 'new_dh_secret' -> 'secret')
    clean_name = tool_name.replace("new_dh_", "").replace("get_dh_", "").replace("list_dh_", "").replace("delete_dh_", "")
    entity_topic = clean_name.split("_")[0]
    return (
        f"SDK Exception in tool '{tool_name}': {exc}\n"
        f"Self-Correction & Escalation Guidance:\n"
        f"1. Check the entity specification: `get_knowledge_doc('{entity_topic}')`.\n"
        f"2. Consult the troubleshooting guide: `get_knowledge_doc('troubleshooting')` or `search_knowledge('{type(exc).__name__}')`.\n"
        f"3. Verify parameter requirements before retrying (maximum 2 retries allowed).\n"
        f"4. STOPPING RULE: If you cannot resolve this issue after 1-2 attempts or if the error persists, STOP retrying immediately. Do not loop infinitely. Formulate a clear explanation of the problem for the user and ask how they would like to solve it."
    )


def get_dh_agent(
    tools=None,
    model_name=None,
    base_url=None,
    api_key=None,
    system_prompt=None,
    with_memory=False,
):
    """
    Build and return the DigitalHub Agent instance.
    - with_memory=True: attaches MemorySaver for interactive CLI.
    - with_memory=False: no checkpointer (for native LangGraph / langgraph dev).
    """
    if tools is not None:
        active_tools = list(tools)
    else:
        active_tools = list(ALL_TOOLS)
        # Include any dynamic tools already generated
        existing_dynamic = DYNAMIC_REGISTRY.get_all_tools()
        for dt in existing_dynamic:
            if not any(t.name == dt.name for t in active_tools):
                active_tools.append(dt)

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
        stream_usage=True,
    )
    
    error_middleware = ToolErrorMiddleware(on_error=_on_tool_error)

    agent_kwargs = {
        "model": llm,
        "tools": active_tools,
        "system_prompt": prompt,
        "middleware": [error_middleware],
    }
    if with_memory:
        agent_kwargs["checkpointer"] = MemorySaver()

    agent = create_agent(**agent_kwargs)
    DYNAMIC_REGISTRY.register_agent(agent)
    return agent

