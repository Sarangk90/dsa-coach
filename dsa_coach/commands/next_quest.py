import webbrowser
from datetime import datetime
from dsa_coach.ui import UI
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.quests import get_all_quests
from dsa_coach.selection import get_next_quest
from dsa_coach.solution import create_solution_file


def start_quest(quest: dict, progress: dict, ui: UI = None):
    """Start a specific quest: set as current, create file, show UI.

    Note: progress dict is kept for backward compatibility with AI functions,
    but the session is stored in the database.
    """
    if ui is None:
        # Fallback UI if not provided
        ui = UI(rich_available=False, console=None)
        try:
            from rich.console import Console
            ui = UI(rich_available=True, console=Console())
        except ImportError:
            pass

    problem_id = quest.get("problem_id", quest.get("id"))
    pattern_id = quest.get("pattern_id", quest.get("pattern"))

    # Extract V2 fields with V1 fallbacks
    pattern_name = quest.get("pattern_name", quest.get("pattern", "Unknown"))
    concept_name = quest.get("concept_name", "")
    problem_name = quest.get("problem_name", quest.get("title", "Unknown"))
    difficulty = quest.get("difficulty", "unknown")
    estimated_time = quest.get("estimated_time_minutes", "?")
    url = quest.get("url", quest.get("link"))

    # Create/update session in database with current quest
    with SyncDatabase() as db:
        session = db.create_session(
            session_type="practice",
            current_pattern=pattern_id,
            current_quest=problem_id,
        )
        # Log activity
        db.upsert_daily_log(user_id="default", pattern_worked=pattern_id)
    
    # Create solution file
    filepath = create_solution_file(quest)
    
    # Display quest info with hierarchy
    ui.print_styled("\n" + "="*70, "cyan")
    ui.print_styled(f"  ⚔️ QUEST: {problem_name}", "bold green")
    ui.print_styled("="*70, "cyan")
    
    ui.print_styled(f"\n  📚 Pattern: {pattern_name}", "bold cyan")
    if concept_name:
        ui.print_styled(f"  🎯 Concept: {concept_name}", "cyan")
    
    diff_color = {"easy": "green", "medium": "yellow", "hard": "red"}.get(difficulty.lower(), "white")
    ui.print_styled(f"\n  📊 Difficulty: {difficulty.title()}", diff_color)
    ui.print_styled(f"  ⏱️  Estimated Time: {estimated_time} minutes", "yellow")

    # Show system design connections if available
    pattern_id = quest.get("pattern_id")
    if pattern_id:
        from dsa_coach.curriculum import get_pattern_by_id, get_active_mode
        mode = get_active_mode(progress)
        pattern_data = get_pattern_by_id(pattern_id, mode)
        if pattern_data:
            sys_connections = pattern_data.get("system_design_connections", [])
            if sys_connections:
                ui.print_styled(f"\n  🏗️  System Design Connections:", "bold magenta")
                for conn in sys_connections[:2]:  # Show first 2
                    ui.print_styled(f"     • {conn}", "magenta")
    
    ui.print_styled(f"\n  📂 Solution file:", "white")
    ui.print_styled(f"     {filepath}", "dim")
    
    if url:
        ui.print_styled(f"  🔗 LeetCode:", "white")
        ui.print_styled(f"     {url}", "blue")
    
    # Show why this problem was selected
    reason = quest.get("reason_for_selection", "")
    if reason:
        ui.print_styled(f"\n  💡 Why this problem:", "white")
        ui.print_styled(f"     {reason}", "dim")
    
    # Open link
    if url:
        print()
        open_link = input("  Open LeetCode in browser? [Y/n] ").strip().lower()
        if open_link != 'n':
            webbrowser.open(url)
    
    # Show help options
    ui.print_styled("\n" + "─"*70, "dim")
    ui.print_styled("  📋 DIVE Protocol: Decode → Identify → Visualize → Execute → Evaluate", "cyan")
    ui.print_styled("─"*70, "dim")
    
    ui.print_styled("\n  🆘 While solving, you can:", "bold white")
    ui.print_styled("     • python coach.py hint     → Get an adaptive hint", "dim")
    pattern_slug = quest.get("pattern_id", quest.get("pattern", ""))
    if pattern_slug:
        ui.print_styled(f"     • python coach.py learn {pattern_slug}  → Review the pattern", "dim")
    ui.print_styled("     • python coach.py done     → Mark complete & continue", "dim")
    
    # Offer immediate help
    print()
    ui.print_styled("  👉 How would you like to proceed?", "bold white")
    ui.print_styled("     1. 🚀 Start solving (I've got this!)", "green")
    ui.print_styled(f"     2. 📖 Quick refresher on {pattern_name} first", "cyan")
    ui.print_styled("     3. 💡 Give me a starting hint", "yellow")
    
    choice = input("\n  Choose (1/2/3) [1]: ").strip()
    
    if choice == "2":
        # Quick refresher
        try:
            from dsa_coach.ai import interactive_learning_session
            all_quests = get_all_quests()
            pattern_slug = quest.get("pattern_id", quest.get("pattern", ""))
            interactive_learning_session(pattern_slug, progress, all_quests, mode="teach_first")
            ui.print_styled(f"\n✅ Ready to solve? Your quest is still active!", "green")
            ui.print_styled(f"   Run 'python coach.py done' when you've completed {problem_name}", "dim")
        except ImportError:
            ui.print_styled("AI Mentor not available.", "red")
    elif choice == "3":
        # Give a hint
        from dsa_coach.commands.hint import cmd_hint
        cmd_hint()
    else:
        ui.print_styled("\n  💪 Good luck! Remember: understand the pattern, not just the solution.", "green")




