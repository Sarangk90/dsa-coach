from dsa_coach.curriculum import get_pattern_name
from dsa_coach.pattern_manager import PatternManager
from dsa_coach.quests import get_all_quests
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI


def _normalize_pattern(pattern: str) -> str:
    """Normalize pattern name (accept hyphens or underscores)."""
    return pattern.replace("-", "_").replace(" ", "_").lower()


def _format_progress_badge(prog: float) -> tuple[str, str]:
    """Return (emoji, color) for progress level."""
    if prog >= 70:
        return "✅", "green"
    if prog >= 40:
        return "🔶", "yellow"
    return "❌", "red"


def _run_learning_session(
    pattern: str, progress_compat: dict, mode: str, ui: UI
) -> bool:
    """Run a learning session and return True if user wants to practice after."""
    try:
        from dsa_coach.ai import interactive_learning_session

        all_quests = get_all_quests()
        interactive_learning_session(pattern, progress_compat, all_quests, mode=mode)

        # After session ends, offer to practice
        ui.print_styled("\n" + "─" * 60, "dim")
        ui.print_styled("  ✅ Great learning session!", "green")

        # Reload progress
        pm = PatternManager(mode=mode)
        status = pm.get_pattern_status(pattern)
        next_quest = status["next_quest"]

        if next_quest:
            ui.print_styled(
                f"\n  📝 Ready to practice? Next problem: {next_quest['title']}", "cyan"
            )
            practice_now = input("  Start this problem now? [Y/n] ").strip().lower()
            if practice_now != "n":
                return True  # Signal to start practice
        else:
            ui.print_styled(
                "  🎉 You've completed all essential problems for this pattern!",
                "green",
            )

        return False

    except ImportError:
        ui.print_styled(
            "  ❌ AI Mentor not available. Please configure your API key in .env", "red"
        )
        return False


