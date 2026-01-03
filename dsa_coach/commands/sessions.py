"""Sessions command - list and manage saved conversation sessions."""

from dsa_coach.ui import UI

try:
    from rich.console import Console
    _console = Console()
    _ui = UI(rich_available=True, console=_console)
except ImportError:
    _ui = UI(rich_available=False, console=None)


def cmd_sessions():
    """List and manage saved conversation sessions."""
    try:
        from dsa_coach.ai import list_saved_conversations, delete_conversation
    except ImportError:
        _ui.print_styled("Mentor module not available.", "red")
        return
    
    saved = list_saved_conversations()
    
    if not saved:
        _ui.print_styled("\n📂 No saved sessions.", "dim")
        return
    
    _ui.print_styled(f"\n💾 Saved Sessions ({len(saved)}):\n", "cyan")
    
    for i, s in enumerate(saved, 1):
        session_type = s['type'].title()
        session_id = s['id'].replace('_', ' ').title()
        _ui.print_styled(f"{i}. [{session_type}] {session_id}", "yellow")
        _ui.print_styled(f"   Messages: {s['messages']} | Saved: {s['saved_at'][:10]}", "dim")
        
        if s['type'] == 'learn':
            _ui.print_styled(f"   Resume: python coach.py learn {s['id']}", "green")
        else:
            _ui.print_styled(f"   Resume: python coach.py design", "green")
    
    print()
    action = input("Delete a session? Enter number or 'n' to skip: ").strip()
    
    if action.lower() == 'n' or not action:
        return
    
    try:
        idx = int(action) - 1
        if 0 <= idx < len(saved):
            s = saved[idx]
            delete_conversation(s['type'], s['id'])
            _ui.print_styled(f"✅ Deleted session: {s['id']}", "green")
    except ValueError:
        _ui.print_styled("Invalid input.", "red")



