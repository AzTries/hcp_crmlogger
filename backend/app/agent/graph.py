import os
from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

from .tools import all_tools

load_dotenv()


class AgentState(TypedDict):
    """The state passed between nodes in the graph. Just a running message list."""
    messages: Annotated[list[BaseMessage], add_messages]


# LLM bound to our 5 tools - this is what lets it "decide" to call one
# llm = ChatGroq(model="gemma2-9b-it", api_key=os.getenv("GROQ_API_KEY")) // deprecated by Groq in favor of llama-3.1-8b-instant
# llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY")) // hit 25 laggraph cap easily cuz model didnt know when to stop so we upgraded to a bigger model
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
llm_with_tools = llm.bind_tools(all_tools)

SYSTEM_PROMPT = """You are an AI assistant embedded in a pharma CRM, helping
field reps log interactions with Healthcare Professionals (HCPs). You have
access to tools for logging interactions, editing them, detecting adverse
events, retrieving interaction history, searching interactions, and
suggesting follow-ups.

When a rep describes a NEW meeting in natural language, call log_interaction
ONCE to save it. After logging, note the interaction ID returned by log_interaction, then
call detect_adverse_event ONCE using that same ID and the same text, to
check for safety concerns.

When a rep asks to UPDATE, CHANGE, EDIT, or CORRECT an existing interaction
(e.g. "change that to Negative", "update the pricing meeting"), NEVER call
log_interaction. Instead, first call find_interaction using any HCP name or
keyword mentioned or implied by the conversation. If exactly one match is
found, call edit_interaction using its ID. If multiple matches are found, do
NOT guess - list them with their date and sentiment and ask the user which
one they mean, then wait for their reply.

If they ask about past meetings, use get_interaction_history. Never call the
same tool twice for the same user message. Once you have the information you
need, respond to the user directly in plain text - do not call further tools.
Be concise and confirm actions clearly."""


def call_model(state: AgentState):
    """Node: sends the current conversation to the LLM, gets back a response
    (which may include a request to call a tool)."""
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Conditional edge: checks if the LLM's last message requested a tool call.
    If yes, route to the tools node. If no, end the graph."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


# ---------- Build the graph ----------
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(all_tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")  # after running a tool, go back to the LLM

agent_graph = workflow.compile()