"""
Thread-Based Engineering Module for Kaedra
Based on Andy Devdan's framework: https://www.youtube.com/watch?v=-WBHNFAB0OE

Thread Types:
- Base Thread: Prompt → Agent Work → Review
- P-Thread: Parallel execution
- C-Thread: Chained phases with checkpoints
- F-Thread: Fusion (same prompt to multiple agents, combine results)
- B-Thread: Big/Orchestrated (agents prompting agents)
- L-Thread: Long-duration autonomous work with validation loops
- Z-Thread: Zero-touch (maximum trust, no review)
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, List, Dict, TypeVar, Generic
from enum import Enum
import logging

log = logging.getLogger("kaedra.threads")

T = TypeVar("T")


class ThreadStatus(Enum):
    """Status of a thread of work."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"


@dataclass
class ThreadResult(Generic[T]):
    """Result of a thread execution."""
    status: ThreadStatus
    result: Optional[T] = None
    error: Optional[str] = None
    tool_calls: int = 0
    duration_s: float = 0.0
    iterations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str = ""
    should_continue: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseThread(ABC):
    """
    Base Thread: The fundamental unit of work.
    Prompt → Agent Work (tool calls) → Review
    """

    def __init__(self, name: str = "base_thread"):
        self.name = name
        self.status = ThreadStatus.PENDING
        self.tool_calls = 0
        self.start_time: Optional[float] = None

    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> ThreadResult:
        """Execute the thread of work."""
        pass


class LThreadRunner:
    """
    L-Thread: Long-duration autonomous work with validation loops.

    This implements the "Ralph Wiggum" pattern:
    - Run agent work
    - Validate results
    - Loop until validation passes or max iterations reached

    The key insight: agents + deterministic code loops = long-running autonomy
    """

    def __init__(
        self,
        agent_fn: Callable[[str], Any],
        validator_fn: Callable[[Any], ValidationResult],
        max_iterations: int = 100,
        timeout_s: float = 3600.0,  # 1 hour default
        checkpoint_fn: Optional[Callable[[Any, int], None]] = None,
        on_iteration: Optional[Callable[[int, Any], None]] = None,
    ):
        """
        Initialize the L-Thread runner.

        Args:
            agent_fn: Function that executes agent work (prompt -> result)
            validator_fn: Function that validates results (result -> ValidationResult)
            max_iterations: Maximum loop iterations before stopping
            timeout_s: Maximum runtime in seconds
            checkpoint_fn: Optional checkpoint function called after each iteration
            on_iteration: Optional callback after each iteration
        """
        self.agent_fn = agent_fn
        self.validator_fn = validator_fn
        self.max_iterations = max_iterations
        self.timeout_s = timeout_s
        self.checkpoint_fn = checkpoint_fn
        self.on_iteration = on_iteration
        self.status = ThreadStatus.PENDING

    async def run(self, initial_prompt: str, **kwargs) -> ThreadResult:
        """
        Run the L-thread until validation passes or limits reached.

        This is the core Ralph Wiggum loop:
        1. Execute agent work
        2. Validate result
        3. If validation fails and should_continue, loop
        4. Checkpoint state for recovery
        """
        self.status = ThreadStatus.RUNNING
        start_time = time.time()
        iteration = 0
        last_result = None
        total_tool_calls = 0

        try:
            while iteration < self.max_iterations:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.timeout_s:
                    log.warning(f"L-Thread timeout after {elapsed:.1f}s")
                    return ThreadResult(
                        status=ThreadStatus.FAILED,
                        result=last_result,
                        error=f"Timeout after {elapsed:.1f}s",
                        tool_calls=total_tool_calls,
                        duration_s=elapsed,
                        iterations=iteration,
                    )

                # Execute agent work
                iteration += 1
                log.info(f"L-Thread iteration {iteration}/{self.max_iterations}")

                try:
                    if asyncio.iscoroutinefunction(self.agent_fn):
                        last_result = await self.agent_fn(initial_prompt, **kwargs)
                    else:
                        last_result = self.agent_fn(initial_prompt, **kwargs)

                    # Track tool calls if result has that info
                    if hasattr(last_result, "tool_calls"):
                        total_tool_calls += last_result.tool_calls
                    else:
                        total_tool_calls += 1  # Assume at least one

                except Exception as e:
                    log.error(f"L-Thread agent error: {e}")
                    last_result = {"error": str(e)}

                # Validate result
                self.status = ThreadStatus.VALIDATING
                try:
                    if asyncio.iscoroutinefunction(self.validator_fn):
                        validation = await self.validator_fn(last_result)
                    else:
                        validation = self.validator_fn(last_result)
                except Exception as e:
                    log.error(f"L-Thread validation error: {e}")
                    validation = ValidationResult(passed=False, message=str(e), should_continue=True)

                # Checkpoint if provided
                if self.checkpoint_fn:
                    try:
                        self.checkpoint_fn(last_result, iteration)
                    except Exception as e:
                        log.warning(f"Checkpoint failed: {e}")

                # Callback if provided
                if self.on_iteration:
                    try:
                        self.on_iteration(iteration, last_result)
                    except Exception:
                        pass

                # Check validation result
                if validation.passed:
                    self.status = ThreadStatus.COMPLETED
                    elapsed = time.time() - start_time
                    log.info(f"L-Thread completed in {iteration} iterations, {elapsed:.1f}s")
                    return ThreadResult(
                        status=ThreadStatus.COMPLETED,
                        result=last_result,
                        tool_calls=total_tool_calls,
                        duration_s=elapsed,
                        iterations=iteration,
                        metadata={"validation_message": validation.message},
                    )

                # Check if we should continue
                if not validation.should_continue:
                    self.status = ThreadStatus.FAILED
                    elapsed = time.time() - start_time
                    return ThreadResult(
                        status=ThreadStatus.FAILED,
                        result=last_result,
                        error=f"Validation stopped: {validation.message}",
                        tool_calls=total_tool_calls,
                        duration_s=elapsed,
                        iterations=iteration,
                    )

                self.status = ThreadStatus.RUNNING

            # Max iterations reached
            self.status = ThreadStatus.FAILED
            elapsed = time.time() - start_time
            return ThreadResult(
                status=ThreadStatus.FAILED,
                result=last_result,
                error=f"Max iterations ({self.max_iterations}) reached",
                tool_calls=total_tool_calls,
                duration_s=elapsed,
                iterations=iteration,
            )

        except Exception as e:
            self.status = ThreadStatus.FAILED
            elapsed = time.time() - start_time
            return ThreadResult(
                status=ThreadStatus.FAILED,
                error=str(e),
                tool_calls=total_tool_calls,
                duration_s=elapsed,
                iterations=iteration,
            )


