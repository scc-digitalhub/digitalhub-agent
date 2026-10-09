# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

from agent import get_dh_agent
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

# Global agent instance with checkpointer for stateful sessions
agent = get_dh_agent(with_memory=True)

threads: Dict[str, Dict[str, Any]] = {}


def serialize_message(msg: Any) -> Dict[str, Any]:
    """Serialize LangChain or dict message to standardized JSON for assistant-ui / LangGraph SDK."""
    if isinstance(msg, dict):
        return msg

    msg_type = getattr(msg, "type", "ai")
    type_map = {
        "human": "human",
        "user": "human",
        "ai": "ai",
        "assistant": "ai",
        "tool": "tool",
        "system": "system",
        "AIMessageChunk": "ai",
    }

    out: Dict[str, Any] = {
        "id": getattr(msg, "id", None) or str(uuid.uuid4()),
        "type": type_map.get(msg_type, msg_type),
        "content": getattr(msg, "content", ""),
    }

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.get("id", str(uuid.uuid4())),
                "name": tc.get("name", ""),
                "args": tc.get("args", {}),
            }
            for tc in msg.tool_calls
        ]

    if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
        out["tool_call_chunks"] = [
            {
                "index": getattr(tc, "index", idx),
                "id": getattr(tc, "id", "") or str(uuid.uuid4()),
                "name": getattr(tc, "name", ""),
                "args": getattr(tc, "args", ""),
            }
            for idx, tc in enumerate(msg.tool_call_chunks)
        ]

    if hasattr(msg, "tool_call_id") and msg.tool_call_id:
        out["tool_call_id"] = msg.tool_call_id
        out["name"] = getattr(msg, "name", "")
        out["status"] = getattr(msg, "status", "success")
    return out


def parse_incoming_messages(
    body: Dict[str, Any], project_name: Optional[str] = None
) -> List[BaseMessage]:
    """Parse incoming JSON payload into LangChain messages and prepend current project context."""
    messages_input = body.get("input", {}).get("messages") or body.get("messages", [])
    parsed_messages: List[BaseMessage] = []

    for m in messages_input:
        if isinstance(m, dict):
            role = m.get("role") or m.get("type", "human")
            content = m.get("content", "")
            if isinstance(content, list):
                content = "".join(
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ) or str(content)

            if role in ("user", "human"):
                parsed_messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                parsed_messages.append(AIMessage(content=content))
            elif role in ("system",):
                parsed_messages.append(SystemMessage(content=content))
        elif isinstance(m, BaseMessage):
            parsed_messages.append(m)

    if not parsed_messages:
        prompt = body.get("message") or body.get("input", {}).get("message")
        if prompt:
            parsed_messages.append(HumanMessage(content=str(prompt)))

    context_text = (
        f"[DigitalHub Console Context]\nCURRENT ACTIVE PROJECT: '{project_name}'"
        if project_name
        else "[DigitalHub Console Context]\nCURRENT ACTIVE PROJECT: None"
    )
    return [SystemMessage(content=context_text)] + parsed_messages


def extract_project(body: Dict[str, Any]) -> Optional[str]:
    """Extract project name from standard JSON payload or nested input."""
    raw = body.get("input", {}).get("project")
    if raw:
        clean = str(raw).strip()
        if clean.lower() not in ("null", "none", "undefined", ""):
            return clean
    return None


async def create_thread(request: Request) -> JSONResponse:
    """Create or register a conversation thread."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    thread_id = body.get("thread_id") or f"thread_{uuid.uuid4().hex[:12]}"
    metadata = body.get("metadata", {})

    thread_info = {
        "thread_id": thread_id,
        "created_at": asyncio.get_event_loop().time(),
        "metadata": metadata,
        "status": "idle",
    }
    threads[thread_id] = thread_info
    return JSONResponse(thread_info)


async def get_thread_state(request: Request) -> JSONResponse:
    """Get the state and message history of an existing thread."""
    thread_id = request.path_params.get("thread_id")
    if not thread_id:
        return JSONResponse({"error": "thread_id is required"}, status_code=400)

    try:
        state = agent.get_state({"configurable": {"thread_id": thread_id}})
        raw_messages = (
            state.values.get("messages", []) if state and state.values else []
        )
        # Filter internal system context messages so they do not pollute UI chat history
        messages = [
            serialize_message(m)
            for m in raw_messages
            if getattr(m, "type", "") not in ("system", "SystemMessage")
        ]
        return JSONResponse(
            {
                "values": {"messages": messages},
                "next": list(state.next) if state and state.next else [],
                "checkpoint": getattr(state, "config", {}),
            }
        )
    except Exception as e:
        return JSONResponse({"values": {"messages": []}, "error": str(e)})


def sse_pack(event: str, data: Any) -> str:
    """Format standard Server-Sent Event (SSE) payload."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def sse_data(data: Any) -> str:
    """Format single data payload for SSE."""
    return f"data: {json.dumps(data)}\n\n"


def serialize_node_update(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize LangGraph state update dictionary."""
    update: Dict[str, Any] = {}
    for node, val in chunk.items():
        if isinstance(val, dict) and "messages" in val:
            update[node] = {
                "messages": [
                    serialize_message(m)
                    for m in val["messages"]
                    if getattr(m, "type", "") not in ("system", "SystemMessage")
                ]
            }
        else:
            update[node] = str(val)
    return update


async def stream_thread_run(request: Request) -> Response:
    """
    Stream agent run events in LangGraph SSE protocol.
    Directly compatible with @assistant-ui/react-langgraph and @langchain/langgraph-sdk.
    """
    thread_id = request.path_params.get("thread_id")
    if not thread_id:
        return JSONResponse({"error": "thread_id is required"}, status_code=400)

    try:
        body = await request.json()
    except Exception:
        body = {}

    project = extract_project(body)
    messages = parse_incoming_messages(body, project_name=project)
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            run_id = f"run_{uuid.uuid4().hex[:12]}"
            yield sse_pack("metadata", {"run_id": run_id, "thread_id": thread_id})

            # Native non-blocking async streaming
            async for mode, chunk in agent.astream(
                {"messages": messages},
                stream_mode=["messages", "updates"],
                config=config,
            ):
                if mode == "messages":
                    msg_chunk, meta = chunk
                    if getattr(msg_chunk, "type", "") in ("system", "SystemMessage"):
                        continue
                    yield sse_pack("messages", [serialize_message(msg_chunk), meta])

                elif mode == "updates" and isinstance(chunk, dict):
                    yield sse_pack("updates", serialize_node_update(chunk))

                await asyncio.sleep(0.005)

            yield sse_pack("end", {"status": "success"})

        except Exception as exc:
            yield sse_pack("error", {"error": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


routes = [
    Route("/threads", create_thread, methods=["POST"]),
    Route("/threads/{thread_id}/state", get_thread_state, methods=["GET"]),
    Route("/threads/{thread_id}/runs/stream", stream_thread_run, methods=["POST"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DigitalHub Agent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument(
        "--port", type=int, default=2024, help="Port to listen on (default: 2024)"
    )
    args = parser.parse_args()

    print(f"Starting DigitalHub Agent API Server on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
