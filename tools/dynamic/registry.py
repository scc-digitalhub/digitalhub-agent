"""
Registry for dynamic tools and domain scoping lifecycle management.
"""
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from langchain.agents.middleware import AgentMiddleware, ToolCallRequest, ModelRequest


class DynamicToolsMiddleware(AgentMiddleware):
    def __init__(self, registry: "DynamicToolRegistry"):
        super().__init__()
        self.registry = registry

    def _enrich_model_request(self, request: ModelRequest) -> ModelRequest:
        active_tools = self.registry.get_active_domain_tools()
        if active_tools:
            existing_tools = list(request.tools or [])
            existing_names = {getattr(t, "name", "") for t in existing_tools}
            new_tools = [t for t in active_tools if getattr(t, "name", "") not in existing_names]
            if new_tools:
                request = request.override(tools=existing_tools + new_tools)
        return request

    def _resolve_tool_request(self, request: ToolCallRequest) -> ToolCallRequest:
        tool_name = (
            request.tool_call.get("name")
            if isinstance(request.tool_call, dict)
            else getattr(request.tool_call, "name", "")
        )
        if not request.tool or not getattr(request.tool, "name", None):
            dyn_tool = self.registry.get_tool(tool_name)
            if dyn_tool:
                request = request.override(tool=dyn_tool)
        return request

    def wrap_model_call(self, request: ModelRequest, handler):
        return handler(self._enrich_model_request(request))

    async def awrap_model_call(self, request: ModelRequest, handler):
        return await handler(self._enrich_model_request(request))

    def wrap_tool_call(self, request: ToolCallRequest, handler):
        return handler(self._resolve_tool_request(request))

    async def awrap_tool_call(self, request: ToolCallRequest, handler):
        return await handler(self._resolve_tool_request(request))



class DynamicToolRegistry:
    """
    Central registry with Domain Scoping support.
    Tracks active tools per entity/runtime domain (e.g. 'project', 'runtime:python')
    and automatically unloads previous domain tools when activating a new domain,
    preventing tool context creep and hallucination.
    """

    def __init__(self):
        self._domain_tools: Dict[str, Dict[str, BaseTool]] = {}
        self._active_domain: Optional[str] = None
        self._active_agents: List[Any] = []
        self._middleware: Optional[DynamicToolsMiddleware] = None

    def get_middleware(self) -> DynamicToolsMiddleware:
        """Return the LangChain AgentMiddleware for this registry."""
        if self._middleware is None:
            self._middleware = DynamicToolsMiddleware(self)
        return self._middleware

    def activate_domain(self, domain: str, tools: List[BaseTool], swap_domain: bool = True) -> None:
        """Activate tools for a domain and swap out previous domain tools if swap_domain=True."""
        domain_key = domain.lower()

        # 1. If swapping domains, unload previous active domain tools from all agents
        if swap_domain and self._active_domain and self._active_domain != domain_key:
            prev_tools = self._domain_tools.get(self._active_domain, {})
            for agent in self._active_agents:
                self._unload_tools_from_agent(agent, list(prev_tools.keys()))

        # 2. Store tools in domain dictionary
        if domain_key not in self._domain_tools:
            self._domain_tools[domain_key] = {}
        for t in tools:
            self._domain_tools[domain_key][t.name] = t

        self._active_domain = domain_key

        # 3. Inject new domain tools into all active agents
        for agent in self._active_agents:
            for t in tools:
                self._inject_tool_into_agent(agent, t)

    def register_agent(self, agent: Any) -> None:
        """Register an active agent graph instance and populate it with currently active domain tools."""
        if agent not in self._active_agents:
            self._active_agents.append(agent)
            if self._active_domain:
                active_tools = self._domain_tools.get(self._active_domain, {})
                for t in active_tools.values():
                    self._inject_tool_into_agent(agent, t)

    def _inject_tool_into_agent(self, agent: Any, dynamic_tool: BaseTool) -> None:
        """Inject a dynamic tool into the agent's ToolNode and model node tool list closure."""
        try:
            tools_node = getattr(agent, "nodes", {}).get("tools")
            if tools_node and hasattr(tools_node, "bound") and hasattr(tools_node.bound, "tools_by_name"):
                tools_node.bound.tools_by_name[dynamic_tool.name] = dynamic_tool

            model_node = getattr(agent, "nodes", {}).get("model")
            if model_node and hasattr(model_node, "bound") and hasattr(model_node.bound, "func"):
                closure = getattr(model_node.bound.func, "__closure__", None)
                if closure:
                    for cell in closure:
                        val = cell.cell_contents
                        if isinstance(val, list) and (len(val) == 0 or hasattr(val[0], "name")):
                            if not any(getattr(t, "name", None) == dynamic_tool.name for t in val):
                                val.append(dynamic_tool)
        except Exception:
            pass

    def _unload_tools_from_agent(self, agent: Any, tool_names: List[str]) -> None:
        """Unload specific tool names from the agent's ToolNode and model node tool list closure."""
        try:
            names_set = set(tool_names)
            tools_node = getattr(agent, "nodes", {}).get("tools")
            if tools_node and hasattr(tools_node, "bound") and hasattr(tools_node.bound, "tools_by_name"):
                for name in tool_names:
                    tools_node.bound.tools_by_name.pop(name, None)

            model_node = getattr(agent, "nodes", {}).get("model")
            if model_node and hasattr(model_node, "bound") and hasattr(model_node.bound, "func"):
                closure = getattr(model_node.bound.func, "__closure__", None)
                if closure:
                    for cell in closure:
                        val = cell.cell_contents
                        if isinstance(val, list) and (len(val) == 0 or hasattr(val[0], "name")):
                            cell.cell_contents[:] = [t for t in val if getattr(t, "name", "") not in names_set]
        except Exception:
            pass

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Find a tool across any registered domain."""
        for domain_dict in self._domain_tools.values():
            if name in domain_dict:
                return domain_dict[name]
        return None

    def get_active_domain_tools(self) -> List[BaseTool]:
        """Return tools for the currently active domain."""
        if not self._active_domain:
            return []
        return list(self._domain_tools.get(self._active_domain, {}).values())

    def get_all_tools(self) -> List[BaseTool]:
        """Return all registered tools across all domains."""
        all_t = {}
        for d in self._domain_tools.values():
            all_t.update(d)
        return list(all_t.values())

    def clear(self) -> None:
        """Clear all registered domain tools and active domain."""
        for domain_dict in self._domain_tools.values():
            for agent in self._active_agents:
                self._unload_tools_from_agent(agent, list(domain_dict.keys()))
        self._domain_tools.clear()
        self._active_domain = None


# Global registry singleton
DYNAMIC_REGISTRY = DynamicToolRegistry()