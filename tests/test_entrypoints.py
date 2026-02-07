"""Tests for CLI entrypoints and command dispatch."""

from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

import coach
from dsa_coach import main as package_main


def test_package_main_help_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dsa-coach", "--help"])

    package_main.main()

    out = capsys.readouterr().out
    assert "Package CLI entrypoint for DSA Coach" in out


def test_package_main_dashboard_dispatches_with_flags(monkeypatch):
    calls = {}

    def fake_dashboard(*, daemon: bool, stop: bool):
        calls["daemon"] = daemon
        calls["stop"] = stop

    monkeypatch.setattr(coach, "cmd_dashboard", fake_dashboard)
    monkeypatch.setattr(sys, "argv", ["dsa-coach", "dashboard", "--daemon", "--stop"])

    package_main.main()

    assert calls == {"daemon": True, "stop": True}


def test_package_main_runs_agent_mode_by_default(monkeypatch):
    called = {"ran": False}

    def fake_run_agent_mode():
        called["ran"] = True

    monkeypatch.setattr(coach, "run_agent_mode", fake_run_agent_mode)
    monkeypatch.setattr(sys, "argv", ["dsa-coach"])

    package_main.main()

    assert called["ran"] is True


def test_coach_main_help_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["coach.py", "-h"])

    coach.main()

    out = capsys.readouterr().out
    assert "DSA Coach entrypoint" in out


def test_coach_main_dispatches_dashboard(monkeypatch):
    calls = {}

    def fake_dashboard(*, daemon: bool, stop: bool):
        calls["daemon"] = daemon
        calls["stop"] = stop

    monkeypatch.setattr(coach, "cmd_dashboard", fake_dashboard)
    monkeypatch.setattr(sys, "argv", ["coach.py", "dashboard", "-d"])

    coach.main()

    assert calls == {"daemon": True, "stop": False}


def test_coach_main_runs_agent_mode_by_default(monkeypatch):
    called = {"ran": False}

    def fake_run_agent_mode():
        called["ran"] = True

    monkeypatch.setattr(coach, "run_agent_mode", fake_run_agent_mode)
    monkeypatch.setattr(sys, "argv", ["coach.py"])

    coach.main()

    assert called["ran"] is True


def test_run_agent_mode_imports_and_calls_agent_main(monkeypatch):
    called = {"ran": False}
    fake_loop_module = types.SimpleNamespace(
        main=lambda: called.__setitem__("ran", True)
    )
    monkeypatch.setitem(sys.modules, "dsa_coach.agent.loop", fake_loop_module)

    coach.run_agent_mode()

    assert called["ran"] is True


def test_run_agent_mode_exits_on_exception(monkeypatch, capsys):
    def raising_main():
        raise RuntimeError("boom")

    fake_loop_module = types.SimpleNamespace(main=raising_main)
    monkeypatch.setitem(sys.modules, "dsa_coach.agent.loop", fake_loop_module)

    with pytest.raises(SystemExit) as exc:
        coach.run_agent_mode()

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Error starting agent: boom" in out


def test_cmd_dashboard_stop_when_not_running(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))

    coach.cmd_dashboard(stop=True)

    assert "No dashboard server running" in capsys.readouterr().out


def test_cmd_dashboard_stop_handles_stale_pid(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    state_dir = Path(os.environ["HOME"]) / ".dsa-coach"
    state_dir.mkdir(parents=True, exist_ok=True)
    pid_file = state_dir / "dashboard.pid"
    pid_file.write_text("12345")

    def fake_kill(pid: int, sig: int):
        raise ProcessLookupError

    monkeypatch.setattr(os, "kill", fake_kill)

    coach.cmd_dashboard(stop=True)

    out = capsys.readouterr().out
    assert "Dashboard server was not running" in out
    assert not pid_file.exists()


def test_cmd_dashboard_reports_already_running(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    state_dir = Path(os.environ["HOME"]) / ".dsa-coach"
    state_dir.mkdir(parents=True, exist_ok=True)
    pid_file = state_dir / "dashboard.pid"
    pid_file.write_text("321")

    calls = []

    def fake_kill(pid: int, sig: int):
        calls.append((pid, sig))

    monkeypatch.setattr(os, "kill", fake_kill)

    coach.cmd_dashboard()

    out = capsys.readouterr().out
    assert "Dashboard already running (PID 321)" in out
    assert "Open: http://localhost:8501" in out
    assert calls == [(321, 0)]


def test_cmd_dashboard_daemon_mode_starts_process_and_writes_pid(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("HOME", str(tmp_path))

    class FakeProcess:
        pid = 9876

    popen_calls = []

    def fake_popen(cmd, stdout=None, stderr=None, start_new_session=False):
        popen_calls.append(
            {
                "cmd": cmd,
                "stdout": stdout,
                "stderr": stderr,
                "start_new_session": start_new_session,
            }
        )
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    coach.cmd_dashboard(daemon=True)

    state_dir = Path(os.environ["HOME"]) / ".dsa-coach"
    pid_file = state_dir / "dashboard.pid"
    assert pid_file.exists()
    assert pid_file.read_text() == "9876"

    out = capsys.readouterr().out
    assert "Dashboard started in background (PID 9876)" in out
    assert "Open: http://localhost:8501" in out
    assert popen_calls
    assert popen_calls[0]["cmd"][0:2] == ["streamlit", "run"]
    assert popen_calls[0]["cmd"][2].endswith("dsa_coach/web/dashboard.py")


def test_cmd_dashboard_foreground_mode_runs_streamlit(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    run_calls = []

    def fake_run(cmd):
        run_calls.append(cmd)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    coach.cmd_dashboard()

    out = capsys.readouterr().out
    assert "Starting dashboard at http://localhost:8501" in out
    assert run_calls
    assert run_calls[0][0:2] == ["streamlit", "run"]
    assert run_calls[0][2].endswith("dsa_coach/web/dashboard.py")
    assert run_calls[0][-2:] == ["--server.port", "8501"]
