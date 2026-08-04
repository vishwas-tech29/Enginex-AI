import logging

from langgraph.graph import END, StateGraph

from app.ai.agents.state import AgentState
from app.ai.providers.base import LLMMessage
from app.ai.providers.router import LLMRouter
from app.ai.tools.context import ToolContext
from app.ai.tools.registry import ToolRegistry
from app.config import settings

logger = logging.getLogger("enginex.ai.agent")

MAX_TOOL_ROUNDS = 3


class BaseAgent:
    """An engineering agent: a system prompt + a role's tools, run through a
    small LangGraph workflow (understand -> plan -> execute tools -> review).

    Single-pass by design (no review->execute loop-back) — a real LLM call
    per node already makes multi-round loops slow/costly, and an
    LLM-judged "is this acceptable?" gate is exactly the kind of condition
    that can silently never trigger and loop forever. Bounded, predictable,
    finite beats clever here.
    """

    def __init__(
        self,
        key: str,
        name: str,
        role: str,
        system_prompt: str,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry,
    ):
        self.key = key
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm_router = llm_router
        self.tool_registry = tool_registry
        self.model = settings.ai_default_model
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("understand", self._understand_task)
        graph.add_node("plan", self._plan_steps)
        graph.add_node("execute", self._execute_tools)
        graph.add_node("output", self._generate_output)

        graph.set_entry_point("understand")
        graph.add_edge("understand", "plan")
        graph.add_conditional_edges(
            "plan", self._should_execute_tools, {True: "execute", False: "output"}
        )
        graph.add_edge("execute", "output")
        graph.add_edge("output", END)
        return graph.compile()

    async def _emit(self, state: AgentState, event_type: str, **fields) -> None:
        on_event = state["context"].get("_on_event")
        if on_event is not None:
            await on_event({"type": event_type, "agent": self.name, **fields})

    def _track_usage(self, state: AgentState, response) -> dict:
        return {
            "tokens_used": {
                "input": state["tokens_used"]["input"] + response.tokens_used.get("input", 0),
                "output": state["tokens_used"]["output"] + response.tokens_used.get("output", 0),
            },
            "cost": state["cost"] + response.cost,
        }

    async def _understand_task(self, state: AgentState) -> dict:
        await self._emit(state, "agent_started")
        prompt = (
            f"{self.system_prompt}\n\nUser task: {state['task']}\n"
            f"Context: {state['context']}\n\n"
            "In 2-3 sentences, state what needs to be accomplished and any "
            "constraints you should respect."
        )
        response = await self.llm_router.call_model(
            model=self.model,
            messages=[LLMMessage(role="system", content=self.system_prompt), LLMMessage(role="user", content=prompt)],
            temperature=0.4,
        )
        return {
            "reasoning": response.content,
            "messages": state["messages"] + [LLMMessage(role="assistant", content=response.content)],
            **self._track_usage(state, response),
        }

    async def _plan_steps(self, state: AgentState) -> dict:
        available_tools = self.tool_registry.get_tools_for_role(self.role)
        tool_names = ", ".join(t["name"] for t in available_tools) or "none"
        prompt = (
            f"Understanding so far: {state['reasoning']}\n\n"
            f"Available tools: {tool_names}\n\n"
            "List the concrete steps you'll take. If tools are needed, name "
            "which ones and why."
        )
        response = await self.llm_router.call_model(
            model=self.model,
            messages=state["messages"] + [LLMMessage(role="user", content=prompt)],
            temperature=0.4,
        )
        return {
            "messages": state["messages"] + [LLMMessage(role="assistant", content=response.content)],
            **self._track_usage(state, response),
        }

    def _should_execute_tools(self, state: AgentState) -> bool:
        return len(self.tool_registry.get_tools_for_role(self.role)) > 0

    async def _execute_tools(self, state: AgentState) -> dict:
        available_tools = self.tool_registry.get_tools_for_role(self.role)
        prompt = "Call the tools you need to accomplish the plan. If no tool call is needed, say so."

        response = await self.llm_router.call_model(
            model=self.model,
            messages=state["messages"] + [LLMMessage(role="user", content=prompt)],
            tools=available_tools,
            temperature=0.2,
        )

        tools_used = list(state["tools_used"])
        tool_ctx: ToolContext | None = state["context"].get("_tool_ctx")
        for call in response.tool_calls[:MAX_TOOL_ROUNDS]:
            tool_name, args = call["name"], call["arguments"]
            await self._emit(state, "tool_called", tool=tool_name, args=args)

            if not self.tool_registry.has_access(self.role, tool_name):
                outcome_entry = {"tool": tool_name, "error": "not permitted for this agent role"}
            elif tool_ctx is None:
                outcome_entry = {"tool": tool_name, "error": "no execution context available"}
            else:
                outcome = await self.tool_registry.execute_tool(tool_name, tool_ctx, **args)
                outcome_entry = {"tool": tool_name, "args": args, **outcome}

            tools_used.append(outcome_entry)
            await self._emit(state, "tool_result", tool=tool_name, result=outcome_entry)

        return {
            "tools_used": tools_used,
            "messages": state["messages"] + [LLMMessage(role="assistant", content=response.content)],
            **self._track_usage(state, response),
        }

    async def _generate_output(self, state: AgentState) -> dict:
        await self._emit(state, "agent_completed")
        prompt = (
            "Summarize what you accomplished in a short, clear message for "
            f"the user. Tools used: {state['tools_used']}"
        )
        response = await self.llm_router.call_model(
            model=self.model,
            messages=state["messages"] + [LLMMessage(role="user", content=prompt)],
            temperature=0.5,
        )
        usage = self._track_usage(state, response)
        return {"result": response.content, **usage}

    async def run(self, task: str, context: dict | None = None) -> AgentState:
        initial_state: AgentState = {
            "task": task,
            "context": context or {},
            "messages": [],
            "tools_used": [],
            "reasoning": "",
            "result": "",
            "tokens_used": {"input": 0, "output": 0},
            "cost": 0.0,
        }
        return await self.graph.ainvoke(initial_state)
