from __future__ import annotations

"""A2A (Agent-to-Agent) Loop Orchestrator — reusable multi-round loop with confidence gate.

Formalizes the iterative loop pattern:
  Round N: call agents → collect outputs → evaluate confidence → continue or finalize

Used by website_overhaul_agent and designed to be inherited by future orchestrators.

Pattern:
    loop = A2ALoopOrchestrator(
        agents={"content_engine": ce_runner, "data_analyst": da_runner},
        termination_fn=my_confidence_check,
        max_iterations=3,
    )
    result = await loop.run(initial_query)
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from skills.utils.summarize import compress_round_output


@dataclass
class RoundResult:
    """Result of a single A2A loop iteration."""
    iteration: int
    agent_name: str
    raw_output: str
    compressed_output: str
    elapsed_seconds: float
    confidence_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopState:
    """Shared state across all A2A loop iterations — immune to history compression."""
    iterations: list[RoundResult] = field(default_factory=list)
    shared: dict[str, Any] = field(default_factory=dict)  # Cross-round data (pages, keywords, etc.)
    final_output: str = ""
    terminated_reason: str = ""
    total_elapsed_seconds: float = 0.0

    def set(self, key: str, value: Any) -> None:
        """Store a value in shared state (persists across rounds)."""
        self.shared[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from shared state."""
        return self.shared.get(key, default)

    def get_compressed_history(self, max_chars_per_round: int = 2000) -> str:
        """Return compressed history of all rounds for context injection."""
        parts = []
        for r in self.iterations:
            parts.append(
                f"=== Round {r.iteration} ({r.agent_name}, {r.elapsed_seconds:.1f}s) ===\n"
                f"{r.compressed_output[:max_chars_per_round]}"
            )
        return "\n\n".join(parts)


