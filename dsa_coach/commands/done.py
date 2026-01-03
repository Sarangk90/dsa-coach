from datetime import datetime

from dsa_coach.curriculum import (
    check_all_problems_complete,
    check_concept_complete,
    check_pattern_mastery,
    get_active_mode,
    get_pattern_by_id,
    get_problem_by_id,
    unlock_dependent_patterns,
)
from dsa_coach.quests import get_all_quests
from dsa_coach.storage.models import PatternProgress, QuestCompletion
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI


def cmd_done(success: bool = True, time_mins: int | None = None):
    """Mark current quest as complete."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        session = db.get_latest_session()
        current_id = session.current_quest if session else None

        if not current_id:
            ui.print_styled(
                "No active quest. Run 'python coach.py next' to get one.", "yellow"
            )
            return

        # Build compatibility dict for curriculum functions
        progress_compat = db.build_progress_compat()
        mode = get_active_mode(progress_compat)

        # Find quest (support both V1 and V2)
        quest = get_problem_by_id(current_id, mode)
        if not quest:
            all_quests = get_all_quests()
            quest = next(
                (
                    q
                    for q in all_quests
                    if q.get("id") == current_id or q.get("problem_id") == current_id
                ),
                None,
            )

        if not quest:
            ui.print_styled("Quest not found. Something went wrong.", "red")
            return

        # Calculate time taken from session
        if session and session.created_at and not time_mins:
            elapsed = datetime.now() - session.created_at
            time_mins = int(elapsed.total_seconds() / 60)

        # Ask for self-assessment if not provided
        if success and time_mins is None:
            try:
                time_input = input("How many minutes did it take? ").strip()
                time_mins = int(time_input) if time_input else 30
            except ValueError:
                time_mins = 30

        # Extract problem/pattern info with V1 fallback
        quest.get("problem_id", quest.get("id"))
        quest.get("problem_name", quest.get("title", "Unknown"))
        pattern_id = quest.get("pattern_id", quest.get("pattern"))
        pattern_name = quest.get("pattern_name", pattern_id)
        concept_id = quest.get("concept_id")

        # Get hints used from daily log for today
        weekly = db.get_weekly_activity("default")
        hints_used = weekly.get("hints_used", 0) if weekly else 0

        # Create/update QuestCompletion in database
        existing_completion = db.get_quest_completion("default", current_id)
        if existing_completion:
            existing_completion.review_count += 1
            existing_completion.last_reviewed = datetime.now()
            existing_completion.time_minutes = (
                existing_completion.time_minutes or 0
            ) + (time_mins or 0)
            db.upsert_quest_completion(existing_completion)
        else:
            # First completion
            completion = QuestCompletion(
                id=f"default_{current_id}",
                user_id="default",
                quest_id=current_id,
                pattern_id=pattern_id or "",
                completed_at=datetime.now(),
                time_minutes=time_mins,
                hints_used=hints_used,
                success=success,
                review_count=0,
                next_review_in=1,  # First review in 1 day
            )
            db.upsert_quest_completion(completion)

        # Update pattern progress
        pattern_progress = (
            db.get_pattern_progress("default", pattern_id) if pattern_id else None
        )
        if pattern_progress:
            pattern_progress.quests_completed += 1
            pattern_progress.last_practiced = datetime.now()
            # Confidence boost based on hints
            if hints_used == 0:
                pattern_progress.confidence = min(100, pattern_progress.confidence + 15)
            else:
                pattern_progress.confidence = min(100, pattern_progress.confidence + 10)
            db.upsert_pattern_progress(pattern_progress)
        elif pattern_id:
            # Create new pattern progress
            pattern_progress = PatternProgress(
                id=f"default_{pattern_id}",
                user_id="default",
                pattern_id=pattern_id,
                confidence=15 if hints_used == 0 else 10,
                quests_completed=1,
                last_practiced=datetime.now(),
            )
            db.upsert_pattern_progress(pattern_progress)

        # Update daily log
        db.upsert_daily_log(
            user_id="default",
            problems_delta=1,
            time_delta_mins=time_mins or 0,
            pattern_worked=pattern_id,
        )

        # Update profile quests_completed
        profile = db.get_or_create_profile()
        profile.quests_completed += 1
        profile.last_active = datetime.now()
        db.update_profile(profile)

        # Clear current quest from session
        if session:
            session.current_quest = None
            session.current_pattern = None
            db.update_session(session)

        # Rebuild progress_compat after updates for curriculum checks
        progress_compat = db.build_progress_compat()

        # V2: Check concept completion
        concept_complete = False
        if pattern_id and concept_id:
            concept_complete = check_concept_complete(
                pattern_id, concept_id, progress_compat, mode
            )
            if concept_complete:
                ui.print_styled(
                    f"\n✅ Concept complete: {quest.get('concept_name', concept_id)}",
                    "bold green",
                )

        # V2: Check pattern completion
        pattern_complete = False
        if pattern_id:
            all_problems_done = check_all_problems_complete(
                pattern_id, progress_compat, mode
            )
            is_mastered, unmet_criteria = check_pattern_mastery(
                pattern_id, progress_compat, mode
            )

            if all_problems_done and is_mastered:
                pattern_complete = True

                # Mark pattern as mastered in database
                if pattern_progress:
                    pattern_progress.mastered = True
                    db.upsert_pattern_progress(pattern_progress)

                # Add milestone to database
                db.add_milestone(
                    user_id="default",
                    milestone_type="pattern_mastered",
                    description=f"Mastered {pattern_name}",
                    pattern_id=pattern_id,
                )

                # Display completion message
                ui.print_styled(f"\n🎉 PATTERN MASTERED: {pattern_name}!", "bold green")

                # Show system design connections
                pattern_data = get_pattern_by_id(pattern_id, mode)
                if pattern_data:
                    sys_conn = pattern_data.get("system_design_connections", [])
                    if sys_conn:
                        ui.print_styled("\n🏗️  You now understand:", "bold magenta")
                        for conn in sys_conn[:3]:
                            ui.print_styled(f"   • {conn}", "magenta")

                # Unlock dependent patterns (updates progress_compat in place)
                newly_unlocked = unlock_dependent_patterns(
                    pattern_id, progress_compat, mode
                )
                if newly_unlocked:
                    ui.print_styled(
                        f"\n🔓 Unlocked {len(newly_unlocked)} new patterns!", "yellow"
                    )

            elif all_problems_done and not is_mastered:
                ui.print_styled(
                    "\n⚠️ All problems complete, but mastery criteria not met:", "yellow"
                )
                for criterion in unmet_criteria:
                    ui.print_styled(f"   • {criterion}", "dim")

        # Get current confidence for display
        confidence = pattern_progress.confidence if pattern_progress else 0

        # Display results
        if ui.rich_available and ui.console:
            ui.console.print("\n[bold green]🎉 VICTORY![/bold green]")

            # Show confidence gain
            if pattern_id and confidence > 0:
                ui.console.print(
                    f"[cyan]{pattern_name} confidence: {confidence:.0f}%[/cyan]"
                )

            if hints_used == 0:
                ui.console.print("[green]✓ No hints used![/green]")
        else:
            print("\n🎉 VICTORY!")

            # Show confidence gain
            if pattern_id and confidence > 0:
                print(f"{pattern_name} confidence: {confidence:.0f}%")

            if hints_used == 0:
                print("✓ No hints used!")

        # Auto-transition: Offer next problem
        if not pattern_complete:
            from dsa_coach.selection import get_next_quest_for_pattern

            next_in_pattern = (
                get_next_quest_for_pattern(pattern_id, progress_compat)
                if pattern_id
                else None
            )

            if next_in_pattern:
                next_name = next_in_pattern.get(
                    "problem_name", next_in_pattern.get("title", "Unknown")
                )

                print()
                ui.print_styled("  👉 What's next?", "bold white")
                ui.print_styled(f"     1. ⚔️  Continue: {next_name}", "green")
                ui.print_styled(f"     2. 📖 Learn more about {pattern_name}", "cyan")
                ui.print_styled("     3. 🔄 Switch to a different pattern", "white")
                ui.print_styled("     0. ← Done for now", "dim")

                choice = input("\n  Choose (1/2/3/0): ").strip()

                if choice == "1":
                    from dsa_coach.commands.next_quest import start_quest

                    start_quest(next_in_pattern, progress_compat, ui)
                    return
                if choice == "2":
                    from dsa_coach.commands.learn import cmd_learn

                    cmd_learn(pattern_id)
                    return
                if choice == "3":
                    from dsa_coach.commands.learn import cmd_learn

                    cmd_learn(None)
                    return

        ui.print_styled("\nRun 'python coach.py next' for your next quest.", "dim")
