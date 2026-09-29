"""Conversation and response helpers for the AgentApp."""

from typing import Any
import os
from agent.evidence import EVIDENCE

from flwr.agentapp import AgentSession
from flwr.app import Context
from openai import OpenAI

MODEL = os.environ.get("CONNECTMESH_MODEL", "openai/gpt-5.6-sol")
STREAM_EVENT_TYPES = {
    "response.output_text.delta",
    "response.reasoning_summary_text.delta",
}

# This helps AgentApps construct reply messages correctly
AGENT_COLLABORATION_INSTRUCTIONS = (
    "The presence of src_node_id in the prompt means another agent sent the request; "
    "payload contains the assignment. Reply using push_reply_message with a string, "
    "once per request. Otherwise reply directly to the user. "
)
INSTRUCTIONS = (
    "You are ConnectMesh's experiment-evidence reviewer, not a bank investigator. "
    "Use the public aggregate evidence below. Do not invent training results or classify customers. "
    "For a user review request, discover available peers with Grid tools and request "
    "two complementary reviews if peers are available: numerical comparison and methodological challenge. "
    "Collect their replies, reconcile disagreements against evidence, then give a concise conclusion "
    "with peer node identifiers and an explicit collaboration status. "
    "If no peers are available or a call fails, state that limitation and mark the answer SOLO REVIEW. "
    "Never claim collaboration without actual replies. If this is a peer request, "
    "answer only the assigned review and return via push_reply_message; do not delegate recursively. "
    "Reviewers are model-generated perspectives, not independent human audits. "
    "A useful challenge should distinguish hypotheses from demonstrated causes. "
    "Only claim region-specific measured advantages supported by the bundled CSV; never a universal advantage, secure isolation, cloud training, or verified raw provenance. "
    "No raw transactions, credentials, filesystem access or external communications are needed. "
    "End with one next validation experiment, without changing the measured scores. "
    "PUBLIC EVIDENCE: " + EVIDENCE
)


def _message_text(content: Any) -> str:
    """Extract text from a trace message."""
    if isinstance(content, str):
        return content
    return "\n".join(part["text"] for part in content if "text" in part)


def _conversation(agent: AgentSession, context: Context) -> list[dict[str, str]]:
    """Rebuild user and assistant messages from this run series."""
    messages: list[dict[str, str]] = []
    current_prompt_seen = False
    for event in agent.events.get_trace():
        data = event["data"]
        if data.get("type") == "message" and data.get("role") in {"user", "assistant"}:
            text = _message_text(data["content"])
            messages.append({"type": "message", "role": data["role"], "content": text})
            current_prompt_seen |= (
                data["role"] == "user"
                and event.get("run_id") == context.run_id
                and text.strip() == agent.prompt.strip()
            )
        elif data.get("type") == "response.completed":
            for item in data["response"]["output"]:
                if item.get("type") == "message" and item.get("role") == "assistant":
                    messages.append(
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": _message_text(item["content"]),
                        }
                    )
    if not current_prompt_seen:
        messages.append(
            {"type": "message", "role": "user", "content": agent.prompt.strip()}
        )
    return messages


def _stream_response(
    client: OpenAI,
    agent: AgentSession,
    input_items: list[Any],
    tools: list[dict[str, Any]],
) -> tuple[Any, dict[str, Any]]:
    """Stream one model turn and return its completed response and event."""
    completed_response = None
    completed_event = None
    stream = client.responses.create(
        model=MODEL,
        reasoning={"effort": "medium"},
        input=input_items,
        instructions=AGENT_COLLABORATION_INSTRUCTIONS + INSTRUCTIONS,
        tools=tools,
        stream=True,
    )
    for event in stream:
        if event.type in STREAM_EVENT_TYPES:
            agent.events.emit(event.to_dict())
        elif event.type == "response.completed":
            completed_response = event.response
            completed_event = event.to_dict()

    if completed_response is None or completed_event is None:
        raise RuntimeError("Model response stream ended before completion")
    return completed_response, completed_event