class PThreadRunner:
    """
    P-Thread: Parallel execution of multiple agents.

    Run the same or different prompts across multiple agents simultaneously.
    """

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent

    async def run_parallel(
        self,
        agent_fns: List[Callable[[str], Any]],
        prompts: List[str],
    ) -> List[ThreadResult]:
        """
        Run multiple agents in parallel.

        Args:
            agent_fns: List of agent functions to run
            prompts: List of prompts (must match length of agent_fns, or single prompt for all)
        """
        if len(prompts) == 1:
            prompts = prompts * len(agent_fns)

        if len(prompts) != len(agent_fns):
            raise ValueError("Number of prompts must match number of agents or be 1")

        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_semaphore(agent_fn, prompt, index):
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(agent_fn):
                        result = await agent_fn(prompt)
                    else:
                        result = await asyncio.to_thread(agent_fn, prompt)
                    return ThreadResult(
                        status=ThreadStatus.COMPLETED,
                        result=result,
                        tool_calls=1,
                        duration_s=time.time() - start_time,
                        metadata={"index": index},
                    )
                except Exception as e:
                    return ThreadResult(
                        status=ThreadStatus.FAILED,
                        error=str(e),
                        duration_s=time.time() - start_time,
                        metadata={"index": index},
                    )

        tasks = [
            run_with_semaphore(agent_fn, prompt, i)
            for i, (agent_fn, prompt) in enumerate(zip(agent_fns, prompts))
        ]

        results = await asyncio.gather(*tasks)
        return results


class FThreadRunner:
    """
    F-Thread: Fusion thread - same prompt to multiple agents, fuse best results.

    This is the "best of N" pattern for increased confidence.
    """

    def __init__(
        self,
        agent_fns: List[Callable[[str], Any]],
        fusion_fn: Optional[Callable[[List[Any]], Any]] = None,
    ):
        """
        Initialize fusion thread.

        Args:
            agent_fns: List of agent functions to run
            fusion_fn: Function to combine results (default: pick most common)
        """
        self.agent_fns = agent_fns
        self.fusion_fn = fusion_fn or self._default_fusion
        self.pthread = PThreadRunner(max_concurrent=len(agent_fns))

    def _default_fusion(self, results: List[Any]) -> Any:
        """Default fusion: return all results for manual selection."""
        return {
            "all_results": results,
            "count": len(results),
            "first": results[0] if results else None,
        }

    async def fuse(self, prompt: str) -> ThreadResult:
        """
        Run the same prompt through all agents and fuse results.
        """
        start_time = time.time()

        # Run all agents in parallel
        results = await self.pthread.run_parallel(
            self.agent_fns,
            [prompt],  # Same prompt for all
        )

        # Extract successful results
        successful = [r.result for r in results if r.status == ThreadStatus.COMPLETED]
        failed_count = len(results) - len(successful)

        if not successful:
            return ThreadResult(
                status=ThreadStatus.FAILED,
                error="All agents failed",
                tool_calls=len(results),
                duration_s=time.time() - start_time,
            )

        # Fuse results
        try:
            fused = self.fusion_fn(successful)
        except Exception as e:
            return ThreadResult(
                status=ThreadStatus.FAILED,
                error=f"Fusion failed: {e}",
                result={"raw_results": successful},
                tool_calls=len(results),
                duration_s=time.time() - start_time,
            )

        return ThreadResult(
            status=ThreadStatus.COMPLETED,
            result=fused,
            tool_calls=len(results),
            duration_s=time.time() - start_time,
            metadata={
                "successful_agents": len(successful),
                "failed_agents": failed_count,
            },
        )


