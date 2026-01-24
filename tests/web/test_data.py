"""Tests for web dashboard data layer."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from dsa_coach.storage.models import QuestCompletion


class TestLoadSliceProblemIds:
    """Tests for load_slice_problem_ids function."""

    def test_returns_dict_with_three_slices(self):
        """Should return a dict with slice-1, slice-2, slice-3 keys."""
        from dsa_coach.web.data import load_slice_problem_ids

        result = load_slice_problem_ids()

        assert "slice-1" in result
        assert "slice-2" in result
        assert "slice-3" in result

    def test_slice_counts_match_expected(self):
        """Slice counts should match quests.json metadata: 22, 19, 13."""
        from dsa_coach.web.data import load_slice_problem_ids

        result = load_slice_problem_ids()

        # These counts come from quests.json metadata
        assert len(result["slice-1"]) == 22
        assert len(result["slice-2"]) == 19
        assert len(result["slice-3"]) == 13

    def test_slices_are_disjoint(self):
        """No problem should be in multiple slices."""
        from dsa_coach.web.data import load_slice_problem_ids

        result = load_slice_problem_ids()

        s1 = result["slice-1"]
        s2 = result["slice-2"]
        s3 = result["slice-3"]

        assert len(s1 & s2) == 0, "Slice 1 and 2 overlap"
        assert len(s1 & s3) == 0, "Slice 1 and 3 overlap"
        assert len(s2 & s3) == 0, "Slice 2 and 3 overlap"


class TestLoadAllProblems:
    """Tests for load_all_problems function."""

    def test_returns_list_of_dicts(self):
        """Should return a list of problem dicts."""
        from dsa_coach.web.data import load_all_problems

        result = load_all_problems()

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

    def test_problems_have_required_fields(self):
        """Each problem should have required fields."""
        from dsa_coach.web.data import load_all_problems

        result = load_all_problems()
        required_fields = [
            "problem_id",
            "problem_name",
            "pattern_id",
            "pattern_name",
            "difficulty",
            "slice",
            "is_google_l6",
        ]

        for problem in result[:10]:  # Check first 10
            for field in required_fields:
                assert field in problem, f"Missing field: {field}"


class TestCalculateStreak:
    """Tests for calculate_streak function."""

    def test_empty_completions_returns_zero(self):
        """No completions should return 0 streak."""
        from dsa_coach.web.data import calculate_streak

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = []

        result = calculate_streak(mock_db)
        assert result == 0

    def test_today_only_returns_one(self):
        """Activity only today returns streak of 1."""
        from dsa_coach.web.data import calculate_streak

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(
                id="test",
                quest_id="q1",
                pattern_id="p1",
                completed_at=datetime.now(),
            )
        ]

        result = calculate_streak(mock_db)
        assert result == 1

    def test_consecutive_days_counts_correctly(self):
        """Consecutive days should count as streak."""
        from dsa_coach.web.data import calculate_streak

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(
                id="t1", quest_id="q1", pattern_id="p1", completed_at=today
            ),
            QuestCompletion(
                id="t2", quest_id="q2", pattern_id="p1", completed_at=yesterday
            ),
            QuestCompletion(
                id="t3", quest_id="q3", pattern_id="p1", completed_at=two_days_ago
            ),
        ]

        result = calculate_streak(mock_db)
        assert result == 3

    def test_gap_breaks_streak(self):
        """A gap in days should break the streak."""
        from dsa_coach.web.data import calculate_streak

        today = datetime.now()
        two_days_ago = today - timedelta(days=2)  # Skip yesterday

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(
                id="t1", quest_id="q1", pattern_id="p1", completed_at=today
            ),
            QuestCompletion(
                id="t2", quest_id="q2", pattern_id="p1", completed_at=two_days_ago
            ),
        ]

        result = calculate_streak(mock_db)
        assert result == 1  # Only today counts


class TestVelocityMetrics:
    """Tests for get_velocity_metrics function."""

    def test_empty_returns_zeroes(self):
        """No completions should return zero metrics."""
        from dsa_coach.web.data import get_velocity_metrics

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = []

        result = get_velocity_metrics(mock_db)

        assert result["avg_per_week"] == 0.0
        assert result["best_week"] == 0
        assert result["power_day"] is None

    def test_groups_by_week_correctly(self):
        """Should group completions by ISO week."""
        from dsa_coach.web.data import get_velocity_metrics

        # Create completions spread across two weeks
        this_week = datetime(2025, 1, 20, 12, 0)  # Monday Week 4
        last_week = datetime(2025, 1, 13, 12, 0)  # Monday Week 3

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(
                id="t1", quest_id="q1", pattern_id="p1", completed_at=this_week
            ),
            QuestCompletion(
                id="t2", quest_id="q2", pattern_id="p1", completed_at=this_week
            ),
            QuestCompletion(
                id="t3", quest_id="q3", pattern_id="p1", completed_at=last_week
            ),
        ]

        result = get_velocity_metrics(mock_db)

        assert result["best_week"] == 2  # This week has 2

    def test_identifies_power_day(self):
        """Should identify the day with most completions."""
        from dsa_coach.web.data import get_velocity_metrics

        # 3 problems on Thursday, 1 on Monday
        thu1 = datetime(2025, 1, 16, 10, 0)  # Thursday
        thu2 = datetime(2025, 1, 16, 14, 0)
        thu3 = datetime(2025, 1, 16, 18, 0)
        mon = datetime(2025, 1, 13, 10, 0)  # Monday

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(id="t1", quest_id="q1", pattern_id="p1", completed_at=thu1),
            QuestCompletion(id="t2", quest_id="q2", pattern_id="p1", completed_at=thu2),
            QuestCompletion(id="t3", quest_id="q3", pattern_id="p1", completed_at=thu3),
            QuestCompletion(id="t4", quest_id="q4", pattern_id="p1", completed_at=mon),
        ]

        result = get_velocity_metrics(mock_db)

        assert result["power_day"] == "Thu"


class TestEstimateCompletionWeeks:
    """Tests for estimate_completion_weeks function."""

    def test_returns_none_for_zero_pace(self):
        """Zero pace should return None."""
        from dsa_coach.web.data import estimate_completion_weeks

        result = estimate_completion_weeks(10, 0)
        assert result is None

    def test_calculates_correctly(self):
        """Should calculate weeks correctly."""
        from dsa_coach.web.data import estimate_completion_weeks

        # 20 problems remaining, 4 per week = 5 weeks
        result = estimate_completion_weeks(20, 4)
        assert result == 5.0

        # 15 problems remaining, 7 per week = 2.1 weeks
        result = estimate_completion_weeks(15, 7)
        assert result == 2.1


class TestGetSliceProgress:
    """Tests for get_slice_progress function."""

    def test_returns_three_slices(self):
        """Should return data for all 3 slices."""
        from dsa_coach.web.data import get_slice_progress

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = []

        result = get_slice_progress(mock_db)

        assert len(result) == 3
        assert result[0]["slice"] == 1
        assert result[1]["slice"] == 2
        assert result[2]["slice"] == 3

    def test_slice_metadata_correct(self):
        """Slice names and readiness percentages should be correct."""
        from dsa_coach.web.data import get_slice_progress

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = []

        result = get_slice_progress(mock_db)

        assert result[0]["name"] == "Foundation"
        assert result[0]["readiness_pct"] == 70
        assert result[1]["name"] == "Expansion"
        assert result[1]["readiness_pct"] == 85
        assert result[2]["name"] == "Mastery"
        assert result[2]["readiness_pct"] == 93

    def test_counts_completions_correctly(self):
        """Should count completed problems in each slice."""
        from dsa_coach.web.data import get_slice_progress, load_slice_problem_ids

        # Get an actual slice-1 problem ID
        slice_ids = load_slice_problem_ids()
        slice1_id = list(slice_ids["slice-1"])[0]

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            QuestCompletion(
                id="t1",
                quest_id=slice1_id,
                pattern_id="dynamic_programming",
                completed_at=datetime.now(),
            )
        ]

        result = get_slice_progress(mock_db)

        assert result[0]["completed"] == 1
        assert result[1]["completed"] == 0
        assert result[2]["completed"] == 0


class TestGetFoundationProgress:
    """Tests for get_foundation_progress function."""

    def test_excludes_slice_problems(self):
        """Foundation should not include slice-tagged problems."""
        from dsa_coach.web.data import get_foundation_progress, load_slice_problem_ids

        # Get a slice-1 problem ID
        slice_ids = load_slice_problem_ids()
        slice1_id = list(slice_ids["slice-1"])[0]

        mock_db = MagicMock()
        mock_db.get_completed_quests.return_value = [
            # This is a slice problem - should NOT be in foundation
            QuestCompletion(
                id="t1",
                quest_id=slice1_id,
                pattern_id="dp",
                completed_at=datetime.now(),
            ),
            # This is a non-slice problem - SHOULD be in foundation
            QuestCompletion(
                id="t2",
                quest_id="arrays_hashing_two_sum",
                pattern_id="arrays_hashing",
                completed_at=datetime.now(),
            ),
        ]

        result = get_foundation_progress(mock_db)

        # Only the non-slice problem should be counted
        assert result["completed"] == 1
        assert result["patterns_touched"] == ["arrays_hashing"]


class TestGetDashboardData:
    """Tests for the main get_dashboard_data aggregator."""

    def test_returns_all_required_keys(self, tmp_path):
        """Should return dict with all expected keys."""
        from dsa_coach.web.data import get_dashboard_data

        with patch("dsa_coach.web.data.SyncDatabase") as mock_db_class:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.get_completed_quests.return_value = []
            mock_instance.get_all_pattern_progress.return_value = []
            mock_instance.get_due_reviews.return_value = []
            mock_db_class.return_value = mock_instance

            result = get_dashboard_data()

            required_keys = [
                "foundation",
                "slices",
                "patterns",
                "velocity",
                "problems",
                "due_reviews",
                "streak",
                "total_slice_problems",
                "total_slice_completed",
            ]
            for key in required_keys:
                assert key in result, f"Missing key: {key}"
