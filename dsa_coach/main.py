"""Package CLI entrypoint for DSA Coach.

Usage:
    dsa-coach                     - Start interactive AI coach
    dsa-coach dashboard           - Open progress dashboard in browser
    dsa-coach dashboard --daemon  - Start dashboard in background
    dsa-coach dashboard --stop    - Stop background dashboard
"""

from __future__ import annotations

import sys


def main() -> None:
    """Main package entrypoint."""
    # Delegate to top-level script logic for a single behavior surface.
    from coach import cmd_dashboard, run_agent_mode

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
