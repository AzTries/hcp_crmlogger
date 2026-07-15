from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from ..schemas import ChatRequest
from ..agent.graph import agent_graph

router = APIRouter()


@router.post("/chat")
def chat(payload: ChatRequest):
    """
    Send the full conversation history to the LangGraph agent, so it has
    context from earlier messages (e.g. answering a clarifying question).
    """
    lc_messages = []
    for m in payload.messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        else:
            lc_messages.append(AIMessage(content=m.content))

    result = agent_graph.invoke({"messages": lc_messages})
    final_message = result["messages"][-1]

    return {
        "reply": final_message.content,
        "tool_calls_made": [
            m.tool_calls for m in result["messages"]
            if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
        ],
    }