class CThreadRunner:
    """
    C-Thread: Chained thread - work broken into phases with checkpoints.

    Perfect for high-stakes work that needs verification at each step.
    """

    @dataclass
    class Phase:
        name: str
        agent_fn: Callable[[str, Any], Any]
        validator_fn: Optional[Callable[[Any], ValidationResult]] = None

    def __init__(self, phases: List["CThreadRunner.Phase"]):
        self.phases = phases

    async def run_chained(
        self,
        initial_prompt: str,
        on_phase_complete: Optional[Callable[[str, Any], None]] = None,
    ) -> ThreadResult:
        """
        Run phases sequentially with validation between each.
        """
        start_time = time.time()
        current_context = None
        total_tool_calls = 0

        for i, phase in enumerate(self.phases):
            log.info(f"C-Thread phase {i+1}/{len(self.phases)}: {phase.name}")

            try:
                # Execute phase
                if asyncio.iscoroutinefunction(phase.agent_fn):
                    result = await phase.agent_fn(initial_prompt, current_context)
                else:
                    result = phase.agent_fn(initial_prompt, current_context)

                total_tool_calls += 1
                current_context = result

                # Validate if validator provided
                if phase.validator_fn:
                    if asyncio.iscoroutinefunction(phase.validator_fn):
                        validation = await phase.validator_fn(result)
                    else:
                        validation = phase.validator_fn(result)

                    if not validation.passed:
                        return ThreadResult(
                            status=ThreadStatus.FAILED,
                            result=result,
                            error=f"Phase '{phase.name}' validation failed: {validation.message}",
                            tool_calls=total_tool_calls,
                            duration_s=time.time() - start_time,
                            iterations=i + 1,
                        )

                # Callback
                if on_phase_complete:
                    on_phase_complete(phase.name, result)

            except Exception as e:
                return ThreadResult(
                    status=ThreadStatus.FAILED,
                    error=f"Phase '{phase.name}' failed: {e}",
                    tool_calls=total_tool_calls,
                    duration_s=time.time() - start_time,
                    iterations=i + 1,
                )

        return ThreadResult(
            status=ThreadStatus.COMPLETED,
            result=current_context,
            tool_calls=total_tool_calls,
            duration_s=time.time() - start_time,
            iterations=len(self.phases),
        )


# Convenience factory functions
def create_lthread(
    agent_fn: Callable[[str], Any],
    validator_fn: Callable[[Any], ValidationResult],
    **kwargs,
) -> LThreadRunner:
    """Create an L-Thread runner for long-running autonomous work."""
    return LThreadRunner(agent_fn, validator_fn, **kwargs)


def create_pthread(max_concurrent: int = 5) -> PThreadRunner:
    """Create a P-Thread runner for parallel agent execution."""
    return PThreadRunner(max_concurrent)


def create_fthread(
    agent_fns: List[Callable[[str], Any]],
    fusion_fn: Optional[Callable[[List[Any]], Any]] = None,
) -> FThreadRunner:
    """Create an F-Thread runner for fusion/best-of-N patterns."""
    return FThreadRunner(agent_fns, fusion_fn)


