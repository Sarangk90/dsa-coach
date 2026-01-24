"""Helpers for choosing how a learning session should start (teach vs diagnose).

This is intentionally pure logic (no printing / file IO) so it can be tested and
reused from the CLI/mentor layers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

LearningStartMode = Literal["teach_first", "diagnose_first"]
LearningModeRequest = Literal[
    "ask",
    "auto",
    "llm",
    "teach_first",
    "diagnose_first",
]


def heuristic_learning_start_mode(progress: float) -> LearningStartMode:
    """Choose a reasonable start mode without prompting or LLM calls.

    Heuristic:
    - higher progress -> diagnose first (confirm + patch gaps fast)
    - lower progress  -> teach first (build the mental model)
    """
    # Treat unknown/negative as 0.
    prog = max(progress, 0.0)
    return "diagnose_first" if prog >= 60.0 else "teach_first"


def choose_learning_start_mode(
    *,
    request: LearningModeRequest,
    progress: float,
    interactive: bool,
    input_func: Callable[[str], str],
    llm_decider: Callable[[], LearningStartMode] | None,
) -> LearningStartMode | None:
    """Resolve a learning start mode.

    Args:
        request: Requested mode strategy:
            - "teach_first" / "diagnose_first": force mode
            - "auto": local heuristic
            - "llm": use llm_decider if provided else fallback to heuristic
            - "ask": prompt (if interactive) else fallback to heuristic
        progress: Pattern progress (0-100).
        interactive: Whether prompting is allowed.
        input_func: Function used to collect user input.
        llm_decider: Optional function that returns a mode using an LLM.

    Returns:
        Selected mode, or None if the user chose to quit.
    """
    if request in ("teach_first", "diagnose_first"):
        return request

    if request == "auto":
        return heuristic_learning_start_mode(progress)

    if request == "llm":
        if llm_decider is None:
            return heuristic_learning_start_mode(progress)
        try:
            mode = llm_decider()
        except Exception:
            return heuristic_learning_start_mode(progress)
        return (
            mode
            if mode in ("teach_first", "diagnose_first")
            else heuristic_learning_start_mode(progress)
        )

    if not interactive:
        return heuristic_learning_start_mode(progress)

    prompt = (
        "\nHow do you want to start this learning session?\n"
        "  [D] Diagnose-first (quiz me, then fill gaps)\n"
        "  [T] Teach-first (explain briefly, then quiz + practice)\n"
        "  [A] Auto (use progress heuristic)  [default]\n"
        "  [L] Let the LLM decide\n"
        "  [Q] Quit\n"
        "Choice: "
    )

    while True:
        raw = input_func(prompt).strip().lower()
        if raw == "":
            return heuristic_learning_start_mode(progress)
        if raw in ("d", "diagnose"):
            return "diagnose_first"
        if raw in ("t", "teach"):
            return "teach_first"
        if raw in ("a", "auto"):
            return heuristic_learning_start_mode(progress)
        if raw in ("l", "llm"):
            if llm_decider is None:
                return heuristic_learning_start_mode(progress)
            try:
                mode = llm_decider()
            except Exception:
                return heuristic_learning_start_mode(progress)
            return (
                mode
                if mode in ("teach_first", "diagnose_first")
                else heuristic_learning_start_mode(progress)
            )
        if raw in ("q", "quit", "exit"):
            return None
