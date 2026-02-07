"""Interactive learning session functionality for DSA Coach."""

import contextlib
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .client import get_ai_response
from .prompts import (
    LEARNING_SESSION_DIAGNOSE_INTRO,
    LEARNING_SESSION_INTRO,
    SYSTEM_DESIGN_PROMPT,
    get_mentor_system_prompt,
)
from .session import load_conversation, save_conversation
from .ui import print_ai_response


def start_learning_session(
    pattern: str, progress: dict[str, Any], mode: str = "teach_first"
) -> tuple[list[dict[str, str]], str]:
    """Start an interactive learning session for a pattern.

    Args:
        pattern: Pattern to learn.
        progress: User progress dict.
        mode: "teach_first" or "diagnose_first".

    Returns:
        Tuple of (messages, response)
    """
    pattern_title = pattern.replace("_", " ").title()
    if mode == "diagnose_first":
        user_message = LEARNING_SESSION_DIAGNOSE_INTRO.format(pattern=pattern_title)
        first_user_content = f"Diagnose my understanding of {pattern}"
    else:
        user_message = LEARNING_SESSION_INTRO.format(pattern=pattern_title)
        first_user_content = f"Teach me {pattern}"

    system_prompt = get_mentor_system_prompt(progress)

    try:
        response = get_ai_response(
            user_message=user_message, system_prompt=system_prompt, max_tokens=800
        )
        messages = [
            {"role": "user", "content": first_user_content},
            {"role": "assistant", "content": response},
        ]
        return messages, response
    except Exception as e:
        return [], f"Error starting learning session: {e}"


def start_design_session(
    topic: str, progress: dict[str, Any]
) -> tuple[list[dict[str, str]], str]:
    """Start a system design interview session.

    Args:
        topic: System design topic
        progress: User progress dict

    Returns:
        Tuple of (messages, response)
    """
    user_message = SYSTEM_DESIGN_PROMPT.format(topic=topic)
    system_prompt = get_mentor_system_prompt(progress)

    try:
        response = get_ai_response(user_message, system_prompt, max_tokens=800)
        messages = [
            {"role": "user", "content": f"Design {topic}"},
            {"role": "assistant", "content": response},
        ]
        return messages, response
    except Exception as e:
        return [], f"Error starting design session: {e}"


def continue_conversation(
    messages: list[dict[str, str]], user_input: str, progress: dict[str, Any]
) -> tuple[list[dict[str, str]], str]:
    """Continue an ongoing conversation.

    Args:
        messages: Existing conversation messages
        user_input: User's input
        progress: User progress dict

    Returns:
        Tuple of (updated_messages, response)
    """
    system_prompt = get_mentor_system_prompt(progress)

    try:
        # Extract just the content for conversation history
        history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        response = get_ai_response(
            user_input, system_prompt, max_tokens=800, conversation_history=history
        )

        # Append to messages
        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": response})

        return messages, response
    except Exception as e:
        return messages, f"Error continuing conversation: {e}"


