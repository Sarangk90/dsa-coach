"""Tests for Obsidian tools."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from dsa_coach.tools.obsidian import (
    propose_pattern_note,
    create_pattern_note,
    list_existing_notes,
    update_note_with_insights,
    check_note_creation_criteria,
    create_problem_note,
)
from dsa_coach.obsidian.note_generator import (
    generate_pattern_note,
    generate_problem_note,
    get_filename_for_pattern,
)
from dsa_coach.obsidian.writer import (
    write_note,
    list_existing_notes as list_notes_func,
    note_exists,
)


@pytest.fixture
def temp_vault():
    """Create a temporary Obsidian vault for testing."""
    temp_dir = tempfile.mkdtemp()
    vault_path = Path(temp_dir) / "test-vault"
    vault_path.mkdir()
    (vault_path / "Patterns").mkdir()
    (vault_path / "Problems").mkdir()
    
    yield vault_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_vault_env(temp_vault):
    """Mock OBSIDIAN_VAULT_PATH environment variable."""
    with patch.dict(os.environ, {"OBSIDIAN_VAULT_PATH": str(temp_vault)}):
        yield temp_vault


class TestNoteGenerator:
    """Test note generation functions."""
    
    def test_generate_pattern_note_basic(self):
        """Test basic pattern note generation."""
        content = generate_pattern_note(
            pattern="sliding_window",
            title="Sliding Window",
            description="A technique for efficiently processing arrays.",
            why_matters="Critical for array/string problems.",
            trade_offs=[{
                "aspect": "Performance",
                "description": "O(n) vs O(n^2)",
                "when_to_use": "When you need optimal time complexity",
            }],
            code_example="def sliding_window(arr):\n    # Implementation\n    pass",
            code_explanation="This shows the core pattern.",
            sixty_second_pitch="Sliding window optimizes array traversal.",
            key_terminology=["window", "two pointers"],
            follow_up_questions=["How do you handle variable size?"],
            common_pitfalls=["Forgetting to move the left pointer"],
        )
        
        assert "# Sliding Window" in content
        assert "sliding_window" in content.lower()
        assert "## Core Concept" in content
        assert "## Implementation Approach" in content
        assert "## Interview Articulation Guide" in content
        assert "def sliding_window(arr):" in content
    
    def test_generate_pattern_note_with_frontmatter(self):
        """Test that frontmatter is generated correctly."""
        content = generate_pattern_note(
            pattern="two_pointers",
            title="Two Pointers",
            description="Use two pointers moving towards each other.",
            why_matters="Common pattern.",
            trade_offs=[],
            code_example="pass",
            code_explanation="See code",
            sixty_second_pitch="Two pointers technique.",
            key_terminology=["pointers"],
            follow_up_questions=["When to use?"],
            common_pitfalls=["Off by one"],
        )
        
        assert content.startswith("---")
        assert "title: Two Pointers" in content
        assert "tags:" in content
        assert "dsa/patterns" in content
    
    def test_get_filename_for_pattern(self):
        """Test filename generation."""
        assert get_filename_for_pattern("sliding_window") == "sliding-window.md"
        assert get_filename_for_pattern("two_pointers") == "two-pointers.md"


class TestWriter:
    """Test note writing functions."""
    
    def test_write_note_success(self, mock_vault_env):
        """Test successful note writing."""
        content = "# Test Note\n\nThis is a test."
        success, message, filepath = write_note(content, "test.md", "pattern")
        
        assert success
        assert filepath is not None
        assert filepath.exists()
        assert filepath.read_text() == content
    
    def test_write_note_no_overwrite(self, mock_vault_env):
        """Test that existing notes aren't overwritten by default."""
        content1 = "# Original"
        content2 = "# Modified"
        
        write_note(content1, "test.md", "pattern")
        success, message, filepath = write_note(content2, "test.md", "pattern", overwrite=False)
        
        assert not success
        assert "already exists" in message.lower()
        assert filepath.read_text() == content1  # Original preserved
    
    def test_write_note_with_overwrite(self, mock_vault_env):
        """Test overwriting existing note."""
        content1 = "# Original"
        content2 = "# Modified"
        
        write_note(content1, "test.md", "pattern")
        success, message, filepath = write_note(content2, "test.md", "pattern", overwrite=True)
        
        assert success
        assert filepath.read_text() == content2
    
    def test_list_existing_notes(self, mock_vault_env):
        """Test listing notes."""
        # Create some test notes
        write_note("# Pattern 1", "pattern1.md", "pattern")
        write_note("# Pattern 2", "pattern2.md", "pattern")
        write_note("# Problem 1", "problem1.md", "problem")
        
        all_notes = list_notes_func("all")
        assert len(all_notes) == 3
        
        pattern_notes = list_notes_func("pattern")
        assert len(pattern_notes) == 2
        
        problem_notes = list_notes_func("problem")
        assert len(problem_notes) == 1
    
    def test_note_exists(self, mock_vault_env):
        """Test checking if note exists."""
        assert not note_exists("test.md", "pattern")
        
        write_note("# Test", "test.md", "pattern")
        
        assert note_exists("test.md", "pattern")


