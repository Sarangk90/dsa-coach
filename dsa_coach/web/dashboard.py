"""Google L6 Interview Prep Progress Dashboard.

A comprehensive Streamlit dashboard for tracking interview preparation.
Run with: streamlit run dsa_coach/web/dashboard.py
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from dsa_coach.web.data import estimate_completion_weeks, get_dashboard_data

# Page configuration
st.set_page_config(
    page_title="Google L6 DSA Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Compact CSS to reduce padding and margins
st.markdown(
    """
<style>
    /* Reduce main container padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    /* Reduce header size */
    h1 { font-size: 1.5rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.2rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1rem !important; margin-bottom: 0.2rem !important; }
    h4 { font-size: 0.9rem !important; margin-bottom: 0.2rem !important; }
    /* Reduce metric spacing */
    [data-testid="stMetric"] {
        padding: 0.3rem 0;
    }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    /* Tighter dataframes */
    [data-testid="stDataFrame"] { font-size: 0.8rem; }
    /* Reduce column gaps */
    [data-testid="column"] { padding: 0 0.5rem; }
    /* Compact alerts */
    [data-testid="stAlert"] { padding: 0.3rem 0.5rem; margin: 0.2rem 0; }
    /* Smaller captions */
    .stCaption { font-size: 0.7rem !important; }
    /* Reduce expander padding */
    [data-testid="stExpander"] { margin-bottom: 0.3rem; }