def _read_multiline_natural(prompt_text: str = "› ") -> str | None:
    """Natural multiline input with full editing capabilities.

    Args:
        prompt_text: Prompt to display

    Returns:
        User input or None if cancelled

    Raises:
        EOFError: If user wants to exit (Ctrl+D)
    """
    try:
        from prompt_toolkit import prompt as pt_prompt
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.lexers import PygmentsLexer
        from prompt_toolkit.styles import Style
        from pygments.lexers.python import PythonLexer

        # Command auto-completion
        completer = WordCompleter(
            ["pause", "exit", "quit", "save"],
            ignore_case=True,
        )

        # Persistent history across messages in this session
        if not hasattr(_read_multiline_natural, "_history"):
            _read_multiline_natural._history = InMemoryHistory()  # type: ignore[attr-defined]

        # Dynamic toolbar that shows line count (accesses current app's buffer)
        def bottom_toolbar():
            from prompt_toolkit.application import get_app

            try:
                app = get_app()
                text = app.current_buffer.text
                line_count = text.count("\\n") + 1 if text else 1
            except Exception:
                line_count = 1

            line_info = f"{line_count} line{'s' if line_count != 1 else ''}"

            return HTML(
                f'<style bg="#333333" fg="#888888">'
                f" <b>Ctrl+J</b> newline │ <b>Enter</b> send │ <b>Ctrl+C</b> cancel │ "
                f'<style fg="#aaddff">{line_info}</style> '
                f"</style>"
            )

        # Key bindings
        kb = KeyBindings()

        @kb.add("c-j")  # Ctrl+J for newline (standard terminal newline)
        def _(event):
            """Ctrl+J → insert newline."""
            event.current_buffer.insert_text("\\n")

        @kb.add("enter")
        def _(event):
            """Enter → send message."""
            event.current_buffer.validate_and_handle()

        # Prompt styling
        style = Style.from_dict(
            {
                "prompt": "bold fg:ansicyan",
                "bottom-toolbar": "bg:#333333 fg:#888888",
            }
        )

        text = pt_prompt(
            [("class:prompt", prompt_text)],
            multiline=True,
            key_bindings=kb,
            completer=completer,
            complete_while_typing=False,  # Only show completions on Tab, not while typing
            history=_read_multiline_natural._history,  # type: ignore[attr-defined]
            lexer=PygmentsLexer(PythonLexer),
            bottom_toolbar=bottom_toolbar,
            style=style,
            enable_history_search=False,
            refresh_interval=0.5,  # Refresh toolbar periodically
        )
        # Return stripped text, or empty string if just Enter was pressed
        # (None is reserved for Ctrl+C cancel)
        return text.strip() if text else ""

    except ImportError:
        # Fallback: simple double-Enter mode
        print(prompt_text, end="", flush=True)
        lines: list[str] = []
        try:
            while True:
                line = input("" if lines else "")
                if line == "" and len(lines) > 0:
                    break
                lines.append(line)
        except KeyboardInterrupt:
            return None

        return "\\n".join(lines).strip()


