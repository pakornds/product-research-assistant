from typing import Annotated, Literal, TypedDict
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages

from src.tools.rag_tool import product_catalog_rag
from src.tools.search_tool import web_search
from src.tools.analysis_tool import price_analysis

# Load environment variables from a .env file if present (for GOOGLE_API_KEY / GEMINI_API_KEY)
load_dotenv()


# Define the state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# Define the tools
tools = [product_catalog_rag, web_search, price_analysis]

# Lazily initialize the model so imports (e.g., during tests) do not require API keys.
_model = None


def get_model():
    global _model
    if _model is None:
        _model = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview", temperature=0
        ).bind_tools(tools)
    return _model


def _render_content(content) -> str:
    """Normalize message content to string.

    LangChain/GenAI messages can return content as a string or a list of parts;
    this converts both to a plain string to avoid join/serialization errors.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part.get("text", "")))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


# Define the nodes
def agent(state: AgentState):
    messages = state["messages"]
    model = get_model()
    response = model.invoke(messages)
    return {"messages": [response]}


# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent)
workflow.add_node("tools", ToolNode(tools))

# Add edges
workflow.set_entry_point("agent")

# Conditional edge: check if the agent wants to call a tool
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# Edge from tools back to agent
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()


def run_agent(query: str):
    """Entry point to run the agent with a query."""
    system_prompt = SystemMessage(
        content="You are a helpful AI assistant. When you decide to use a tool, you MUST first explain your reasoning in the message content, and THEN call the tool."
    )
    inputs = {"messages": [system_prompt, HumanMessage(content=query)]}
    result = app.invoke(inputs)

    # Extract the final response
    last_message = result["messages"][-1]

    # Extract tools used and reasoning
    tools_used = set()
    reasoning_steps = []

    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            # Check for tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tools_used.add(tool_call["name"])
                # If the message has content along with tool calls, it's the reasoning
                if msg.content:
                    reasoning_steps.append(msg.content)

    # Normalize reasoning text and final answer to guard against list-based contents
    rendered_reasoning = [_render_content(c) for c in reasoning_steps]
    final_reasoning = (
        " -> ".join(rendered_reasoning)
        if rendered_reasoning
        else "Agent autonomously selected tools based on query content."
    )

    return {
        "answer": _render_content(last_message.content),
        "tools_used": list(tools_used),
        "reasoning": final_reasoning,
    }