@pytest.mark.asyncio
class TestObsidianTools:
    """Test Obsidian agent tools."""
    
    async def test_propose_pattern_note(self, mock_vault_env):
        """Test proposing a pattern note."""
        result = await propose_pattern_note(
            pattern="sliding_window",
            confidence=60.0,
            session_insights="Learned about variable-size windows",
        )
        
        assert result.success
        assert result.data is not None
        assert result.data["pattern"] == "sliding_window"
        assert result.data["filename"] == "sliding-window.md"
        assert "sections" in result.data
        assert result.data["needs_diagram"] == True  # High confidence
    
    async def test_propose_existing_note_fails(self, mock_vault_env):
        """Test that proposing fails if note already exists."""
        # Create existing note
        write_note("# Existing", "sliding-window.md", "pattern")
        
        result = await propose_pattern_note(
            pattern="sliding_window",
            confidence=50.0,
            session_insights="Test",
        )
        
        assert not result.success
        assert "already exists" in result.message.lower()
    
    async def test_create_pattern_note(self, mock_vault_env):
        """Test creating a pattern note."""
        result = await create_pattern_note(
            pattern="two_pointers",
            title="Two Pointers",
            description="Use two pointers.",
            why_matters="Common pattern",
            trade_offs='[{"aspect": "Test", "description": "Desc", "when_to_use": "Always"}]',
            code_example="def example(): pass",
            code_explanation="Simple example",
            sixty_second_pitch="Two pointers work well",
            key_terminology="left, right",
            follow_up_questions="When to use?",
            common_pitfalls="Off by one",
        )
        
        assert result.success
        assert result.data is not None
        assert "filepath" in result.data
        
        # Verify file was created
        filepath = Path(result.data["filepath"])
        assert filepath.exists()
        content = filepath.read_text()
        assert "# Two Pointers" in content
        assert "def example(): pass" in content
    
    async def test_list_existing_notes_tool(self, mock_vault_env):
        """Test list existing notes tool."""
        # Create some notes
        write_note("# Pattern", "test-pattern.md", "pattern")
        write_note("# Problem", "test-problem.md", "problem")
        
        result = await list_existing_notes("all")
        
        assert result.success
        assert result.data["count"] == 2
        assert len(result.data["notes"]) == 2
    
    async def test_update_note_with_insights(self, mock_vault_env):
        """Test updating a note."""
        # Create initial note
        write_note("# Test Note\n\nOriginal content", "test.md", "pattern")
        
        result = await update_note_with_insights(
            note_name="test",
            new_insights="New insight added",
            section_title="Update",
        )
        
        assert result.success
        
        # Verify content was appended
        filepath = Path(result.data["filepath"])
        content = filepath.read_text()
        assert "Original content" in content
        assert "New insight added" in content
        assert "## Update" in content
    
    async def test_check_note_creation_criteria_high_confidence(self):
        """Test note creation criteria with high confidence gain."""
        result = await check_note_creation_criteria(
            pattern="sliding_window",
            confidence=70.0,
            session_messages=8,
            confidence_gain=20.0,
        )
        
        assert result.success
        assert result.data["should_create"] == True
        reason = result.data.get("reason", result.message or "")
        assert "learned" in reason.lower() or "gain" in reason.lower()
    
    async def test_check_note_creation_criteria_short_session(self):
        """Test that short sessions don't trigger note creation."""
        result = await check_note_creation_criteria(
            pattern="test",
            confidence=30.0,
            session_messages=2,
            confidence_gain=5.0,
        )
        
        assert result.success
        assert result.data["should_create"] == False
        reason = result.data.get("reason", result.message or "")
        assert "short" in reason.lower()
    
    async def test_create_problem_note(self, mock_vault_env):
        """Test creating a problem note."""
        result = await create_problem_note(
            problem_id="two_sum",
            title="Two Sum",
            pattern="hash_map",
            difficulty="Easy",
            key_insight="Use hash map for O(1) lookup",
            trade_offs="Space vs time trade-off",
            edge_cases="Empty array, duplicates",
            solution_approach="Iterate through array once, checking hash map for complement",
            time_complexity="O(n)",
            space_complexity="O(n)",
        )
        
        assert result.success
        assert result.data is not None
        
        filepath = Path(result.data["filepath"])
        assert filepath.exists()
        content = filepath.read_text()
        assert "# Two Sum" in content
        assert "hash_map" in content.lower() or "hash-map" in content.lower()
        # Check that solution approach and complexity are present
        assert "Solution Approach" in content or "Key Insight" in content
        assert "Time" in content or "Space" in content


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the full workflow."""
    
    async def test_full_pattern_note_workflow(self, mock_vault_env):
        """Test complete workflow from proposal to creation."""
        # 1. Check criteria
        criteria_result = await check_note_creation_criteria(
            pattern="sliding_window",
            confidence=65.0,
            session_messages=10,
            confidence_gain=25.0,
        )
        assert criteria_result.data["should_create"]
        
        # 2. Propose note
        proposal_result = await propose_pattern_note(
            pattern="sliding_window",
            confidence=65.0,
            session_insights="Learned variable-size windows",
        )
        assert proposal_result.success
        
        # 3. Create note
        create_result = await create_pattern_note(
            pattern="sliding_window",
            title="Sliding Window",
            description="An optimization technique for array problems.",
            why_matters="Reduces time complexity from O(n²) to O(n).",
            trade_offs='[{"aspect": "Memory", "description": "Uses extra space", "when_to_use": "When optimization needed"}]',
            code_example="def sliding_window(arr, k):\n    # Core logic\n    return result",
            code_explanation="Maintains a window and slides it.",
            sixty_second_pitch="Sliding window optimizes array traversal.",
            key_terminology="window, left pointer, right pointer",
            follow_up_questions="How to handle variable size?, Edge cases?",
            common_pitfalls="Forgetting to shrink window, off-by-one errors",
            has_diagram=True,
        )
        assert create_result.success
        
        # 4. Verify note exists
        list_result = await list_existing_notes("pattern")
        assert list_result.data["count"] == 1
        assert list_result.data["notes"][0]["name"] == "sliding-window"
        
        # 5. Update with new insights
        update_result = await update_note_with_insights(
            note_name="sliding-window",
            new_insights="Also useful for longest substring problems.",
            section_title="Additional Insights",
        )
        assert update_result.success