def cmd_learn(pattern: str | None = None):
    """Start an interactive learning session."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed_quests = db.get_completed_quests()
        session = db.get_latest_session()

        # Build pattern progress map
        pattern_progress_map = {p.pattern_id: p.progress for p in patterns}
        pattern_ids = set(pattern_progress_map.keys())
        completed_quest_ids = {c.quest_id for c in completed_quests}

        # Build compatibility dict for AI functions
        progress_compat = db.build_progress_compat()

    if not profile.name or profile.name == "DSA Learner":
        ui.print_styled("No profile found. Run 'python coach.py start' first.", "red")
        return

    # Get current quest from session
    current_quest_id = session.current_quest if session else None

    # Load quest data to find current quest's pattern
    current_quest_pattern = None
    if current_quest_id:
        all_quests = get_all_quests()
        for quest in all_quests:
            if quest["id"] == current_quest_id:
                current_quest_pattern = quest.get("pattern")
                break

    # If pattern not specified, show comprehensive menu
    if not pattern:
        from dsa_coach.curriculum import get_curriculum

        # Get patterns from V2 curriculum
        curriculum = get_curriculum(
            progress_compat.get("profile", {}).get("active_mode", "fast_track")
        )
        patterns_config = {p["pattern_id"]: p for p in curriculum}

        ui.print_styled("\n" + "=" * 70, "cyan")
        ui.print_styled("  📚 INTERACTIVE LEARNING - CHOOSE YOUR PATTERN", "bold cyan")
        ui.print_styled("=" * 70, "cyan")

        if current_quest_pattern:
            ui.print_styled(
                f"\n  🎯 Your current quest uses: {get_pattern_name(current_quest_pattern)}",
                "yellow",
            )

        ui.print_styled(
            "\n  Legend: ✅ Mastered (70%+) | 🔶 Learning (40-69%) | ❌ Needs Work (<40%)\n",
            "dim",
        )

        # Build pattern list
        pattern_options = []
        option_num = 1

        # Sort patterns by sequence_order (curriculum order) for V2
        sorted_patterns = sorted(
            patterns_config.items(), key=lambda x: x[1].get("sequence_order", 999)
        )

        for pat_id, pat_data in sorted_patterns:
            prog = pattern_progress_map.get(pat_id, 0)
            badge, color = _format_progress_badge(prog)

            # Use pattern_name for V2 (or fall back to title for compatibility)
            pattern_display = pat_data.get(
                "pattern_name", pat_data.get("title", pat_id.replace("_", " ").title())
            )
            is_current = pat_id == current_quest_pattern
            current_marker = " 👈 YOUR QUEST" if is_current else ""

            ui.print_styled(
                f"  {option_num}. {badge} {pattern_display} ({prog:.0f}%){current_marker}",
                color if not is_current else "bold yellow",
            )
            pattern_options.append(pat_id)
            option_num += 1

        print()

        choice = input("  Select a pattern (number or name): ").strip()

        # Try to parse as number first
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pattern_options):
                pattern = pattern_options[idx]
            else:
                ui.print_styled("  ❌ Invalid selection.", "red")
                return
        except ValueError:
            # Treat as pattern name
            normalized = _normalize_pattern(choice)
            if normalized in pattern_ids or normalized in list(patterns_config.keys()):
                pattern = normalized
            else:
                ui.print_styled(
                    f"  ❌ Pattern '{choice}' not found. Try using the number or exact name (e.g., 'sliding_window').",
                    "red",
                )
                return
    else:
        # Pattern provided as argument - normalize it
        from dsa_coach.curriculum import get_curriculum

        pattern = _normalize_pattern(pattern)
        # Allow patterns from config even if no progress yet
        curriculum = get_curriculum(
            progress_compat.get("profile", {}).get("active_mode", "fast_track")
        )
        patterns_config = {p["pattern_id"]: p for p in curriculum}
        if pattern not in pattern_ids and pattern not in patterns_config:
            ui.print_styled(f"  ❌ Pattern '{pattern}' not found.", "red")
            return

    # --- Pattern Dashboard & Action Menu ---

    pm = PatternManager(
        mode=progress_compat.get("profile", {}).get("active_mode", "fast_track")
    )
    status = pm.get_pattern_status(pattern)
    syllabus = pm.get_pattern_syllabus(pattern)

    # Check for saved session
    try:
        from dsa_coach.ai import load_conversation

        saved_session = load_conversation("learn", pattern)
        has_saved = saved_session and saved_session.get("messages")
    except ImportError:
        has_saved = False
        saved_session = None

    # Header
    ui.print_styled("\n" + "=" * 70, "cyan")
    ui.print_styled(f"  📚 LEARNING MODE: {get_pattern_name(pattern)}", "bold cyan")
    ui.print_styled("=" * 70, "cyan")

    # Description
    desc = syllabus.get("description", "Master this pattern to ace interviews.")
    ui.print_styled(f"\n  {desc}\n", "white")

    # Progress Bar for Essential Questions
    total = status["essential_total"]
    done_count = status["essential_done_count"]

    if total > 0:
        bar_len = 20
        filled = int((done_count / total) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        color = "green" if done_count == total else "yellow"
        ui.print_styled(f"  Essential Problems: [{bar}] {done_count}/{total}", color)
    else:
        ui.print_styled("  Essential Problems: (Pattern syllabus coming soon)", "dim")

    # Concepts
    concepts = syllabus.get("concepts", [])
    if concepts:
        ui.print_styled("\n  🔑 Key Concepts:", "cyan")
        for concept in concepts:
            ui.print_styled(f"     • {concept}", "dim")

    # Action Menu
    print()
    ui.print_styled("  👉 What would you like to do?", "bold white")
    ui.print_styled("     1. 🧠 Diagnose My Level (Quiz Me)", "cyan")
    ui.print_styled("     2. 📖 Explain Concepts (Teach Me)", "cyan")

    next_quest = status["next_quest"]
    if next_quest:
        ui.print_styled(f"     3. ⚔️  Start Practice: {next_quest['title']}", "green")
    else:
        ui.print_styled("     3. ✅ Practice (All essential problems done!)", "dim")

    ui.print_styled("     4. 🔍 Pick a Specific Problem", "white")

    if has_saved and saved_session:
        saved_date = saved_session.get("saved_at", "")[:10]
        ui.print_styled(f"     5. 📂 Resume Saved Session ({saved_date})", "yellow")

    ui.print_styled("     0. ← Back", "dim")
    print()

    action = input("  Choose an option: ").strip()

    if action == "0":
        return

    try:
        # 1. Diagnose
        if action == "1":
            want_practice = _run_learning_session(
                pattern, progress_compat, "diagnose_first", ui
            )
            if want_practice:
                # Reload and start next quest
                pm = PatternManager(
                    mode=progress_compat.get("profile", {}).get(
                        "active_mode", "fast_track"
                    )
                )
                status = pm.get_pattern_status(pattern)
                if status["next_quest"]:
                    from dsa_coach.commands.next_quest import start_quest

                    start_quest(status["next_quest"], progress_compat, ui)

        # 2. Teach
        elif action == "2":
            want_practice = _run_learning_session(
                pattern, progress_compat, "teach_first", ui
            )
            if want_practice:
                pm = PatternManager(
                    mode=progress_compat.get("profile", {}).get(
                        "active_mode", "fast_track"
                    )
                )
                status = pm.get_pattern_status(pattern)
                if status["next_quest"]:
                    from dsa_coach.commands.next_quest import start_quest

                    start_quest(status["next_quest"], progress_compat, ui)

        # 3. Next Quest
        elif action == "3":
            if next_quest:
                from dsa_coach.commands.next_quest import start_quest

                start_quest(next_quest, progress_compat, ui)
            else:
                ui.print_styled(
                    "  🎉 You've completed all essential problems for this pattern!",
                    "green",
                )

        # 4. Pick Problem
        elif action == "4":
            # List all quests for this pattern
            all_quests = get_all_quests()
            pattern_quests = [q for q in all_quests if q.get("pattern_id") == pattern]

            if not pattern_quests:
                ui.print_styled("  No quests found for this pattern.", "red")
                return

            ui.print_styled(
                f"\n  📝 Available Quests for {get_pattern_name(pattern)}:", "cyan"
            )
            for i, q in enumerate(pattern_quests, 1):
                status_icon = "✅" if q["problem_id"] in completed_quest_ids else "⬜"
                ui.print_styled(
                    f"     {i}. {status_icon} {q['problem_name']} ({q['difficulty']})",
                    "white",
                )

            q_idx = input(f"\n  Select quest (1-{len(pattern_quests)}): ").strip()
            try:
                idx = int(q_idx) - 1
                if 0 <= idx < len(pattern_quests):
                    selected = pattern_quests[idx]
                    from dsa_coach.commands.next_quest import start_quest

                    start_quest(selected, progress_compat, ui)
                else:
                    ui.print_styled("Invalid selection.", "red")
            except ValueError:
                pass

        # 5. Resume saved session
        elif action == "5" and has_saved:
            try:
                from dsa_coach.ai import interactive_learning_session

                all_quests = get_all_quests()
                # Pass mode=None to trigger the resume flow in mentor.py
                interactive_learning_session(
                    pattern, progress_compat, all_quests, mode=None
                )

                # After session, offer practice
                ui.print_styled("\n" + "─" * 60, "dim")
                pm = PatternManager(
                    mode=progress_compat.get("profile", {}).get(
                        "active_mode", "fast_track"
                    )
                )
                status = pm.get_pattern_status(pattern)
                next_quest = status["next_quest"]

                if next_quest:
                    ui.print_styled(
                        f"\n  📝 Ready to practice? Next problem: {next_quest['title']}",
                        "cyan",
                    )
                    practice_now = (
                        input("  Start this problem now? [Y/n] ").strip().lower()
                    )
                    if practice_now != "n":
                        from dsa_coach.commands.next_quest import start_quest

                        start_quest(next_quest, progress_compat, ui)

            except ImportError:
                ui.print_styled("  ❌ AI Mentor not available.", "red")

    except ImportError:
        ui.print_styled(
            "  ❌ AI Mentor not available or error importing modules.", "red"
        )
