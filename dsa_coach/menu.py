"""Interactive menu system for DSA Coach."""

from __future__ import annotations

import os
import sys

from . import paths
from .curriculum import get_pattern_name
from .storage.sync import SyncDatabase
from .ui import UI


def clear_screen() -> None:
    """Clear terminal screen (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def get_ui() -> UI:
    """Get UI wrapper with Rich if available."""
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass
    return ui


def render_progress_bar(current: int, target: int, width: int = 20) -> str:
    """Render a simple progress bar."""
    filled = 0 if target == 0 else int(current / target * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{target}"


def render_dashboard() -> None:
    """Render the status dashboard at the top of the screen."""
    ui = get_ui()

    # Load all data from database
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        completed_quests = db.get_completed_quests()
        pattern_progress = db.get_all_pattern_progress()
        due_items = db.get_due_reviews()
        session = db.get_latest_session()

    if not profile.name or profile.name == "DSA Learner":
        ui.print_styled("\n" + "=" * 70, "yellow")
        ui.print_styled("  🎯 DSA COACH - WELCOME!", "bold yellow")
        ui.print_styled("=" * 70 + "\n", "yellow")
        ui.print_styled("  ⚠️  No profile found. Let's get you started!", "yellow")
        ui.print_styled("  💡 Select option 1 to initialize your profile\n", "dim")
        return

    # Calculate stats
    completed = len(completed_quests)

    # Find weakest patterns
    pattern_conf = [
        (p.pattern_id, p.confidence) for p in pattern_progress if p.quests_completed > 0
    ]
    pattern_conf.sort(key=lambda x: x[1])
    weakest = [(p, c) for p, c in pattern_conf if c < 70][:3]

    # Get current quest from session
    current_quest_id = session.current_quest if session else None

    # Find quest details for current quest
    current_quest_title = None
    current_pattern = None
    if current_quest_id:
        from .quests import get_all_quests

        for quest in get_all_quests():
            if (
                quest.get("id") == current_quest_id
                or quest.get("problem_id") == current_quest_id
            ):
                current_quest_title = quest.get(
                    "problem_name", quest.get("title", current_quest_id)
                )
                current_pattern = (
                    quest.get("pattern_name", quest.get("pattern", ""))
                    .replace("_", " ")
                    .title()
                )
                break
        if not current_quest_title:
            current_quest_title = current_quest_id  # Fallback to ID

    # Render dashboard
    if ui.rich_available and ui.console:
        # Header
        ui.console.print("\n" + "=" * 70)
        ui.console.print(f"  🎯 DSA COACH - {profile.name}", style="bold cyan")
        ui.console.print("=" * 70)

        # Quick stats row
        stats_line = f"  ✅ Completed: [bold]{completed}[/bold] quests"

        if due_items:
            stats_line += f"  |  ⏰ Due Today: [red bold]{len(due_items)}[/red bold]"

        ui.console.print(stats_line)
        ui.console.print("=" * 70 + "\n")

        # Current quest (with pattern info)
        if current_quest_title:
            if current_pattern:
                ui.console.print(
                    f"  🎯 [yellow]Current Quest:[/yellow] [bold]{current_quest_title}[/bold] [dim]({current_pattern})[/dim]"
                )
            else:
                ui.console.print(
                    f"  🎯 [yellow]Current Quest:[/yellow] [bold]{current_quest_title}[/bold]"
                )
        else:
            ui.console.print(
                "  💡 [dim]No active quest - select 'Next Quest' to get started![/dim]"
            )

        # Weak patterns
        if weakest:
            weak_str = ", ".join(
                [f"{get_pattern_name(p)} ({int(c)}%)" for p, c in weakest]
            )
            ui.console.print(f"  ⚠️  [red]Focus Areas:[/red] {weak_str}")

        ui.console.print()
    else:
        # Plain text fallback
        print("\n" + "=" * 70)
        print(f"  🎯 DSA COACH - {profile.name}")
        print("=" * 70)

        stats_line = f"  ✅ Completed: {completed} quests"

        if due_items:
            stats_line += f"  |  ⏰ Due Today: {len(due_items)}"

        print(stats_line)
        print("=" * 70 + "\n")

        # Current quest (with pattern info)
        if current_quest_title:
            if current_pattern:
                print(f"  🎯 Current Quest: {current_quest_title} ({current_pattern})")
            else:
                print(f"  🎯 Current Quest: {current_quest_title}")
        else:
            print("  💡 No active quest - select 'Next Quest' to get started!")

        if weakest:
            weak_str = ", ".join(
                [f"{get_pattern_name(p)} ({int(c)}%)" for p, c in weakest]
            )
            print(f"  ⚠️  Focus Areas: {weak_str}")

        print()


def cmd_continue_quest() -> None:
    """Show current quest details and how to work on it."""
    ui = get_ui()

    # Load from database
    with SyncDatabase() as db:
        session = db.get_latest_session()
        current_quest_id = session.current_quest if session else None
        pattern_progress_map = {p.pattern_id: p for p in db.get_all_pattern_progress()}

    if not current_quest_id:
        ui.print_styled("\n  ⚠️  No active quest!", "yellow")
        ui.print_styled("  💡 Select option 3 (Next Quest) to get started.", "dim")
        return

    # Find the quest details
    import webbrowser

    from .quests import get_all_quests
    from .storage import load_json

    quest = None
    for q in get_all_quests():
        if q.get("id") == current_quest_id or q.get("problem_id") == current_quest_id:
            quest = q
            break

    if not quest:
        ui.print_styled(
            f"\n  ❌ Quest '{current_quest_id}' not found in database.", "red"
        )
        return

    quest_title = quest.get("problem_name", quest.get("title", current_quest_id))

    # Display quest info
    ui.print_styled("\n" + "=" * 70, "cyan")
    ui.print_styled(f"  🎯 CURRENT QUEST: {quest_title}", "bold yellow")
    ui.print_styled("=" * 70, "cyan")

    # Quest details
    pattern = (
        quest.get("pattern_name", quest.get("pattern", "unknown"))
        .replace("_", " ")
        .title()
    )
    pattern_id = quest.get("pattern_id", quest.get("pattern", ""))
    difficulty = quest.get("difficulty", "unknown").capitalize()

    ui.print_styled(f"\n  📌 Pattern: {pattern}", "cyan")
    ui.print_styled(f"  📊 Difficulty: {difficulty}", "cyan")

    # Find solution file
    load_json(paths.QUESTS_FILE)
    quest_id = quest.get("id", quest.get("problem_id", "unknown"))
    solution_file = paths.SOLUTIONS_DIR / f"{quest_id}.py"

    ui.print_styled("\n  📂 Solution File:", "yellow")
    ui.print_styled(f"     {solution_file}", "white")

    # LeetCode link
    leetcode_link = quest.get("url", quest.get("link", ""))
    if leetcode_link:
        ui.print_styled("\n  🔗 LeetCode Link:", "yellow")
        ui.print_styled(f"     {leetcode_link}", "blue")

    # Pattern confidence
    if pattern_id:
        pattern_prog = pattern_progress_map.get(pattern_id)
        conf = pattern_prog.confidence if pattern_prog else 0
        ui.print_styled(
            f"\n  📈 Your {pattern} Confidence: {conf:.0f}%",
            "green" if conf >= 70 else "yellow" if conf >= 40 else "red",
        )

    # DIVE protocol reminder
    ui.print_styled("\n  📋 DIVE Protocol:", "cyan")
    ui.print_styled(
        "     D - Decode (2 min): Read problem, clarify inputs/outputs", "dim"
    )
    ui.print_styled("     I - Identify (2 min): Map to pattern", "dim")
    ui.print_styled(
        "     V - Visualize (3 min): Draw example, walk through logic", "dim"
    )
    ui.print_styled("     E - Execute (15 min): Write clean code", "dim")
    ui.print_styled(
        "     E - Evaluate (3 min): Time/space complexity, test edges", "dim"
    )

    # Next steps
    ui.print_styled("\n  💡 Next Steps:", "green")
    ui.print_styled(f"     1. Open: {solution_file}", "")
    ui.print_styled(
        f"     2. Visit: {leetcode_link if leetcode_link else 'LeetCode'}", ""
    )
    ui.print_styled("     3. Solve using DIVE protocol", "")
    ui.print_styled("     4. Return here and select option 4 (Mark Quest Done)", "")

    # Helper options
    ui.print_styled("\n  🆘 Need Help?", "yellow")
    ui.print_styled("     • Option 5: Get adaptive hint", "dim")
    ui.print_styled(f"     • Option 6: Learn {pattern} pattern", "dim")
    ui.print_styled("     • Option 8: Request code review", "dim")

    # Offer to open browser
    print()
    open_browser = (
        input("  🌐 Open LeetCode problem in browser? (y/n): ").strip().lower()
    )
    if open_browser == "y" and leetcode_link:
        try:
            webbrowser.open(leetcode_link)
            ui.print_styled("  ✅ Browser opened!", "green")
        except Exception:
            ui.print_styled("  ⚠️  Could not open browser automatically", "yellow")


def render_menu() -> None:
    """Render the main menu."""
    ui = get_ui()

    menu_text = """
  ═══ DAILY WORKFLOW ═══
  1. Today's Schedule
  2. Continue Current Quest
  3. Next Quest
  4. Mark Quest Done
  5. View Status

  ═══ LEARNING & HELP ═══
  6. Get Hint
  7. Learn Pattern (Interactive)
  8. Review Mistakes

  ═══ AI FEATURES ═══
  9. Code Review
  10. System Design Session

  ═══ ADVANCED ═══
  11. Spaced Repetition (Recall)
  12. View Sessions
  13. Full Summary

  0. Exit
