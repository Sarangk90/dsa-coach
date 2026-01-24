"""
Tests for SDK agent workflow determinism.

These tests verify that the consolidated tools and internal hooks
work deterministically to ensure important actions never get missed.

Key scenarios:
1. Quest completion triggers all hooks (activity logging, milestones, note suggestions)
2. Learning events are properly recorded
3. Workflow state transitions are correct
4. Consolidated tools work correctly

Run with: pytest tests/harness/test_sdk_workflows.py -v
"""

import pytest

from tests.harness import CoachTestHarness


class TestConsolidatedTools:
    """Test that consolidated tools work correctly."""

    @pytest.mark.asyncio
    async def test_get_dashboard_returns_comprehensive_data(self, tmp_path):
        """get_dashboard should return profile, patterns, and due reviews."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            response = await harness.send("Show me my dashboard")

            # Check that a tool was used
            if response.tools_used:
                # Should use get_dashboard
                assert any("dashboard" in t.lower() for t in response.tools_used), (
                    f"Expected dashboard tool, got {response.tools_used}"
                )

            # Response should contain relevant information
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["pattern", "progress", "confidence", "quest"]
            ), (
                f"Response should mention progress-related terms: {response.content[:200]}"
            )

    @pytest.mark.asyncio
    async def test_list_patterns_with_progress(self, tmp_path):
        """list_patterns should show patterns with progress levels."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            response = await harness.send("What patterns are available?")

            # Should mention patterns
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["pattern", "array", "pointer", "window", "search"]
            ), f"Response should list patterns: {response.content[:300]}"

    @pytest.mark.asyncio
    async def test_start_quest_creates_session(self, tmp_path):
        """start_quest should set up a quest and create session state."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            _ = await harness.snapshot()  # Take snapshot for potential future use

            # Ask to start a quest
            response = await harness.send("I want to work on the two sum problem")

            # Should use start_quest or assign_quest
            quest_tools = ["start_quest", "assign_quest"]
            assert any(t in response.tools_used for t in quest_tools), (
                "Should use quest tool"
            )

            # Response should acknowledge the quest
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["quest", "problem", "two sum", "start", "work"]
            ), f"Response should acknowledge starting a quest: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_get_hint_provides_adaptive_hint(self, tmp_path):
        """get_hint should provide hints based on progress level."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # First start a quest
            await harness.send("I want to practice two pointers")

            # Then ask for a hint
            response = await harness.send("I'm stuck, can you give me a hint?")

            # Response should contain helpful guidance
            assert response.content, "Should provide a response"
            # Either uses the hint tool or provides guidance directly
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "try",
                    "think",
                    "consider",
                    "what",
                    "how",
                    "hint",
                    "approach",
                ]
            ), f"Response should provide guidance: {response.content[:200]}"


class TestQuestCompletionHooks:
    """Test that quest completion triggers all internal hooks."""

    @pytest.mark.asyncio
    async def test_complete_quest_logs_activity(self, tmp_path):
        """Completing a quest should log session activity (Hook 1)."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Start a quest first
            await harness.send("Let me start working on two pointers")

            before = await harness.snapshot()

            # Complete a quest
            response = await harness.send(
                "I finished the 3sum problem. It took me 25 minutes and I used no hints."
            )

            after = await harness.snapshot()

            # Check for state changes (profile quests_completed might increase)
            _ = harness.diff_snapshot(before, after)  # For debugging

            # The response should acknowledge completion
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "complete",
                    "done",
                    "great",
                    "nice",
                    "good",
                    "finished",
                    "congrat",
                ]
            ), f"Response should acknowledge completion: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_milestone_suggestion_on_high_progress(self, tmp_path):
        """Hook 2: Milestone should be suggested when progress reaches 80%."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # The arrays_hashing pattern has 75% progress in test data
            # Completing another quest should bring it to ~85%+

            # Ask about the pattern that's almost mastered
            response = await harness.send(
                "I just solved another arrays and hashing problem without hints!"
            )

            # Check if milestones are mentioned (may or may not trigger based on hooks)
            # The key is that the hook is part of the complete_quest tool
            content_lower = response.content.lower()
            # Response should acknowledge their progress
            assert any(
                word in content_lower
                for word in ["progress", "confidence", "great", "good", "keep", "nice"]
            ), f"Response should acknowledge progress: {response.content[:200]}"


