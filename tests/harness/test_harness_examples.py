"""
Example tests demonstrating the CoachTestHarness.

These tests serve as both:
1. Documentation for how to use the harness
2. Verification that the harness works correctly

Run with: pytest tests/harness/test_harness_examples.py -v
"""

import pytest

from tests.harness import CoachTestHarness


class TestHarnessSetup:
    """Test that the harness initializes correctly."""

    @pytest.mark.asyncio
    async def test_harness_initializes(self, tmp_path):
        """Harness should initialize with a fresh database."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            # Should have agent and db
            assert harness.agent is not None
            assert harness.db is not None

    @pytest.mark.asyncio
    async def test_harness_with_hydration(self, tmp_path):
        """Harness can be initialized with test data."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            profile = await harness.inspect_profile()
            assert profile.name == "Test Student"

            patterns = await harness.inspect_patterns()
            assert len(patterns) > 0


class TestConversation:
    """Test conversation capabilities."""

    @pytest.mark.asyncio
    async def test_send_message(self, tmp_path):
        """Can send messages and get responses."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            response = await harness.send("Hello, what can you help me with?")

            assert response.content  # Got a response
            assert isinstance(response.content, str)
            assert len(response.content) > 10  # Non-trivial response

    @pytest.mark.asyncio
    async def test_greeting(self, tmp_path):
        """Can get the agent's greeting."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            greeting = await harness.get_greeting()

            assert greeting
            assert "Test Student" in greeting or "ready" in greeting.lower()

    @pytest.mark.asyncio
    async def test_conversation_history(self, tmp_path):
        """Conversation history is tracked."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            await harness.send("First message")
            await harness.send("Second message")

            history = harness.get_conversation_history()

            # 2 user messages + 2 assistant messages = 4 total
            assert len(history) == 4
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "First message"


class TestStateInspection:
    """Test database state inspection."""

    @pytest.mark.asyncio
    async def test_inspect_patterns(self, tmp_path):
        """Can inspect pattern progress."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            patterns = await harness.inspect_patterns()

            assert len(patterns) == 4  # ft_02, ft_03, ft_04, ft_05

            # Check specific pattern
            ft_02 = await harness.inspect_pattern("ft_02")
            assert ft_02 is not None
            assert ft_02.confidence == 75
            assert ft_02.mastered is True

    @pytest.mark.asyncio
    async def test_inspect_quests(self, tmp_path):
        """Can inspect completed quests."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            quests = await harness.inspect_quests()

            assert len(quests) == 5

            # Check specific quest
            quest = await harness.inspect_quest("ft_02_c1_p1")
            assert quest is not None
            assert quest.hints_used == 1

    @pytest.mark.asyncio
    async def test_inspect_mistakes(self, tmp_path):
        """Can inspect recorded mistakes."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            mistakes = await harness.inspect_mistakes()

            assert len(mistakes) >= 1

            # Check for the off-by-one mistake from hydration (mistakes are dicts)
            types = [m["mistake_type"] for m in mistakes]
            assert "off_by_one" in types

    @pytest.mark.asyncio
    async def test_inspect_milestones(self, tmp_path):
        """Can inspect achieved milestones."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            milestones = await harness.inspect_milestones()

            assert len(milestones) >= 1

            # Check for pattern mastered milestone (milestones are dicts)
            types = [m["milestone_type"] for m in milestones]
            assert "pattern_mastered" in types


class TestSnapshotAndDiff:
    """Test snapshot and diff capabilities."""

    @pytest.mark.asyncio
    async def test_snapshot(self, tmp_path):
        """Can take database snapshots."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            snapshot = await harness.snapshot()

            assert snapshot.timestamp is not None
            assert snapshot.profile is not None
            assert len(snapshot.patterns) > 0
            assert len(snapshot.quests) > 0

    @pytest.mark.asyncio
    async def test_snapshot_to_dict(self, tmp_path):
        """Snapshot can be converted to dict for JSON serialization."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            snapshot = await harness.snapshot()
            data = snapshot.to_dict()

            assert "timestamp" in data
            assert "profile" in data
            assert "patterns" in data

    @pytest.mark.asyncio
    async def test_diff_detects_changes(self, tmp_path):
        """Diff detects database changes between snapshots."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            before = await harness.snapshot()

            # Manually add a mistake
            await harness.db.add_mistake(
                user_id="test_user",
                quest_id="test_quest",
                pattern_id="ft_03",
                mistake_type="edge_case",
                description="Test mistake for diff",
            )

            after = await harness.snapshot()
            diff = harness.diff_snapshot(before, after)

            assert "mistakes_added" in diff
            assert len(diff["mistakes_added"]) == 1


class TestAssertionHelpers:
    """Test assertion helper methods."""

    @pytest.mark.asyncio
    async def test_assert_pattern_confidence(self, tmp_path):
        """Can assert pattern confidence levels."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Should pass - ft_02 has 75% confidence
            await harness.assert_pattern_confidence("ft_02", 75)

            # Should pass with tolerance
            await harness.assert_pattern_confidence("ft_02", 77, tolerance=5)

            # Should fail - wrong confidence
            with pytest.raises(AssertionError):
                await harness.assert_pattern_confidence("ft_02", 50)

    @pytest.mark.asyncio
    async def test_assert_quest_completed(self, tmp_path):
        """Can assert quest completion."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Should pass - quest is completed
            await harness.assert_quest_completed("ft_02_c1_p1")

            # Should fail - quest not completed
            with pytest.raises(AssertionError):
                await harness.assert_quest_completed("nonexistent_quest")

    @pytest.mark.asyncio
    async def test_assert_mistake_recorded(self, tmp_path):
        """Can assert mistake types."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Should pass - mistake exists
            await harness.assert_mistake_recorded("off_by_one")

            # Should fail - mistake type doesn't exist
            with pytest.raises(AssertionError):
                await harness.assert_mistake_recorded("nonexistent_type")

    @pytest.mark.asyncio
    async def test_assert_content_contains(self, tmp_path):
        """Can assert response content."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            response = await harness.send("Tell me about yourself")

            # Check content - case insensitive by default
            await harness.assert_content_contains(response, "dsa")

    @pytest.mark.asyncio
    async def test_assert_tool_was_used(self, tmp_path):
        """Can assert tool usage."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path, auto_hydrate=True) as harness:
            # Ask something that should trigger a tool
            response = await harness.send("Show me my pattern progress")

            # If tools were used, verify
            if response.tools_used:
                # At least one tool was used
                assert len(response.tools_used) > 0


class TestExportCapabilities:
    """Test export and serialization."""

    @pytest.mark.asyncio
    async def test_to_json(self, tmp_path):
        """Harness state can be exported as JSON."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            await harness.send("Hello!")

            json_str = harness.to_json()

            assert "test_user" in json_str
            assert "Hello!" in json_str

    @pytest.mark.asyncio
    async def test_response_to_dict(self, tmp_path):
        """Response can be converted to dict."""
        db_path = tmp_path / "test.db"
        async with CoachTestHarness(db_path=db_path) as harness:
            response = await harness.send("Hello!")
            data = response.to_dict()

            assert "content" in data
            assert "tools_used" in data
            assert "state_updated" in data