def interactive_learning_session(
    pattern: str,
    progress: dict[str, Any],
    quests: list[dict[str, Any]],
    mode: str | None = None,
) -> None:
    """Run an interactive learning session for a pattern.

    Args:
        pattern: Pattern to learn
        progress: User progress dict
        quests: List of all quests (currently unused)
        mode: Optional initial mode ("teach_first" or "diagnose_first")
    """

    def _autosave_enabled() -> bool:
        v = (os.getenv("COACH_AUTOSAVE") or "1").strip().lower()
        return v not in {"0", "false", "no", "off"}

    def _resume_show_mode() -> str:
        """How much transcript to show when resuming."""
        return (os.getenv("COACH_RESUME_SHOW") or "tail").strip().lower()

    def _resume_tail_n() -> int:
        try:
            return max(1, int(os.getenv("COACH_RESUME_TAIL") or "25"))
        except Exception:
            return 25

    def _print_transcript(msgs: list[dict[str, Any]]) -> None:
        """Print a readable transcript (best-effort) for resumed sessions."""
        # Skip system messages; map OpenAI roles to our UI roles.
        show_mode = _resume_show_mode()
        filtered = [
            m for m in msgs if isinstance(m, dict) and m.get("role") != "system"
        ]

        if show_mode == "last":
            filtered = filtered[-1:] if filtered else []
        elif show_mode == "tail":
            tail_n = _resume_tail_n()
            if len(filtered) > tail_n:
                print(
                    f"\\n📜 Showing last {tail_n} of {len(filtered)} messages. "
                    f"Set COACH_RESUME_SHOW=all to show everything.\\n"
                )
            filtered = filtered[-tail_n:] if filtered else []
        elif show_mode == "all":
            pass
        else:
            # Unknown mode -> safe default.
            filtered = filtered[-1:] if filtered else []

        for m in filtered:
            role = (m.get("role") or "").strip().lower()
            content = m.get("content") or ""
            if not content:
                continue
            ui_role = (
                "Mentor"
                if role == "assistant"
                else ("You" if role == "user" else role.title() or "Message")
            )
            print_ai_response(str(content), ui_role)

    def _read_from_editor() -> str | None:
        """Open $EDITOR for composing a multi-line message. Returns None if cancelled/empty."""
        editor_env = (os.getenv("EDITOR") or "").strip()
        if not editor_env:
            # Safe default on macOS/Linux; user can set EDITOR for preference.
            editor_env = "vi"

        # Support EDITOR with args, e.g. "subl -w" or "code --wait".
        cmd = shlex.split(editor_env) or ["vi"]

        # Best-effort: if user set "subl" / "code" without a wait flag, add one so
        # we don't read the file before the editor is closed.
        exe = (Path(cmd[0]).name or "").lower()
        if exe in {"subl", "sublime_text"} and "-w" not in cmd and "--wait" not in cmd:
            cmd.append("-w")
        if exe in {"code", "code-insiders"} and "--wait" not in cmd and "-w" not in cmd:
            cmd.append("--wait")

        with tempfile.NamedTemporaryFile(
            prefix="dsa-coach-msg-", suffix=".md", delete=False
        ) as tf:
            path = Path(tf.name)

        try:
            print(
                "\\n📝 Editor mode: write your message, SAVE, then CLOSE the editor/tab to send it.\\n"
            )
            subprocess.run([*cmd, str(path)], check=False)
            text = path.read_text(encoding="utf-8", errors="replace")
        finally:
            with contextlib.suppress(Exception):
                path.unlink()

        text = (text or "").strip()
        return text or None

    def _session_meta(messages: list[dict[str, Any]]) -> dict[str, Any]:
        meta = {"pattern": pattern}
        with contextlib.suppress(Exception):
            meta["learning_mode"] = (
                "diagnose_first"
                if messages
                and "Diagnose my understanding" in messages[0].get("content", "")
                else "teach_first"
            )
        return meta

    # If mode is explicitly passed, start fresh with that mode (skip resume check)
    # Only check for saved sessions when mode=None (user chose "Resume" from menu)
    if mode:
        # Fresh session with explicit mode
        messages, response = start_learning_session(pattern, progress, mode=mode)
        print_ai_response(response, "Mentor")
        if _autosave_enabled():
            save_conversation("learn", pattern, messages, _session_meta(messages))
    else:
        # mode=None means user wants to resume (came from menu option 5)
        saved = load_conversation("learn", pattern)
        if saved:
            msgs = saved.get("messages")
            if isinstance(msgs, list) and len(msgs) > 0:
                messages = msgs
                _print_transcript(messages)
            else:
                # Corrupted session, start fresh
                messages, response = start_learning_session(
                    pattern, progress, mode="teach_first"
                )
                print_ai_response(response, "Mentor")
                if _autosave_enabled():
                    save_conversation(
                        "learn", pattern, messages, _session_meta(messages)
                    )
        else:
            # No saved session, start fresh
            messages, response = start_learning_session(
                pattern, progress, mode="teach_first"
            )
            print_ai_response(response, "Mentor")
            if _autosave_enabled():
                save_conversation("learn", pattern, messages, _session_meta(messages))

    # Interactive loop
    print(
        "\\n💡 Ctrl+J for newlines, Enter to send, Ctrl+D to exit."
        "\\n   Type ':e' to compose in $EDITOR, 'pause' to save & exit.\\n"
    )

    try:
        while True:
            try:
                user_input_raw = _read_multiline_natural("🧑 You › ")
            except EOFError:
                # Ctrl+D → exit session
                save_conversation("learn", pattern, messages, _session_meta(messages))
                print("\\n💾 Session saved!")
                print("Resume by starting `python coach.py` and using `/resume`.\\n")
                break

            if user_input_raw is None:
                # Ctrl+C during compose → cancel this message, continue session
                print("⚠️  Message cancelled.\\n")
                continue

            user_input = user_input_raw.strip()

            if not user_input:
                continue

            # Check for special commands
            if user_input.lower() in ["pause", "exit", "quit", "save"]:
                save_conversation("learn", pattern, messages, _session_meta(messages))
                print("\\n💾 Session paused and saved!")
                print("Resume by starting `python coach.py` and using `/resume`.\\n")
                break

            if user_input.strip().lower() in {":editor", ":e"}:
                edited = _read_from_editor()
                if edited is None:
                    continue
                user_input = edited

            # Echo user's message as a bubble
            chat_style = (os.getenv("COACH_CHAT_STYLE") or "discord").strip().lower()
            if chat_style == "discord":
                print_ai_response(user_input, "You")

            messages, response = continue_conversation(messages, user_input, progress)
            print_ai_response(response, "Mentor")
            if _autosave_enabled():
                save_conversation("learn", pattern, messages, _session_meta(messages))

    except KeyboardInterrupt:
        # Fallback: auto-save on unexpected Ctrl+C
        save_conversation("learn", pattern, messages, _session_meta(messages))
        print("\\n\\n💾 Session auto-saved!")
        print("Resume by starting `python coach.py` and using `/resume`.\\n")