def cmd_next():
    """Get the next optimal quest."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console
        from rich.panel import Panel
        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        session = db.get_latest_session()
        completed_quests = db.get_completed_quests()
        progress_compat = db.build_progress_compat()

    if not profile.name or profile.name == "DSA Learner":
        ui.print_styled("No profile found. Run 'python coach.py start' first.", "red")
        return

    # Check if there's a current quest in progress
    current_id = session.current_quest if session else None
    if current_id:
        from dsa_coach.curriculum import get_problem_by_id, get_active_mode
        mode = get_active_mode(progress_compat)
        current = get_problem_by_id(current_id, mode)

        # Fallback to old quest format
        if not current:
            all_quests = get_all_quests()
            current = next((q for q in all_quests if q.get("id") == current_id or q.get("problem_id") == current_id), None)

        if current:
            name = current.get("problem_name", current.get("title", "Unknown"))
            ui.print_styled(f"⚠️ You have an active quest: {name}", "yellow")
            ui.print_styled("Complete it with 'python coach.py done' or abandon it first.", "dim")
            return

    # Get next quest (uses selection algorithm with progress_compat)
    quest = get_next_quest(progress_compat)

    if not quest:
        ui.print_panel(
            "🎉 Congratulations!",
            "You've completed all available quests! You're ready for your interview!",
            "green"
        )
        return

    # Check if pattern is new - offer to learn first
    pattern_id = quest.get("pattern_id", quest.get("pattern"))
    if pattern_id:
        # Check if this is a new pattern (no problems solved from it yet)
        completed_quest_ids = {c.quest_id for c in completed_quests}
        pattern_problems_solved = any(
            q_id.startswith(pattern_id) for q_id in completed_quest_ids
        )

        if not pattern_problems_solved:
            pattern_name = quest.get("pattern_name", pattern_id)
            ui.print_styled(f"\n📚 This is your first problem in {pattern_name}!", "yellow")
            learn_first = input("Want to learn this pattern first? [Y/n] ").strip().lower()

            if learn_first != 'n':
                # Import and run learning session
                try:
                    from dsa_coach.ai import interactive_learning_session
                    all_quests = get_all_quests()
                    interactive_learning_session(pattern_id, progress_compat, all_quests)
                    ui.print_styled("\n" + "─" * 60 + "\n", "dim")
                    ui.print_styled("Now let's apply what you learned!", "green")
                except ImportError:
                    ui.print_styled("AI Mentor not available.", "red")

    # Start the selected quest
    start_quest(quest, progress_compat, ui)