</style>
""",
    unsafe_allow_html=True,
)


def main():
    """Main dashboard entry point."""
    # Load data
    data = get_dashboard_data()

    # Compact header with title and key stats inline
    col_title, col_stats = st.columns([2, 3])
    with col_title:
        st.title("Google L6 Interview Prep")
    with col_stats:
        render_compact_stats(data)

    # Row 1: Slice Progress (compact)
    render_slice_progress_compact(data)

    # Row 2: Pattern table + Due Reviews + Activity (3 columns)
    col1, col2, col3 = st.columns([2, 1, 1.5])
    with col1:
        render_pattern_table_compact(data)
    with col2:
        render_due_reviews_compact(data)
    with col3:
        render_activity_compact(data)

    # Row 3: Problem table (in expander)
    with st.expander(
        f"📋 Problem List ({len(data['problems'])} problems)", expanded=False
    ):
        render_problem_table(data)


def render_compact_stats(data: dict):
    """Render compact stats row at the top."""
    cols = st.columns(6)

    # Foundation
    with cols[0]:
        st.metric("Foundation", f"{data['foundation']['completed']} done")

    # Slice progress
    total = data["total_slice_problems"]
    done = data["total_slice_completed"]
    pct = int(done / total * 100) if total > 0 else 0
    with cols[1]:
        st.metric("Slices", f"{done}/{total}", delta=f"{pct}%")

    # Readiness status
    with cols[2]:
        if data["slices"][0]["completed"] == data["slices"][0]["total"]:
            readiness = (
                "85%"
                if data["slices"][1]["completed"] == data["slices"][1]["total"]
                else "70%"
            )
        else:
            readiness = f"{pct}%"
        st.metric("Readiness", readiness)

    # Velocity
    with cols[3]:
        st.metric("Pace", f"{data['velocity']['avg_per_week']}/wk")

    # Due reviews
    with cols[4]:
        due_count = len(data["due_reviews"])
        st.metric("Due", due_count, delta="⚠️" if due_count > 5 else None)

    # Streak
    with cols[5]:
        st.metric("Streak", f"{data['streak']}d")


def render_slice_progress_compact(data: dict):
    """Render compact slice progress as single row."""
    cols = st.columns(3)
    slice_colors = ["🟢", "🔵", "🟣"]

    for i, (col, slice_data) in enumerate(zip(cols, data["slices"], strict=True)):
        with col:
            pct = (
                slice_data["completed"] / slice_data["total"]
                if slice_data["total"] > 0
                else 0
            )
            label = f"{slice_colors[i]} S{slice_data['slice']}: {slice_data['name']}"
            st.progress(
                pct,
                text=f"{label} — {slice_data['completed']}/{slice_data['total']} ({slice_data['readiness_pct']}% ready)",
            )


def render_pattern_table_compact(data: dict):
    """Render compact pattern progress table."""
    st.markdown("**Patterns**")

    patterns = data["patterns"]
    table_data = []
    for p in patterns:
        bar = "█" * (p["progress"] // 20) + "░" * (5 - p["progress"] // 20)
        icon = (
            "✅"
            if p["status"] == "MASTERED"
            else "⚠️"
            if p["is_critical_gap"]
            else "🔄"
            if p["status"] == "In Progress"
            else "⬜"
        )
        table_data.append(
            {
                "Pattern": p["pattern_name"][:15],
                "Progress": f"{bar} {p['progress']}%",
                "Done": f"{p['completed']}/{p['total']}",
                "": icon,
            }
        )

    st.dataframe(table_data, use_container_width=True, hide_index=True, height=200)

    critical_gaps = [p for p in patterns if p["is_critical_gap"]]
    if critical_gaps:
        st.caption(f"⚠️ Gaps: {', '.join(p['pattern_name'] for p in critical_gaps)}")


def render_due_reviews_compact(data: dict):
    """Render compact due reviews."""
    st.markdown("**Due Reviews**")

    due = data["due_reviews"]
    if not due:
        st.success("None due!")
        return

    # Show as compact list
    for review in due[:6]:
        name = review["quest_id"].replace("_", " ").title()[:25]
        st.caption(f"• {name} ({review['days_since']}d)")

    if len(due) > 6:
        st.caption(f"...+{len(due) - 6} more")


def render_activity_compact(data: dict):
    """Render compact activity heatmap."""
    st.markdown("**Activity (6 weeks)**")

    calendar_data = data["velocity"]["calendar_data"]
    if not calendar_data:
        st.info("No data yet")
        return

    # Build heatmap
    calendar_weeks: dict[int, dict[str, int]] = {}
    for entry in calendar_data:
        week = entry["iso_week"]
        if week not in calendar_weeks:
            calendar_weeks[week] = {
                "Mon": 0,
                "Tue": 0,
                "Wed": 0,
                "Thu": 0,
                "Fri": 0,
                "Sat": 0,
                "Sun": 0,
            }
        calendar_weeks[week][entry["weekday"]] = entry["count"]

    week_labels = [f"W{w}" for w in sorted(calendar_weeks.keys())]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    z_data = [
        [calendar_weeks[w].get(day, 0) for w in sorted(calendar_weeks.keys())]
        for day in days
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=week_labels,
            y=days,
            colorscale=[
                [0, "#ebedf0"],
                [0.25, "#9be9a8"],
                [0.5, "#40c463"],
                [0.75, "#30a14e"],
                [1, "#216e39"],
            ],
            showscale=False,
            hovertemplate="%{y} W%{x}: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        height=150, margin={"l": 40, "r": 10, "t": 10, "b": 10}, xaxis={"side": "top"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Projections inline
    remaining = data["total_slice_problems"] - data["total_slice_completed"]
    if remaining > 0:
        weeks_est = estimate_completion_weeks(
            remaining, data["velocity"]["avg_per_week"]
        )
        st.caption(
            f"Est. {weeks_est} weeks @ current pace | Best day: {data['velocity']['power_day']}"
        )


def render_problem_table(data: dict):
    """Render the filterable problem table with inline filters."""
    problems = data["problems"]

    # Inline filters
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        slice_filter = st.selectbox(
            "Slice",
            ["All", "S1", "S2", "S3", "Foundation"],
            key="slice_f",
            label_visibility="collapsed",
        )
    with col2:
        pattern_ids = ["All"] + list({p["pattern_id"] for p in data["patterns"]})
        pattern_filter = st.selectbox(
            "Pattern", pattern_ids, key="pattern_f", label_visibility="collapsed"
        )
    with col3:
        status_filter = st.selectbox(
            "Status",
            ["All", "Done", "Todo"],
            key="status_f",
            label_visibility="collapsed",
        )

    # Apply filters
    if slice_filter == "S1":
        problems = [p for p in problems if p["slice"] == 1]
    elif slice_filter == "S2":
        problems = [p for p in problems if p["slice"] == 2]
    elif slice_filter == "S3":
        problems = [p for p in problems if p["slice"] == 3]
    elif slice_filter == "Foundation":
        problems = [p for p in problems if p["slice"] == 0]

    if pattern_filter != "All":
        problems = [p for p in problems if p["pattern_id"] == pattern_filter]

    if status_filter != "All":
        problems = [p for p in problems if p["status"] == status_filter]

    # Compact table
    table_data = []
    for i, p in enumerate(problems, 1):
        icon = "✅" if p["status"] == "Done" else "⬜"
        table_data.append(
            {
                "#": i,
                "Problem": p["problem_name"],
                "Pattern": p["pattern_name"][:12],
                "S": p["slice"] if p["slice"] > 0 else "-",
                "D": p["difficulty"][0].upper(),
                "": icon,
            }
        )

    if table_data:
        st.dataframe(table_data, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No problems match filters")


if __name__ == "__main__":
    main()