class RalphRunner:
    """
    Ralph Wiggum Pattern Runner.

    Based on https://ghuntley.com/ralph/
    Core pattern: while :; do cat PROMPT.md | claude-code ; done

    Key insights from repomirror:
    - Simple prompts work better (103 words > 1,500 words)
    - Use .agent/ scratchpad for TODO.md and long-term plans
    - Commit after every edit for recovery
    - Agent can self-terminate when done
    - ~$10.50/hour with Sonnet overnight
    """

    def __init__(
        self,
        prompt_file: str,
        agent_fn: Callable[[str], Any],
        scratchpad_dir: str = ".agent",
        max_iterations: int = 1000,
        timeout_hours: float = 24.0,
        on_iteration: Optional[Callable[[int, Any], None]] = None,
        done_detector: Optional[Callable[[Any], bool]] = None,
    ):
        """
        Initialize Ralph runner.

        Args:
            prompt_file: Path to PROMPT.md file
            agent_fn: Function to execute agent (prompt -> result)
            scratchpad_dir: Directory for agent notes/TODO.md
            max_iterations: Max loop iterations
            timeout_hours: Max runtime in hours
            on_iteration: Callback after each iteration
            done_detector: Function to detect if agent is "done" (early stopping)
        """
        self.prompt_file = prompt_file
        self.agent_fn = agent_fn
        self.scratchpad_dir = scratchpad_dir
        self.max_iterations = max_iterations
        self.timeout_s = timeout_hours * 3600
        self.on_iteration = on_iteration
        self.done_detector = done_detector or self._default_done_detector
        self.status = ThreadStatus.PENDING

    def _default_done_detector(self, result: Any) -> bool:
        """Default: never early stop (run until max iterations)."""
        return False

    def _read_prompt(self) -> str:
        """Read the prompt file."""
        from pathlib import Path
        prompt_path = Path(self.prompt_file)
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return ""

    def _ensure_scratchpad(self):
        """Ensure scratchpad directory exists."""
        from pathlib import Path
        Path(self.scratchpad_dir).mkdir(parents=True, exist_ok=True)
        todo_path = Path(self.scratchpad_dir) / "TODO.md"
        if not todo_path.exists():
            todo_path.write_text("# Agent TODO\n\n- [ ] Start work\n", encoding="utf-8")

    async def run(self, **kwargs) -> ThreadResult:
        """
        Run the Ralph loop until done or limits reached.

        This is the core: while :; do cat PROMPT.md | agent ; done
        """
        self.status = ThreadStatus.RUNNING
        self._ensure_scratchpad()
        start_time = time.time()
        iteration = 0
        last_result = None
        total_tool_calls = 0

        try:
            while iteration < self.max_iterations:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.timeout_s:
                    log.warning(f"Ralph timeout after {elapsed/3600:.1f}h")
                    return ThreadResult(
                        status=ThreadStatus.COMPLETED,
                        result=last_result,
                        tool_calls=total_tool_calls,
                        duration_s=elapsed,
                        iterations=iteration,
                        metadata={"reason": "timeout"},
                    )

                # Read prompt (may be updated between iterations)
                prompt = self._read_prompt()
                if not prompt:
                    log.warning("Empty prompt file, stopping")
                    break

                # Execute agent
                iteration += 1
                log.info(f"Ralph iteration {iteration}/{self.max_iterations}")

                try:
                    if asyncio.iscoroutinefunction(self.agent_fn):
                        last_result = await self.agent_fn(prompt, **kwargs)
                    else:
                        last_result = self.agent_fn(prompt, **kwargs)
                    total_tool_calls += 1
                except Exception as e:
                    log.error(f"Ralph agent error: {e}")
                    last_result = {"error": str(e)}

                # Callback
                if self.on_iteration:
                    try:
                        self.on_iteration(iteration, last_result)
                    except Exception:
                        pass

                # Check for early stopping (agent declared "done")
                if self.done_detector(last_result):
                    self.status = ThreadStatus.COMPLETED
                    elapsed = time.time() - start_time
                    log.info(f"Ralph completed (early stop) in {iteration} iterations")
                    return ThreadResult(
                        status=ThreadStatus.COMPLETED,
                        result=last_result,
                        tool_calls=total_tool_calls,
                        duration_s=elapsed,
                        iterations=iteration,
                        metadata={"reason": "done_detected"},
                    )

            # Max iterations reached
            self.status = ThreadStatus.COMPLETED
            elapsed = time.time() - start_time
            return ThreadResult(
                status=ThreadStatus.COMPLETED,
                result=last_result,
                tool_calls=total_tool_calls,
                duration_s=elapsed,
                iterations=iteration,
                metadata={"reason": "max_iterations"},
            )

        except Exception as e:
            self.status = ThreadStatus.FAILED
            elapsed = time.time() - start_time
            return ThreadResult(
                status=ThreadStatus.FAILED,
                error=str(e),
                tool_calls=total_tool_calls,
                duration_s=elapsed,
                iterations=iteration,
            )


def create_ralph(
    prompt_file: str,
    agent_fn: Callable[[str], Any],
    **kwargs,
) -> RalphRunner:
    """
    Create a Ralph Wiggum runner for infinite loop work.

    Usage:
        ralph = create_ralph("PROMPT.md", my_agent_fn)
        result = await ralph.run()
    """
    return RalphRunner(prompt_file, agent_fn, **kwargs)
