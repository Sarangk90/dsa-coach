"""Summary command - full progress dump for debugging and overview."""

from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.curriculum import get_pattern_name
from dsa_coach.ui import UI

try:
    from rich.console import Console
    _console = Console()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _ui = UI(rich_available=False, console=None)


def cmd_summary():
    """Full progress dump for debugging and overview."""
    with SyncDatabase() as db:
        profile = db.get_or_create_profile()
        patterns = db.get_all_pattern_progress()
        completed_quests = db.get_completed_quests()
        due_reviews = db.get_due_reviews()
        mistakes = db.get_recent_mistakes("default", limit=100)
        recurring_mistakes = db.get_recurring_mistake_types("default")
        weekly_activity = db.get_weekly_activity("default")
        milestones = db.get_recent_milestones("default", days=30)

    _ui.print_styled("\n" + "=" * 60, "cyan")
    _ui.print_styled("📊 FULL PROGRESS SUMMARY", "bold cyan")
    _ui.print_styled("=" * 60, "cyan")

    # Profile
    _ui.print_styled(f"\n👤 {profile.name}", "bold")
    _ui.print_styled(f"   Started: {str(profile.created_at)[:10]}", "dim")
    _ui.print_styled(f"   Last Active: {str(profile.last_active)[:10]}", "dim")

    # Completed quests
    _ui.print_styled(f"\n✅ Completed: {len(completed_quests)} quests", "green")

    # Pattern proficiency
    _ui.print_styled("\n📈 Pattern Proficiency:", "yellow")
    prof_list = [(p.pattern_id, p.confidence, p.quests_completed) for p in patterns if p.quests_completed > 0]
    prof_list.sort(key=lambda x: x[1], reverse=True)

    if prof_list:
        for pattern_id, confidence, quests_done in prof_list:
            bar_len = int(confidence / 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            pattern_display = get_pattern_name(pattern_id)
            _ui.print_styled(f"   {pattern_display:25} [{bar}] {confidence:.0f}%  ({quests_done} quests)", "")
    else:
        _ui.print_styled("   No patterns attempted yet.", "dim")

    # Spaced repetition status
    _ui.print_styled(f"\n🔄 Spaced Repetition: {len(due_reviews)} items due for review", "magenta")

    # Mistakes
    _ui.print_styled(f"\n📝 Mistakes logged: {len(mistakes)}", "red" if mistakes else "dim")
    if recurring_mistakes:
        _ui.print_styled("   Recurring patterns:", "dim")
        for r in recurring_mistakes[:3]:
            # DB returns "type" not "mistake_type"
            mtype = r.get("type", r.get("mistake_type", "unknown")).replace("_", " ").title()
            count = r.get("count", 0)
            _ui.print_styled(f"   • {mtype} (x{count})", "red")

    # Weekly activity
    if weekly_activity:
        problems = weekly_activity.get("problems_solved", 0)
        time_mins = weekly_activity.get("time_spent_mins", 0)
        hours = time_mins // 60
        mins = time_mins % 60
        time_str = f"{hours}h {mins}m" if hours else f"{mins}m"
        _ui.print_styled(f"\n📅 This Week: {problems} problems solved, {time_str} spent", "cyan")

    # Recent milestones
    if milestones:
        _ui.print_styled(f"\n🏆 Recent Milestones:", "yellow")
        for m in milestones[:5]:
            desc = m.get("description", "Achievement")
            date = m.get("achieved_at", "")[:10] if m.get("achieved_at") else ""
            _ui.print_styled(f"   • {desc} ({date})", "dim")

    # Saved conversations
    try:
        from dsa_coach.ai import list_saved_conversations
        saved = list_saved_conversations()
        if saved:
            _ui.print_styled(f"\n💾 Saved sessions: {len(saved)}", "yellow")
            for s in saved:
                _ui.print_styled(f"   • {s['type']}/{s['id']} - {s['messages']} messages ({s['saved_at'][:10]})", "dim")
    except ImportError:
        pass

    _ui.print_styled("\n" + "=" * 60 + "\n", "cyan")