class A2ALoopOrchestrator:
    """Orchestrates multi-round Agent-to-Agent loops with a confidence gate.

    Args:
        agents: Dict mapping agent name → async callable (str) → str.
                The callable receives the query/prompt and returns the agent's output.
        termination_fn: Async function(state: LoopState) → (should_stop: bool, confidence: float, reason: str).
                        Called after each round to decide whether to continue.
        max_iterations: Hard cap on loop iterations (default 3).
        max_budget_seconds: Hard budget cap — stops loop if total elapsed exceeds this (default 1500s = 25min).
        compress_after_round: Whether to compress round outputs before storing (default True).
        summary_max_chars: Target chars for round compression (default 3000).
        improvement_threshold: Stop early if confidence improvement round-over-round < this (default 0.05).
    """

    def __init__(
        self,
        agents: dict[str, Callable[[str], Awaitable[str]]],
        termination_fn: Callable[[LoopState], Awaitable[tuple[bool, float, str]]],
        max_iterations: int = 3,
        max_budget_seconds: float = 1500.0,
        compress_after_round: bool = True,
        summary_max_chars: int = 3000,
        improvement_threshold: float = 0.05,
    ) -> None:
        self.agents = agents
        self.termination_fn = termination_fn
        self.max_iterations = max_iterations
        self.max_budget_seconds = max_budget_seconds
        self.compress_after_round = compress_after_round
        self.summary_max_chars = summary_max_chars
        self.improvement_threshold = improvement_threshold

    async def _call_agent(
        self,
        agent_name: str,
        prompt: str,
        iteration: int,
        state: LoopState,
    ) -> RoundResult:
        """Call a single agent and return a RoundResult."""
        runner = self.agents[agent_name]
        t0 = time.monotonic()
        try:
            # Inject shared state context into prompt
            context_injection = ""
            if state.shared:
                context_lines = []
                for k, v in state.shared.items():
                    if isinstance(v, (list, dict)):
                        val_str = json.dumps(v)[:500]
                    else:
                        val_str = str(v)[:500]
                    context_lines.append(f"  {k}: {val_str}")
                context_injection = "\n\n[Shared State from previous rounds]\n" + "\n".join(context_lines)

            if state.iterations:
                history = state.get_compressed_history(max_chars_per_round=1500)
                full_prompt = f"{prompt}{context_injection}\n\n[Previous Rounds Summary]\n{history}"
            else:
                full_prompt = f"{prompt}{context_injection}"

            raw = await asyncio.wait_for(runner(full_prompt), timeout=600.0)
        except asyncio.TimeoutError:
            raw = f"[TIMEOUT] Agent '{agent_name}' timed out after 600s in iteration {iteration}."
        except Exception as e:
            raw = f"[ERROR] Agent '{agent_name}' raised: {str(e)[:300]}"

        elapsed = time.monotonic() - t0

        # Compress output
        if self.compress_after_round and len(raw) > self.summary_max_chars:
            compressed = await compress_round_output(
                raw,
                context=f"Round {iteration}, agent={agent_name}",
                max_chars=self.summary_max_chars,
            )
        else:
            compressed = raw

        return RoundResult(
            iteration=iteration,
            agent_name=agent_name,
            raw_output=raw,
            compressed_output=compressed,
            elapsed_seconds=elapsed,
        )

    async def run(
        self,
        initial_prompt: str,
        agent_sequence: list[str] | None = None,
        initial_shared_state: dict[str, Any] | None = None,
    ) -> LoopState:
        """Execute the A2A loop.

        Args:
            initial_prompt: The starting query/task for the first agent.
            agent_sequence: Ordered list of agent names to call each iteration.
                            Defaults to all agents in registration order.
            initial_shared_state: Pre-populated shared state (e.g., page list from prioritizer).

        Returns:
            LoopState with all round results, shared state, and termination info.
        """
        state = LoopState(shared=initial_shared_state or {})
        sequence = agent_sequence or list(self.agents.keys())
        total_start = time.monotonic()
        prev_confidence = 0.0

        for iteration in range(1, self.max_iterations + 1):
            # Budget check
            elapsed_total = time.monotonic() - total_start
            if elapsed_total > self.max_budget_seconds:
                state.terminated_reason = f"Budget exceeded ({elapsed_total:.0f}s > {self.max_budget_seconds}s)"
                break

            # Build prompt for this iteration
            if iteration == 1:
                prompt = initial_prompt
            else:
                last_result = state.iterations[-1]
                prompt = (
                    f"{initial_prompt}\n\n"
                    f"[Previous round output from {last_result.agent_name}]\n"
                    f"{last_result.compressed_output[:2000]}\n\n"
                    f"Based on the above, continue with the next step."
                )

            # Call agents in sequence (each round may use a different agent)
            for agent_name in sequence:
                if agent_name not in self.agents:
                    continue

                result = await self._call_agent(agent_name, prompt, iteration, state)
                state.iterations.append(result)

                # Update prompt for next agent in same iteration
                prompt = (
                    f"{initial_prompt}\n\n"
                    f"[Output from {agent_name} (round {iteration})]\n"
                    f"{result.compressed_output[:2000]}\n\n"
                    f"Using this output, proceed with your role."
                )

            # Evaluate termination condition
            should_stop, confidence, reason = await self.termination_fn(state)
            state.iterations[-1].confidence_score = confidence

            # Early stop if confidence improvement is negligible
            improvement = confidence - prev_confidence
            if iteration > 1 and improvement < self.improvement_threshold:
                state.terminated_reason = (
                    f"Early stop: confidence improvement {improvement:.3f} < "
                    f"threshold {self.improvement_threshold} (confidence={confidence:.2f})"
                )
                break

            prev_confidence = confidence

            if should_stop:
                state.terminated_reason = reason
                break

            if iteration == self.max_iterations:
                state.terminated_reason = f"Reached max_iterations={self.max_iterations}"

        state.total_elapsed_seconds = time.monotonic() - total_start

        # Compile final output from last round
        if state.iterations:
            state.final_output = state.iterations[-1].raw_output

        return state

    def get_run_summary(self, state: LoopState) -> dict[str, Any]:
        """Build a summary dict suitable for logging or passing to review_packager."""
        return {
            "total_iterations": len(state.iterations),
            "total_elapsed_seconds": round(state.total_elapsed_seconds, 1),
            "terminated_reason": state.terminated_reason,
            "final_confidence": state.iterations[-1].confidence_score if state.iterations else 0.0,
            "rounds": [
                {
                    "iteration": r.iteration,
                    "agent": r.agent_name,
                    "elapsed_s": round(r.elapsed_seconds, 1),
                    "confidence": r.confidence_score,
                    "output_chars": len(r.raw_output),
                }
                for r in state.iterations
            ],
            "shared_state_keys": list(state.shared.keys()),
        }


# ─── Default Termination Functions ───────────────────────────────────────────

async def confidence_gate_90(state: LoopState) -> tuple[bool, float, str]:
    """Stop when the orchestrator's confidence score reaches ≥0.90.

    Reads 'confidence_score' from shared state (set by the orchestrator after each round).
    Falls back to 0.0 if not set.
    """
    confidence = float(state.shared.get("confidence_score", 0.0))
    if confidence >= 0.90:
        return True, confidence, f"Confidence gate passed ({confidence:.2f} ≥ 0.90)"
    return False, confidence, f"Confidence {confidence:.2f} < 0.90 — continuing"


async def fixed_rounds(state: LoopState) -> tuple[bool, float, str]:
    """Always run all max_iterations (no early stop). Useful for fixed workflows."""
    return False, 0.5, "Fixed rounds — no early termination"


async def quality_score_gate(state: LoopState) -> tuple[bool, float, str]:
    """Stop when page quality scores all reach ≥90/100.

    Reads 'quality_scores' list from shared state.
    """
    scores = state.shared.get("quality_scores", [])
    if not scores:
        return False, 0.0, "No quality scores yet"
    min_score = min(scores)
    confidence = min_score / 100.0
    if min_score >= 90:
        return True, confidence, f"All quality scores ≥ 90 (min={min_score})"
    return False, confidence, f"Min quality score {min_score} < 90 — needs another round"
