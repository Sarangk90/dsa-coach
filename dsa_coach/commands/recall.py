from datetime import datetime

from dsa_coach.quests import get_all_quests
from dsa_coach.storage.sync import SyncDatabase
from dsa_coach.ui import UI


def _calculate_next_interval(current_interval: int, rating: int) -> int:
    """Calculate next review interval based on rating (1-5)."""
    # Spaced repetition algorithm
    # Rating 1-2: Reset to 1 day (forgot)
    # Rating 3: Keep same interval
    # Rating 4: Double interval
    # Rating 5: Triple interval
    if rating <= 2:
        return 1
    if rating == 3:
        return current_interval
    if rating == 4:
        return min(current_interval * 2, 30)  # Cap at 30 days
    return min(current_interval * 3, 60)  # Cap at 60 days


def cmd_recall():
    """Spaced repetition quiz on due items."""
    # Setup UI
    ui = UI(rich_available=False, console=None)
    try:
        from rich.console import Console

        ui = UI(rich_available=True, console=Console())
    except ImportError:
        pass

    with SyncDatabase() as db:
        # Get due items from database
        due_items = db.get_due_reviews()

        if not due_items:
            ui.print_styled(
                "No items due for review! Great job staying on top of things.", "green"
            )
            return

        ui.print_styled(f"\n📚 {len(due_items)} items due for review\n", "cyan")

        # Quiz on each item
        all_quests = get_all_quests()

        for completion in due_items:
            # V2 uses problem_id, V1 uses id
            quest = next(
                (
                    q
                    for q in all_quests
                    if q.get("problem_id", q.get("id")) == completion.quest_id
                ),
                None,
            )
            if not quest:
                continue

            pattern_name = (
                quest.get("pattern_name", quest.get("pattern", "N/A"))
                .replace("_", " ")
                .title()
            )
            quest_title = quest.get(
                "problem_name", quest.get("title", completion.quest_id)
            )
            ui.print_styled(f"\n🎯 {quest_title}", "bold")
            ui.print_styled(f"Pattern: {pattern_name}", "dim")
            ui.print_styled(f"Review #{completion.review_count + 1}", "dim")

            input("\nPress Enter when you've recalled the solution approach...")

            # Show a hint as reminder
            hints = quest.get("hints", {})
            ui.print_styled(
                f"\nApproach: {hints.get('low', 'Review your solution file.')}",
                "yellow",
            )

            # Self-assessment
            rating_input = input("\nHow well did you remember? (1-5): ").strip()
            try:
                rating = max(1, min(5, int(rating_input)))
            except ValueError:
                rating = 3

            # Update review tracking
            completion.review_count += 1
            completion.last_reviewed = datetime.now()
            completion.next_review_in = _calculate_next_interval(
                completion.next_review_in, rating
            )

            db.upsert_quest_completion(completion)

            # Feedback based on rating
            if rating >= 4:
                ui.print_styled(
                    f"Great recall! Next review in {completion.next_review_in} days.",
                    "green",
                )
            elif rating == 3:
                ui.print_styled(
                    f"Decent recall. Next review in {completion.next_review_in} days.",
                    "yellow",
                )
            else:
                ui.print_styled(
                    f"Needs work. Reviewing again in {completion.next_review_in} day(s).",
                    "red",
                )

    ui.print_styled("\n✅ Review session complete!", "green")
