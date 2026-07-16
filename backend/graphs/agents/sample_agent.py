"""A minimal LangGraph agent example."""

from __future__ import annotations

from typing import TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - import guard for environments without langgraph
    END = "__end__"
    START = "__start__"
    StateGraph = None


class AgentState(TypedDict):
    message: str


def respond(state: AgentState) -> AgentState:
    return {"message": f"Agent received: {state['message']}"}


class SimpleAgent:
    def invoke(self, state: AgentState) -> AgentState:
        return respond(state)


def build_sample_agent():
    if StateGraph is None:
        return SimpleAgent()

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", respond)
    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", END)
    return workflow.compile()


def run_sample_agent(message: str = "Hello from LangGraph") -> str:
    agent = build_sample_agent()
    return agent.invoke({"message": message})["message"]
