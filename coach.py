#!/usr/bin/env python3
"""DSA Coach entrypoint.

Usage:
    python coach.py                     - Start interactive AI coach
    python coach.py dashboard           - Open progress dashboard in browser
    python coach.py dashboard --daemon  - Start dashboard in background
    python coach.py dashboard --stop    - Stop background dashboard
"""

from __future__ import annotations

import sys


def cmd_dashboard(daemon: bool = False, stop: bool = False) -> None:
    """Launch the Streamlit progress dashboard."""
    import os
    import signal
    import subprocess
    from pathlib import Path

    pid_file = Path.home() / ".dsa-coach" / "dashboard.pid"
    log_file = Path.home() / ".dsa-coach" / "dashboard.log"

    pid_file.parent.mkdir(parents=True, exist_ok=True)

    if stop:
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                pid_file.unlink()
                print(f"Dashboard server stopped (PID {pid})")
            except ProcessLookupError:
                pid_file.unlink()
                print("Dashboard server was not running")
        else:
            print("No dashboard server running")
        return

    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 0)
            print(f"Dashboard already running (PID {pid})")
            print("Open: http://localhost:8501")
            print("Stop with: python coach.py dashboard --stop")
            return
        except ProcessLookupError:
            pid_file.unlink()

    dashboard_path = Path(__file__).parent / "dsa_coach" / "web" / "dashboard.py"

    if daemon:
        with log_file.open("w") as log:
            proc = subprocess.Popen(
                ["streamlit", "run", str(dashboard_path), "--server.port", "8501"],
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        pid_file.write_text(str(proc.pid))
        print(f"Dashboard started in background (PID {proc.pid})")
        print("Open: http://localhost:8501")
        print(f"Logs: {log_file}")
        print("Stop with: python coach.py dashboard --stop")
    else:
        print("Starting dashboard at http://localhost:8501")
        print("Press Ctrl+C to stop")
        subprocess.run(
            ["streamlit", "run", str(dashboard_path), "--server.port", "8501"]
        )


def run_agent_mode() -> None:
    """Run the interactive AI coach agent."""
    try:
        from dsa_coach.agent.loop import main as agent_main

        agent_main()
    except Exception as e:  # pragma: no cover - top-level fail-safe
        print(f"Error starting agent: {e}")
        sys.exit(1)


def main() -> None:
    """Main entrypoint."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        return

    if len(sys.argv) > 1 and sys.argv[1].lower() == "dashboard":
        argv = sys.argv[2:]
        cmd_dashboard(daemon="--daemon" in argv or "-d" in argv, stop="--stop" in argv)
        return

    run_agent_mode()


if __name__ == "__main__":
    main()