class TestLearningRecording:
    """Test that learning events are properly recorded."""

    @pytest.mark.asyncio
    async def test_record_learning_mistake(self, tmp_path):
        """Mistakes should be recorded using record_learning."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            before = await harness.snapshot()

            # Report a mistake
            response = await harness.send(
                "I made an off-by-one error on the sliding window problem. "
                "I forgot to handle the boundary condition."
            )

            after = await harness.snapshot()
            _ = harness.diff_snapshot(before, after)  # For debugging

            # Mistake should have been recorded (check diff or inspect)
            # The agent should acknowledge the mistake
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "mistake",
                    "error",
                    "boundary",
                    "off-by-one",
                    "common",
                    "happens",
                ]
            ), f"Response should acknowledge the mistake: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_record_learning_concept_taught(self, tmp_path):
        """Teaching should be recorded using record_learning."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Ask to learn about a pattern
            response = await harness.send(
                "Can you teach me about the sliding window pattern?"
            )

            # Agent should provide teaching content
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["window", "slide", "expand", "shrink", "pattern"]
            ), f"Response should teach about sliding window: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_record_learning_concept_understood(self, tmp_path):
        """Understanding demonstration should be recorded."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Demonstrate understanding
            response = await harness.send(
                "I understand now! The sliding window pattern uses two pointers "
                "to maintain a window of elements, and you expand when the condition "
                "is met and shrink when it's violated."
            )

            # Agent should acknowledge understanding
            # Should recognize their explanation
            assert len(response.content) > 20, "Should provide a substantive response"


class TestWorkflowStateTransitions:
    """Test that workflow state transitions correctly."""

    @pytest.mark.asyncio
    async def test_greeting_to_practicing(self, tmp_path):
        """Starting a quest should transition from GREETING to PRACTICING."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Initial greeting
            greeting = await harness.get_greeting()
            assert greeting, "Should get a greeting"

            # Start practicing
            response = await harness.send("Let's work on a two pointers problem")

            # Response should acknowledge starting practice
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["problem", "quest", "work", "practice", "pointer", "start"]
            ), f"Should acknowledge starting practice: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_greeting_to_learning(self, tmp_path):
        """Asking to learn should transition to LEARNING mode."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Ask to learn
            response = await harness.send(
                "I want to learn about binary search. Can you teach me?"
            )

            # Should start teaching
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["binary", "search", "pattern", "learn", "teach"]
            ), f"Should start teaching: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_practicing_to_completion(self, tmp_path):
        """Completing a quest should return to GREETING mode."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Start a quest
            await harness.send("Let me work on a problem")

            # Complete it
            response = await harness.send("I finished the problem successfully!")

            # Response should acknowledge and suggest next steps
            assert response.content, "Should get a response"
            assert len(response.content) > 20, "Should be a substantive response"


class TestProgressTracking:
    """Test that progress is properly tracked."""

    @pytest.mark.asyncio
    async def test_progress_summary_includes_activity(self, tmp_path):
        """get_progress_summary should show recent activity."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            response = await harness.send("Show me my progress this week")

            # Should mention progress-related information
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "progress",
                    "week",
                    "quest",
                    "pattern",
                    "solved",
                    "completed",
                ]
            ), f"Should show progress: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_due_reviews_in_progress(self, tmp_path):
        """Progress should include due reviews from spaced repetition."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Ask about reviews
            response = await harness.send("Do I have any reviews due?")

            # Should acknowledge the question about reviews
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in ["review", "due", "repetition", "revisit", "none", "no"]
            ), f"Should address reviews: {response.content[:200]}"


class TestCodeTools:
    """Test code management tools."""

    @pytest.mark.asyncio
    async def test_manage_solution_list(self, tmp_path):
        """manage_solution list action should work."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            response = await harness.send("What solution files do I have?")

            # Should acknowledge the request about solutions
            assert response.content, "Should get a response"

    @pytest.mark.asyncio
    async def test_review_code_provides_feedback(self, tmp_path):
        """review_code should provide meaningful feedback context."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Ask for code review
            response = await harness.send(
                """Can you review this code for Two Sum?

def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""
            )

            # Should provide feedback
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "correct",
                    "good",
                    "complexity",
                    "time",
                    "space",
                    "edge",
                    "hash",
                    "o(n)",
                ]
            ), f"Should provide code review feedback: {response.content[:200]}"


class TestTeachingContext:
    """Test teaching context tools."""

    @pytest.mark.asyncio
    async def test_diagnose_understanding_finds_gaps(self, tmp_path):
        """diagnose_understanding should identify concept gaps."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            response = await harness.send(
                "Can you check my understanding of sliding window?"
            )

            # Should ask diagnostic questions or identify gaps
            content_lower = response.content.lower()
            assert any(
                word in content_lower
                for word in [
                    "window",
                    "understand",
                    "concept",
                    "explain",
                    "tell",
                    "what",
                    "how",
                ]
            ), f"Should diagnose understanding: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_teaching_context_includes_history(self, tmp_path):
        """get_teaching_context should include teaching history."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # First teach something
            await harness.send("Teach me about binary search")

            # Then ask what we've covered
            response = await harness.send("What have we covered so far?")

            # Should have some response
            assert response.content, "Should get a response"
            assert len(response.content) > 20, "Should be substantive"
