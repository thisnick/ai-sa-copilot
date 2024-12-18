import json
from pydantic import BaseModel, TypeAdapter
from pydantic.json import pydantic_encoder
from typing import AsyncGenerator, List, Dict, Any, Literal, Optional, cast
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from supabase import AsyncClient

from api.agents.contexts import get_supabase_client_from_context
from api.agents.types import ContextVariables
from api.db.types import Thread
from api.agents import stream_response
from swarm.types import (
    Message,
    AsyncStreamingResponse as AsyncSwarmStreamingResponse,
    AsyncMessageStreamingChunk,
    AsyncDelimStreamingChunk,
    AsyncResponseStreamingChunk,
    AsyncDeltaResponseStreamingChunk
)

router = APIRouter()


class Request(BaseModel):
  domain_id: str
  thread_id: str
  message: str

async def get_thread_data(
  thread_id: str,
  user_id: str,
  domain_id: str,
) -> tuple[str, Optional[str], List[Message], ContextVariables]:
  supabase = get_supabase_client_from_context()
  thread_response = await (
    supabase
    .table("threads")
    .select("*, state:thread_states!last_known_good_thread_state_id(*)")
    .eq("thread_id", thread_id)
    .limit(1)
    .execute()
  )
  if thread_response.data is None or len(thread_response.data) == 0:
    thread_response = await (
      supabase
      .table("threads")
      .insert({
        "user_id": user_id,
        "thread_id": thread_id,
        "thread_type": "runbook_generator"
      })
      .execute()
    )

  agent_name = None
  messages: List[Message] = []
  context_variables: ContextVariables = {}

  if thread_response and thread_response.data and len(thread_response.data) > 0:
    thread: Thread = thread_response.data[0]
    thread_state = thread.get('state') or {}
    agent_name = thread_state.get("agent_name")
    messages = thread_state.get("messages", [])
    context_variables = thread_state.get("context_variables", {})
    thread_id = thread.get("thread_id")

  context_variables["domain_id"] = domain_id
  return thread_id, agent_name, messages, context_variables

async def generate_stream(
  swarm_response: AsyncSwarmStreamingResponse,
  thread_id: str,
  messages: List[Message],
) -> AsyncGenerator[str, None]:
  supabase = get_supabase_client_from_context()
  async for chunk in swarm_response:
    if "sender" in chunk:
      chunk = cast(AsyncMessageStreamingChunk, chunk)
      data = [{"sender": chunk["sender"]}]

      # annotations
      yield f"8:{json.dumps(data)}\n"

    if "content" in chunk and cast(AsyncMessageStreamingChunk, chunk)["content"] is not None:
      chunk = cast(AsyncMessageStreamingChunk, chunk)
      if chunk["content"]:
        # text
        yield f"0:{json.dumps(str(chunk['content']))}\n"

    if "tool_calls" in chunk and cast(AsyncMessageStreamingChunk, chunk)["tool_calls"] is not None:
      for tool_call in cast(AsyncMessageStreamingChunk, chunk)["tool_calls"]:
        f = tool_call["function"]
        name = f["name"]
        if not name:
          continue
        tool_call_data = { "toolCallId": tool_call["id"], "toolName": name }

        # tool call
        yield f"9:{json.dumps(tool_call_data)}\n"

    if "delim" in chunk and cast(AsyncDelimStreamingChunk, chunk)["delim"] == "end":
      # end step
      step_data = { "finishReason": "stop", "isContinued": False }
      yield f"e:{json.dumps(step_data)}\n"

    if "partial_response" in chunk:
      chunk = cast(AsyncDeltaResponseStreamingChunk, chunk)
      await (
        supabase.table("thread_states").insert({
          "thread_id": thread_id,
          "messages": chunk["partial_response"].messages,
          "context_variables": context_variables_update_dict,
          "agent_name": chunk["partial_response"].agent.name if chunk["partial_response"].agent else None
        })
        .execute()
      )
      messages = chunk["partial_response"].messages
      for message in messages:
        if message['role'] == 'tool':
          tool_result_data = {
            'toolCallId': message["tool_call_id"],
            "result": message["content"]
          }
          yield f"a:{json.dumps(tool_result_data)}\n"

      context_variables_update_dict = json.loads(json.dumps(chunk["partial_response"].context_variables, default=pydantic_encoder))

      yield f"2:{json.dumps([{
        "type": "context_update",
        'context_variables': context_variables_update_dict
      }])}"

    if "response" in chunk:
      chunk = cast(AsyncResponseStreamingChunk, chunk)

      insert_state_response = await (
        supabase.table("thread_states").insert({
          "thread_id": thread_id,
          "messages": messages + chunk["response"].messages,
          "context_variables": json.loads(json.dumps(chunk["response"].context_variables, default=pydantic_encoder)),
          "agent_name": chunk["response"].agent.name if chunk["response"].agent else None
        })
        .execute()
      )
      assert insert_state_response.data is not None and len(insert_state_response.data) > 0, "Failed to insert thread state"

      last_known_good_thread_state_id = insert_state_response.data[0]["thread_state_id"]
      await (
        supabase.table("threads").update({
          "last_known_good_thread_state_id": last_known_good_thread_state_id
        })
        .eq("thread_id", thread_id)
        .execute()
      )

  response_data = { "finishReason": "stop" }
  # end message
  yield f"d:{json.dumps(response_data)}\n"

@router.post("/chat")
async def stream_messages(
  request: Request,
  protocol: Literal["data", "text"] = "data"
) -> StreamingResponse:
  supabase = get_supabase_client_from_context()
  if protocol == "text":
    raise HTTPException(
      status_code=400,
      detail="Text protocol not supported"
    )

  user_response = await supabase.auth.get_user()

  if user_response is None:
    raise HTTPException(
      status_code=401,
      detail="Unauthorized - User must be authenticated"
    )

  thread_id, agent_name, messages, context_variables = await get_thread_data(
    request.thread_id,
    user_response.user.id,
    request.domain_id
  )

  assert isinstance(context_variables, dict)
  assert isinstance(messages, list)

  messages.append({"role": "user", "content": request.message})
  swarm_response = await stream_response(messages, agent_name, context_variables)

  return StreamingResponse(
    generate_stream(swarm_response, thread_id, messages),
    media_type="text/event-stream",
    headers={
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "x-vercel-ai-data-stream": "v1"
    }
  )