"""

    if ui.rich_available and ui.console:
        ui.console.print(menu_text, style="cyan")
    else:
        print(menu_text)


def wait_for_continue() -> None:
    """Pause and wait for user to press Enter."""
    input("\n  Press Enter to continue...")


def dispatch_command(choice: str) -> bool:
    """
    Dispatch menu choice to appropriate command handler.
    Returns True if should continue running, False if should exit.
    """
    from .commands import (
        design,
        done,
        hint,
        learn,
        mistakes,
        next_quest,
        recall,
        review,
        sessions,
        status,
        summary,
        today,
    )

    choice = choice.strip().lower()

    if choice in ["0", "q", "quit", "exit"]:
        print("\n  👋 Happy coding! Remember: patterns over memorization.\n")
        return False

    try:
        if choice == "1":
            # Today's Schedule
            today.cmd_today()
        elif choice == "2":
            # Continue Current Quest
            cmd_continue_quest()
        elif choice == "3":
            # Next Quest
            next_quest.cmd_next()
        elif choice == "4":
            # Mark Quest Done
            done.cmd_done()
        elif choice == "5":
            # View Status
            status.cmd_status()
        elif choice == "6":
            # Get Hint
            hint.cmd_hint()
        elif choice == "7":
            # Learn Pattern - just call with no args to show full menu
            learn.cmd_learn(None)
        elif choice == "8":
            # Review Mistakes
            mistakes.cmd_mistakes()
        elif choice == "9":
            # Code Review
            print("\n  🔍 Code Review")
            file_path = input(
                "  Enter solution file path (e.g., solutions/day1/two_sum.py): "
            ).strip()
            if file_path:
                # Mock sys.argv for review command
                old_argv = sys.argv.copy()
                sys.argv = ["coach.py", "review", file_path]
                review.cmd_review()
                sys.argv = old_argv
            else:
                print("  ⚠️  No file path provided.")
        elif choice == "10":
            # System Design Session
            print("\n  🏗️  System Design Session")
            design_name = input(
                "  Enter design name (or press Enter for menu): "
            ).strip()
            design_name = design_name if design_name else None
            design.cmd_design(design_name)
        elif choice == "11":
            # Spaced Repetition
            recall.cmd_recall()
        elif choice == "12":
            # View Sessions
            sessions.cmd_sessions()
        elif choice == "13":
            # Full Summary
            summary.cmd_summary()
        else:
            print(f"\n  ❌ Invalid option: {choice}")
            print("  Please choose a number from the menu (0-13)")

        wait_for_continue()
        return True

    except KeyboardInterrupt:
        print("\n\n  ⚠️  Command interrupted.")
        wait_for_continue()
        return True
    except Exception as e:
        print(f"\n  ❌ Error executing command: {e}")
        import traceback

        traceback.print_exc()
        wait_for_continue()
        return True


def run_interactive_menu() -> None:
    """Main loop for the interactive menu."""
    first_run = True

    while True:
        clear_screen()

        # Only show dashboard on first run
        if first_run:
            render_dashboard()
            first_run = False

        render_menu()

        try:
            choice = input("  Choose an option: ").strip()
            should_continue = dispatch_command(choice)

            if not should_continue:
                break

        except KeyboardInterrupt:
            print("\n\n  👋 Exiting DSA Coach. See you next session!\n")
            break
        except Exception as e:
            print(f"\n  ❌ Unexpected error: {e}")
            import traceback

            traceback.print_exc()
            wait_for_continue()
