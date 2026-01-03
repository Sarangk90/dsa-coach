from dsa_coach import paths
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI


def cmd_start():
    """Initialize profile and workspace."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    ui.print_styled("\n🎮 Welcome to DSA Coach!", "bold blue")
    ui.print_styled("Your adaptive interview preparation companion.\n", "italic")

    # Check if already initialized
    try:
        with SyncDatabase() as db:
            profile = db.get_or_create_profile()
            if profile.name and profile.name != "DSA Learner":
                ui.print_styled(
                    f"Welcome back, {profile.name}! Use 'python coach.py status' to see your progress.",
                    "green",
                )
                return
    except Exception as e:
        ui.print_styled(f"Warning: Could not load existing progress: {e}", "yellow")
        ui.print_styled("Creating fresh profile...\n", "dim")

    # Get name
    try:
        name = input("What's your name? ").strip()
        if not name:
            name = "Engineer"
    except (EOFError, KeyboardInterrupt):
        ui.print_styled("\n\nSetup cancelled.", "yellow")
        return

    # Initialize profile in database
    try:
        with SyncDatabase() as db:
            profile = db.get_or_create_profile()
            profile.name = name
            db.update_profile(profile)
    except Exception as e:
        ui.print_styled(f"\n❌ Error saving profile: {e}", "red")
        ui.print_styled("Please check database permissions.", "dim")
        return

    # Create solutions directory
    try:
        paths.SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        ui.print_styled(f"Warning: Could not create solutions directory: {e}", "yellow")
        ui.print_styled("You may need to create it manually.", "dim")

    ui.print_panel(
        "🚀 Profile Created!",
        f"""Name: {name}

Your journey to Principal Engineer begins now!
Master patterns through deliberate practice.

Run 'python coach.py next' to get your first quest.""",
        "green",
    )
