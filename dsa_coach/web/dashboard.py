"""Google L6 Interview Prep Progress Dashboard.

A comprehensive Streamlit dashboard for tracking interview preparation.
Run with: streamlit run dsa_coach/web/dashboard.py
"""

from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from dsa_coach.web.data import estimate_completion_weeks, get_dashboard_data

# Page configuration
st.set_page_config(
    page_title="Google L6 DSA Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main dashboard entry point."""
    # Load data
    data = get_dashboard_data()

    # Sidebar
    render_sidebar(data)

    # Main content
    st.title("Google L6 Interview Prep")
    st.markdown("---")

    # Section 1: Interview Readiness Header
    render_readiness_header(data)

    st.markdown("---")

    # Section 2: Slice Progress
    render_slice_progress(data)

    st.markdown("---")

    # Section 3: Pattern Confidence (two columns)
    col1, col2 = st.columns([2, 1])
    with col1:
        render_pattern_table(data)
    with col2:
        render_due_reviews(data)

    st.markdown("---")

    # Section 4: Velocity & Projections
    render_velocity_section(data)

    st.markdown("---")

    # Section 5: Problem Table
    render_problem_table(data)


def render_sidebar(data: dict):
    """Render sidebar with filters and info."""
    with st.sidebar:
        st.header("Dashboard Controls")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

        st.markdown("---")

        # Stats summary
        st.subheader("Quick Stats")
        st.metric("Current Streak", f"{data['streak']} days")
        st.metric("Due Reviews", len(data["due_reviews"]))
        st.metric("Avg Pace", f"{data['velocity']['avg_per_week']}/week")

        st.markdown("---")

        # Filter controls (stored in session state)
        st.subheader("Filters")

        # Slice filter
        slice_options = ["All", "Slice 1", "Slice 2", "Slice 3", "Foundation"]
        st.session_state.slice_filter = st.selectbox(
            "Filter by Slice",
            slice_options,
            index=0,
            key="slice_select",
        )

        # Pattern filter
        pattern_ids = ["All"] + [p["pattern_id"] for p in data["patterns"]]
        st.session_state.pattern_filter = st.selectbox(
            "Filter by Pattern",
            pattern_ids,
            index=0,
            key="pattern_select",
        )

        # Status filter
        status_options = ["All", "Done", "Todo"]
        st.session_state.status_filter = st.selectbox(
            "Filter by Status",
            status_options,
            index=0,
            key="status_select",
        )

        st.markdown("---")
        st.caption(f"Last updated: {date.today().strftime('%Y-%m-%d')}")


def render_readiness_header(data: dict):
    """Render the interview readiness header section."""
    col1, col2, col3 = st.columns([2, 2, 1])

    # Foundation progress
    with col1:
        st.subheader("Foundation (Completed)")
        foundation = data["foundation"]
        st.metric(
            "Basic Problems",
            f"{foundation['completed']} complete",
            help="Problems completed before starting Google L6 slices",
        )
        patterns_str = ", ".join(foundation["patterns_touched"][:5])
        if len(foundation["patterns_touched"]) > 5:
            patterns_str += "..."
        st.caption(f"Patterns: {patterns_str}")

    # Google L6 Slices progress
    with col2:
        st.subheader("Google L6 Slices (Focus)")
        total = data["total_slice_problems"]
        done = data["total_slice_completed"]
        pct = done / total if total > 0 else 0

        st.metric(
            "Slice Problems",
            f"{done}/{total}",
            delta=f"{pct * 100:.0f}% complete" if done > 0 else None,
        )
        st.progress(pct, text=f"{pct * 100:.0f}% toward interview ready")

        # Readiness status
        if done == 0:
            st.warning("Not started - complete Slice 1 for 70% readiness")
        elif data["slices"][0]["completed"] == data["slices"][0]["total"]:
            if data["slices"][1]["completed"] == data["slices"][1]["total"]:
                st.success("93% Interview Ready!")
            else:
                st.info("70% Interview Ready - working on Slice 2")
        else:
            remaining_s1 = data["slices"][0]["total"] - data["slices"][0]["completed"]
            st.info(f"Complete {remaining_s1} more for 70% readiness")

    # Velocity summary
    with col3:
        st.subheader("Velocity")
        velocity = data["velocity"]
        st.metric("Pace", f"{velocity['avg_per_week']}/week")
        st.metric("Best Week", f"{velocity['best_week']} problems")
        if velocity["power_day"]:
            st.caption(f"Power day: {velocity['power_day']}")


def render_slice_progress(data: dict):
    """Render the 3-column slice progress section."""
    st.subheader("Slice Progress")

    cols = st.columns(3)
    slice_colors = ["🟢", "🔵", "🟣"]
    slice_descriptions = [
        "Core DP, graphs, trees",
        "Backtracking, heaps, linked lists",
        "Advanced patterns, edge cases",
    ]

    for i, (col, slice_data) in enumerate(zip(cols, data["slices"], strict=True)):
        with col:
            pct = (
                slice_data["completed"] / slice_data["total"]
                if slice_data["total"] > 0
                else 0
            )

            st.markdown(
                f"### {slice_colors[i]} Slice {slice_data['slice']}: {slice_data['name']}"
            )
            st.caption(f"{slice_data['readiness_pct']}% interview-ready")
            st.progress(pct)
            st.metric(
                "Progress",
                f"{slice_data['completed']}/{slice_data['total']}",
                delta=f"{pct * 100:.0f}%" if slice_data["completed"] > 0 else None,
            )
            st.caption(slice_descriptions[i])

            # Estimate time remaining
            if slice_data["completed"] < slice_data["total"]:
                remaining = slice_data["total"] - slice_data["completed"]
                weeks = estimate_completion_weeks(
                    remaining, data["velocity"]["avg_per_week"]
                )
                if weeks:
                    st.caption(f"~{weeks} weeks at current pace")


def render_pattern_table(data: dict):
    """Render the pattern confidence table."""
    st.subheader("Pattern Confidence")

    # Prepare data for display
    patterns = data["patterns"]

    # Create the table
    table_data = []
    for p in patterns:
        confidence_bar = "█" * (p["confidence"] // 10) + "░" * (
            10 - p["confidence"] // 10
        )
        status_icon = (
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
                "Pattern": p["pattern_name"],
                "Confidence": f"{confidence_bar} {p['confidence']}%",
                "Problems": f"{p['completed']}/{p['total']}",
                "Status": f"{status_icon} {p['status']}",
            }
        )

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pattern": st.column_config.TextColumn("Pattern", width="medium"),
            "Confidence": st.column_config.TextColumn("Confidence", width="large"),
            "Problems": st.column_config.TextColumn("Problems", width="small"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
        },
    )

    # Highlight critical gaps
    critical_gaps = [p for p in patterns if p["is_critical_gap"]]
    if critical_gaps:
        st.warning(
            f"⚠️ Critical gaps: {', '.join(p['pattern_name'] for p in critical_gaps)}"
        )


