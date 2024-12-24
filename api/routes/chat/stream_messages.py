import json
from pydantic import BaseModel, TypeAdapter
from pydantic.json import pydantic_encoder
from typing import AsyncGenerator, List, Dict, Any, Literal, Optional, cast
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from supabase import AsyncClient

from api.agents.contexts import get_supabase_client_from_context
from api.agents.types import ContextVariables
from api.config import Settings
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

settings = Settings()

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
    context_variables_adapter = TypeAdapter(ContextVariables)
    context_variables = context_variables_adapter.validate_python(thread_state.get("context_variables", {}))
    thread_id = thread.get("thread_id")

  context_variables["domain_id"] = domain_id
  return thread_id, agent_name, messages, context_variables

async def generate_stream(
  swarm_response: AsyncSwarmStreamingResponse,
  thread_id: str,
  messages: List[Message],
) -> AsyncGenerator[str, None]:
  supabase = get_supabase_client_from_context()
  last_sender = None
  async for chunk in swarm_response:
    if "delim" in chunk:
      last_sender = None

    if "sender" in chunk:
      new_sender = await handle_sender_chunk(cast(AsyncMessageStreamingChunk, chunk))
      if new_sender != last_sender:
        yield new_sender
        last_sender = new_sender

    if "content" in chunk and cast(AsyncMessageStreamingChunk, chunk)["content"] is not None:
      yield await handle_content_chunk(cast(AsyncMessageStreamingChunk, chunk))

    if "tool_calls" in chunk and cast(AsyncMessageStreamingChunk, chunk)["tool_calls"] is not None:
      async for yield_data in handle_tool_calls_chunk(cast(AsyncMessageStreamingChunk, chunk)):
        yield yield_data

    if "partial_response" in chunk:
      async for yield_data in handle_partial_response_chunk(cast(AsyncDeltaResponseStreamingChunk, chunk), thread_id, supabase):
        yield yield_data

    if "response" in chunk:
      await handle_final_response_chunk(cast(AsyncResponseStreamingChunk, chunk), thread_id, messages, supabase)

  yield f"d:{json.dumps({ 'finishReason': 'stop' })}\n"

async def handle_sender_chunk(chunk: AsyncMessageStreamingChunk) -> str:
  data = [{"sender": chunk["sender"]}]
  return f"8:{json.dumps(data)}\n"

async def handle_content_chunk(chunk: AsyncMessageStreamingChunk) -> str:
  chunk = cast(AsyncMessageStreamingChunk, chunk)
  if chunk["content"]:
    return f"0:{json.dumps(str(chunk['content']))}\n"
  return ""

async def handle_tool_calls_chunk(chunk: AsyncMessageStreamingChunk) -> AsyncGenerator[str, None]:
  for tool_call in cast(AsyncMessageStreamingChunk, chunk)["tool_calls"]:
    f = tool_call["function"]
    name = f["name"]
    if not name:
      continue
    tool_call_data = {
      "toolCallId": tool_call["id"],
      "toolName": name,
      "args": {}
    }
    yield f"9:{json.dumps(tool_call_data)}\n"

async def handle_partial_response_chunk(
  chunk: AsyncDeltaResponseStreamingChunk,
  thread_id: str,
  supabase: AsyncClient
) -> AsyncGenerator[str, None]:
  chunk = cast(AsyncDeltaResponseStreamingChunk, chunk)
  response = chunk["partial_response"]
  context_variables_update = cast(ContextVariables, response.context_variables)
  context_variables_update_dict = json.loads(json.dumps(context_variables_update, default=pydantic_encoder))

  await save_thread_state(
    supabase,
    thread_id,
    response.messages,
    context_variables_update_dict,
    response.agent.name if response.agent else None
  )

  # Handle title updates if needed
  if len(context_variables_update.get("user_requirements") or []) > 0:
    title = (context_variables_update.get("user_requirements") or [])[0]
    await (
      supabase.table("threads").update({
        "title": title
      })
      .eq("thread_id", thread_id)
      .execute()
    )

    yield f"2:{json.dumps([{'type': 'thread_title', 'content': title}])}\n"

  # Handle tool results
  for message in response.messages:
    if message['role'] == 'tool':
      yield f"a:{json.dumps({'toolCallId': message['tool_call_id'], 'result': message['content']})}\n"

  # Yield step data
  yield f"e:{json.dumps({'finishReason': 'stop', 'isContinued': False})}\n"

  # Yield context update
  yield f"2:{json.dumps([{
    'type': 'context_delta',
    'content': context_variables_update_dict
  }])}\n"

async def handle_final_response_chunk(
  chunk: AsyncResponseStreamingChunk,
  thread_id: str,
  messages: List[Message],
  supabase: AsyncClient
) -> None:
  chunk = cast(AsyncResponseStreamingChunk, chunk)
  insert_state_response = await save_thread_state(
    supabase,
    thread_id,
    messages + chunk["response"].messages,
    json.loads(json.dumps(chunk["response"].context_variables, default=pydantic_encoder)),
    chunk["response"].agent.name if chunk["response"].agent else None
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

async def save_thread_state(
  supabase: AsyncClient,
  thread_id: str,
  messages: List[Message],
  context_variables: Dict[str, Any],
  agent_name: Optional[str]
) -> Any:
  return await (
    supabase.table("thread_states").insert({
      "thread_id": thread_id,
      "messages": messages,
      "context_variables": context_variables,
      "agent_name": agent_name
    })
    .execute()
  )

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
  swarm_response = await stream_response(messages, agent_name, context_variables, settings)

  return StreamingResponse(
    generate_stream(swarm_response, thread_id, messages),
    headers={
      "x-vercel-ai-data-stream": "v1",
    }
  )


