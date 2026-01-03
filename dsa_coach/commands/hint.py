from dsa_coach.quests import get_all_quests
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI


def cmd_hint():
    """Get an adaptive hint for the current quest."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        # Get current session to find active quest
        session = db.get_latest_session()
        current_id = session.current_quest if session else None

        if not current_id:
            ui.print_styled(
                "No active quest. Run 'python coach.py next' to get one.", "yellow"
            )
            return

        # Find quest
        all_quests = get_all_quests()
        quest = next((q for q in all_quests if q["id"] == current_id), None)

        if not quest:
            ui.print_styled("Quest not found.", "red")
            return

        # Get confidence level for this pattern
        pattern = quest.get("pattern", "")
        pattern_progress = db.get_pattern_progress("default", pattern)
        confidence = pattern_progress.confidence if pattern_progress else 0

        # Determine hint level
        hints = quest.get("hints", {})
        if confidence < 30:
            hint_level = "low"
            hint_label = "Detailed Walkthrough"
        elif confidence < 70:
            hint_level = "medium"
            hint_label = "Conceptual Nudge"
        else:
            hint_level = "high"
            hint_label = "Socratic Question"

        hint_text = hints.get(hint_level, "No hint available for this quest.")

        # Track hint usage in daily log
        db.upsert_daily_log(user_id="default", hints_delta=1, pattern_worked=pattern)

    # Check if we should use LLM for smarter hints
    try:
        from dsa_coach.ai import get_adaptive_hint

        # Build a minimal progress dict for backward compatibility
        progress_compat = {"pattern_proficiency": {pattern: {"confidence": confidence}}}
        hint_text = get_adaptive_hint(quest, progress_compat, hint_level)
    except ImportError:
        pass  # Use static hints from quests.json

    ui.print_panel(f"💡 Hint ({hint_label})", hint_text, "yellow")

    if confidence >= 70:
        ui.print_styled(
            "Your confidence is high on this pattern. Try to solve without more hints!",
            "dim",
        )