def render_due_reviews(data: dict):
    """Render the due reviews section."""
    st.subheader("Due Reviews")

    due = data["due_reviews"]
    if not due:
        st.success("No reviews due!")
        return

    st.warning(f"⚠️ {len(due)} problems need review")

    for review in due[:5]:  # Show top 5
        st.markdown(
            f"- **{review['quest_id'].replace('_', ' ').title()}** "
            f"({review['pattern_id']}) - {review['days_since']} days ago"
        )

    if len(due) > 5:
        st.caption(f"...and {len(due) - 5} more")


def render_velocity_section(data: dict):
    """Render velocity charts and projections."""
    st.subheader("Velocity & Projections")

    col1, col2 = st.columns(2)

    with col1:
        # Weekly activity bar chart
        st.markdown("#### Weekly Activity")
        weekly = data["velocity"]["weekly"]
        if weekly:
            bar_weeks = list(weekly.keys())
            counts = list(weekly.values())

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=bar_weeks,
                        y=counts,
                        marker_color=[
                            "#4CAF50" if c >= 7 else "#2196F3" for c in counts
                        ],
                    )
                ]
            )
            fig.update_layout(
                height=250,
                margin={"l": 20, "r": 20, "t": 20, "b": 40},
                xaxis_title="",
                yaxis_title="Problems",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data yet")

    with col2:
        # Completion projections
        st.markdown("#### Completion Projections")
        remaining = data["total_slice_problems"] - data["total_slice_completed"]
        avg_pace = data["velocity"]["avg_per_week"]

        if remaining > 0:
            projections = [
                ("Current pace", avg_pace),
                ("Moderate (7/wk)", 7),
                ("Sprint (14/wk)", 14),
            ]

            for name, pace in projections:
                est_weeks = estimate_completion_weeks(remaining, pace)
                if est_weeks:
                    st.metric(
                        name, f"{est_weeks} weeks", delta=f"{remaining} remaining"
                    )
        else:
            st.success("All slice problems completed!")

    # Activity Calendar (Heatmap)
    st.markdown("#### Activity Calendar (Last 6 Weeks)")

    calendar_data = data["velocity"]["calendar_data"]
    if calendar_data:
        # Build heatmap data
        # Group by week and day
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

        # Convert to arrays for plotly
        week_labels = [f"W{w}" for w in sorted(calendar_weeks.keys())]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        z_data = []
        for day in days:
            row = [calendar_weeks[w].get(day, 0) for w in sorted(calendar_weeks.keys())]
            z_data.append(row)

        # Create heatmap
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
                hovertemplate="Week %{x}<br>%{y}: %{z} problems<extra></extra>",
            )
        )

        fig.update_layout(
            height=200,
            margin={"l": 60, "r": 20, "t": 20, "b": 20},
            xaxis={"side": "top"},
        )

        st.plotly_chart(fig, use_container_width=True)

        # Day of week summary
        daily = data["velocity"]["daily"]
        if daily:
            power_day = data["velocity"]["power_day"]
            st.caption(
                f"Most productive day: **{power_day}** ({daily.get(power_day, 0)} problems)"
            )
    else:
        st.info("Complete some problems to see activity data")


