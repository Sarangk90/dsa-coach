"""Tests for Streamlit dashboard rendering logic."""

from __future__ import annotations

from dataclasses import dataclass

from dsa_coach.web import dashboard


@dataclass
class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeStreamlit:
    def __init__(self, select_values: list[str] | None = None):
        self.select_values = list(select_values or [])
        self.dataframes: list[list[dict]] = []
        self.info_messages: list[str] = []
        self.success_messages: list[str] = []
        self.caption_messages: list[str] = []
        self.metric_calls: list[tuple[str, object, object]] = []
        self.title_calls: list[str] = []
        self.markdown_calls: list[str] = []
        self.progress_calls: list[tuple[float, str]] = []
        self.plotly_calls: list[object] = []

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [DummyContext() for _ in range(count)]

    def selectbox(self, *_args, **_kwargs):
        return self.select_values.pop(0)

    def dataframe(self, data, **_kwargs):
        self.dataframes.append(data)

    def info(self, message: str):
        self.info_messages.append(message)

    def success(self, message: str):
        self.success_messages.append(message)

    def caption(self, message: str):
        self.caption_messages.append(message)

    def metric(self, label, value, delta=None):
        self.metric_calls.append((label, value, delta))

    def title(self, message: str):
        self.title_calls.append(message)

    def markdown(self, message: str):
        self.markdown_calls.append(message)

    def progress(self, value: float, text: str):
        self.progress_calls.append((value, text))

    def plotly_chart(self, fig, **_kwargs):
        self.plotly_calls.append(fig)

    def expander(self, *_args, **_kwargs):
        return DummyContext()


def _sample_dashboard_data() -> dict:
    return {
        "foundation": {"completed": 8},
        "total_slice_problems": 10,
        "total_slice_completed": 6,
        "slices": [
            {
                "slice": 1,
                "name": "Core",
                "completed": 3,
                "total": 3,
                "readiness_pct": 100,
            },
            {
                "slice": 2,
                "name": "Advanced",
                "completed": 2,
                "total": 2,
                "readiness_pct": 100,
            },
            {
                "slice": 3,
                "name": "Stretch",
                "completed": 1,
                "total": 5,
                "readiness_pct": 20,
            },
        ],
        "velocity": {
            "avg_per_week": 4,
            "power_day": "Tuesday",
            "calendar_data": [],
        },
        "due_reviews": [],
        "streak": 7,
        "patterns": [
            {
                "pattern_id": "sliding_window",
                "pattern_name": "Sliding Window",
                "progress": 60,
                "completed": 3,
                "total": 5,
                "status": "In Progress",
                "is_critical_gap": False,
            }
        ],
        "problems": [
            {
                "problem_name": "Two Sum",
                "pattern_id": "hash_map",
                "pattern_name": "Hash Map",
                "slice": 1,
                "difficulty": "easy",
                "status": "Done",
            },
            {
                "problem_name": "Three Sum",
                "pattern_id": "two_pointers",
                "pattern_name": "Two Pointers",
                "slice": 2,
                "difficulty": "medium",
                "status": "Todo",
            },
        ],
    }


def test_render_problem_table_applies_filters(monkeypatch):
    fake_st = FakeStreamlit(select_values=["S1", "All", "Done"])
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.render_problem_table(_sample_dashboard_data())

    assert len(fake_st.dataframes) == 1
    rows = fake_st.dataframes[0]
    assert len(rows) == 1
    assert rows[0]["Problem"] == "Two Sum"


def test_render_problem_table_shows_info_when_no_matches(monkeypatch):
    fake_st = FakeStreamlit(select_values=["S3", "All", "All"])
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.render_problem_table(_sample_dashboard_data())

    assert fake_st.dataframes == []
    assert fake_st.info_messages == ["No problems match filters"]


def test_render_due_reviews_compact_shows_success_when_empty(monkeypatch):
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.render_due_reviews_compact({"due_reviews": []})

    assert fake_st.success_messages == ["None due!"]


def test_render_activity_compact_shows_info_when_no_calendar_data(monkeypatch):
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.render_activity_compact({"velocity": {"calendar_data": []}})

    assert fake_st.info_messages == ["No data yet"]


def test_render_compact_stats_sets_readiness_metric(monkeypatch):
    fake_st = FakeStreamlit()
    monkeypatch.setattr(dashboard, "st", fake_st)

    dashboard.render_compact_stats(_sample_dashboard_data())

    readiness_metrics = [m for m in fake_st.metric_calls if m[0] == "Readiness"]
    assert readiness_metrics
    assert readiness_metrics[0][1] == "85%"


def test_dashboard_main_orchestrates_renderer_calls(monkeypatch):
    fake_st = FakeStreamlit()
    data = _sample_dashboard_data()
    calls: dict[str, int] = {}

    def _mark(name):
        calls[name] = calls.get(name, 0) + 1

    monkeypatch.setattr(dashboard, "st", fake_st)
    monkeypatch.setattr(dashboard, "get_dashboard_data", lambda: data)
    monkeypatch.setattr(dashboard, "render_compact_stats", lambda _d: _mark("stats"))
    monkeypatch.setattr(
        dashboard, "render_slice_progress_compact", lambda _d: _mark("slice")
    )
    monkeypatch.setattr(
        dashboard, "render_pattern_table_compact", lambda _d: _mark("patterns")
    )
    monkeypatch.setattr(
        dashboard, "render_due_reviews_compact", lambda _d: _mark("due")
    )
    monkeypatch.setattr(
        dashboard, "render_activity_compact", lambda _d: _mark("activity")
    )
    monkeypatch.setattr(dashboard, "render_problem_table", lambda _d: _mark("problems"))

    dashboard.main()

    assert fake_st.title_calls == ["Google L6 Interview Prep"]
    assert calls == {
        "stats": 1,
        "slice": 1,
        "patterns": 1,
        "due": 1,
        "activity": 1,
        "problems": 1,
    }
