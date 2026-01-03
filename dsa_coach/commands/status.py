from dsa_coach.ui import UI
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.curriculum import get_pattern_name


def cmd_status():
    """Show current progress and stats."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed_quests = db.get_completed_quests()
        session = db.get_latest_session()
        due_reviews = db.get_due_reviews()

    if not profile.name or profile.name == "DSA Learner":
        ui.print_styled("No profile found. Run 'python coach.py start' first.", "red")
        return

    # Calculate stats
    completed = len(completed_quests)

    # Find weakest and strongest patterns
    pattern_conf = [(p.pattern_id, p.confidence) for p in patterns]
    pattern_conf.sort(key=lambda x: x[1])

    weakest = [p for p, c in pattern_conf if c < 50][:3]
    strongest = [p for p, c in pattern_conf if c >= 70][:3]

    # Get current quest from session
    current_quest = session.current_quest if session else None

    # Display
    if ui.rich_available and ui.console:
        from rich.table import Table
        from rich.panel import Panel

        # Header
        ui.console.print(Panel(
            f"[bold]{profile.name}[/bold]",
            title="👤 Profile",
            border_style="blue"
        ))

        # Stats table
        table = Table(show_header=False, box=None)
        table.add_column("Stat", style="dim")
        table.add_column("Value", style="bold")

        table.add_row("✅ Completed", f"{completed} quests")
        table.add_row("📅 Started", str(profile.created_at)[:10])
        table.add_row("🕐 Last Active", str(profile.last_active)[:10])
        table.add_row("📋 Due Reviews", f"{len(due_reviews)} quests")

        ui.console.print(table)

        # Patterns
        if weakest:
            weakest_names = [get_pattern_name(p) for p in weakest]
            ui.console.print(f"\n[red]⚠️ Focus Areas:[/red] {', '.join(weakest_names)}")
        if strongest:
            strongest_names = [get_pattern_name(p) for p in strongest]
            ui.console.print(f"[green]💪 Strengths:[/green] {', '.join(strongest_names)}")

        # Current quest
        if current_quest:
            ui.console.print(f"\n[yellow]🎯 Current Quest:[/yellow] {current_quest}")
    else:
        print(f"\n=== {profile.name} ===")
        print(f"✅ Completed: {completed} quests")
        print(f"📅 Started: {str(profile.created_at)[:10]}")
        print(f"📋 Due Reviews: {len(due_reviews)} quests")
        if weakest:
            weakest_names = [get_pattern_name(p) for p in weakest]
            print(f"⚠️ Focus Areas: {', '.join(weakest_names)}")
        if strongest:
            strongest_names = [get_pattern_name(p) for p in strongest]
            print(f"💪 Strengths: {', '.join(strongest_names)}")