def render_problem_table(data: dict):
    """Render the filterable problem table."""
    st.subheader("Problem List")

    # Apply filters
    problems = data["problems"]

    # Filter by slice
    slice_filter = getattr(st.session_state, "slice_filter", "All")
    if slice_filter == "Slice 1":
        problems = [p for p in problems if p["slice"] == 1]
    elif slice_filter == "Slice 2":
        problems = [p for p in problems if p["slice"] == 2]
    elif slice_filter == "Slice 3":
        problems = [p for p in problems if p["slice"] == 3]
    elif slice_filter == "Foundation":
        problems = [p for p in problems if p["slice"] == 0]

    # Filter by pattern
    pattern_filter = getattr(st.session_state, "pattern_filter", "All")
    if pattern_filter != "All":
        problems = [p for p in problems if p["pattern_id"] == pattern_filter]

    # Filter by status
    status_filter = getattr(st.session_state, "status_filter", "All")
    if status_filter != "All":
        problems = [p for p in problems if p["status"] == status_filter]

    # Prepare table data
    table_data = []
    for i, p in enumerate(problems, 1):
        status_icon = "✅" if p["status"] == "Done" else "⬜"
        time_str = f"{p['time_minutes']}m" if p["time_minutes"] else "-"
        link = f"[🔗]({p['leetcode_url']})" if p["leetcode_url"] else ""

        table_data.append(
            {
                "#": i,
                "Problem": p["problem_name"],
                "Pattern": p["pattern_name"],
                "Slice": str(p["slice"]) if p["slice"] > 0 else "-",
                "Difficulty": p["difficulty"].capitalize(),
                "Status": f"{status_icon} {p['status']}",
                "Time": time_str,
                "Link": link,
            }
        )

    if table_data:
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Problem": st.column_config.TextColumn("Problem", width="large"),
                "Pattern": st.column_config.TextColumn("Pattern", width="medium"),
                "Slice": st.column_config.TextColumn("Slice", width="small"),
                "Difficulty": st.column_config.TextColumn("Difficulty", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Time": st.column_config.TextColumn("Time", width="small"),
                "Link": st.column_config.LinkColumn("Link", width="small"),
            },
        )
        st.caption(f"Showing {len(table_data)} problems")
    else:
        st.info("No problems match the current filters")


if __name__ == "__main__":
    main()
