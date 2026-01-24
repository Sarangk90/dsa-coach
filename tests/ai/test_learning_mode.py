from __future__ import annotations

from collections.abc import Callable


def _fake_input(responses: list[str]) -> Callable[[str], str]:
    it = iter(responses)

    def _inp(_: str) -> str:
        return next(it)

    return _inp


def test_choose_mode_forced_modes_do_not_prompt() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    called = {"input": 0, "llm": 0}

    def inp(_: str) -> str:
        called["input"] += 1
        return "d"

    def llm() -> str:
        called["llm"] += 1
        return "teach_first"

    assert (
        choose_learning_start_mode(
            request="diagnose_first",
            progress=80.0,
            interactive=True,
            input_func=inp,
            llm_decider=llm,
        )
        == "diagnose_first"
    )
    assert called == {"input": 0, "llm": 0}

    assert (
        choose_learning_start_mode(
            request="teach_first",
            progress=10.0,
            interactive=True,
            input_func=inp,
            llm_decider=llm,
        )
        == "teach_first"
    )
    assert called == {"input": 0, "llm": 0}


def test_choose_mode_auto_uses_heuristic_and_never_prompts() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    called = {"input": 0}

    def inp(_: str) -> str:
        called["input"] += 1
        return "t"

    assert (
        choose_learning_start_mode(
            request="auto",
            progress=0.0,
            interactive=True,
            input_func=inp,
            llm_decider=None,
        )
        == "teach_first"
    )
    assert (
        choose_learning_start_mode(
            request="auto",
            progress=85.0,
            interactive=True,
            input_func=inp,
            llm_decider=None,
        )
        == "diagnose_first"
    )
    assert called["input"] == 0


def test_choose_mode_llm_uses_llm_decider_and_falls_back_when_missing() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    called = {"llm": 0}

    def llm() -> str:
        called["llm"] += 1
        return "diagnose_first"

    assert (
        choose_learning_start_mode(
            request="llm",
            progress=10.0,
            interactive=False,
            input_func=_fake_input([]),
            llm_decider=llm,
        )
        == "diagnose_first"
    )
    assert called["llm"] == 1

    # Missing LLM decider -> fallback to heuristic
    assert (
        choose_learning_start_mode(
            request="llm",
            progress=10.0,
            interactive=False,
            input_func=_fake_input([]),
            llm_decider=None,
        )
        == "teach_first"
    )


def test_choose_mode_ask_interactive_accepts_inputs_and_default() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    # Default (empty) -> auto heuristic
    assert (
        choose_learning_start_mode(
            request="ask",
            progress=75.0,
            interactive=True,
            input_func=_fake_input([""]),
            llm_decider=None,
        )
        == "diagnose_first"
    )

    assert (
        choose_learning_start_mode(
            request="ask",
            progress=20.0,
            interactive=True,
            input_func=_fake_input(["t"]),
            llm_decider=None,
        )
        == "teach_first"
    )

    assert (
        choose_learning_start_mode(
            request="ask",
            progress=80.0,
            interactive=True,
            input_func=_fake_input(["d"]),
            llm_decider=None,
        )
        == "diagnose_first"
    )


def test_choose_mode_ask_non_interactive_falls_back_to_heuristic() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    called = {"input": 0}

    def inp(_: str) -> str:
        called["input"] += 1
        return "t"

    assert (
        choose_learning_start_mode(
            request="ask",
            progress=10.0,
            interactive=False,
            input_func=inp,
            llm_decider=None,
        )
        == "teach_first"
    )
    assert called["input"] == 0


def test_choose_mode_ask_can_quit() -> None:
    from dsa_coach.ai.learning_mode import choose_learning_start_mode

    assert (
        choose_learning_start_mode(
            request="ask",
            progress=10.0,
            interactive=True,
            input_func=_fake_input(["q"]),
            llm_decider=None,
        )
        is None
    )
