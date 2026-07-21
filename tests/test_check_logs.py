"""Tests for the log retrieval + error-detection logic (scripts/check_logs.py).

SSH / Docker are fully mocked: no network, no real server. We exercise the
real code path and assert on the command it builds and on how it classifies the
returned log text.
"""
from unittest.mock import MagicMock

import pytest

import check_logs


def _fake_ssh(stdout_text="", stderr_text=""):
    """Build a mock SSHClient whose exec_command returns the given log text."""
    stdout = MagicMock()
    stdout.read.return_value = stdout_text.encode()
    stderr = MagicMock()
    stderr.read.return_value = stderr_text.encode()

    ssh = MagicMock()
    ssh.exec_command.return_value = (MagicMock(), stdout, stderr)
    return ssh


@pytest.fixture
def with_creds(monkeypatch):
    """Provide fake, non-empty credentials so the guard clause passes."""
    monkeypatch.setattr(check_logs, "SERVER_HOST", "10.0.0.1")
    monkeypatch.setattr(check_logs, "SERVER_PASSWORD", "secret")
    monkeypatch.setattr(check_logs, "SERVER_USER", "root")
    monkeypatch.setattr(check_logs, "SERVER_PORT", 22)


def _install_ssh(monkeypatch, ssh):
    monkeypatch.setattr(check_logs.paramiko, "SSHClient", lambda: ssh)


def test_missing_credentials_exits(monkeypatch, capsys):
    monkeypatch.setattr(check_logs, "SERVER_HOST", None)
    monkeypatch.setattr(check_logs, "SERVER_PASSWORD", None)
    with pytest.raises(SystemExit) as exc:
        check_logs.check_logs("web_container", 50)
    assert exc.value.code == 1
    assert "must be set" in capsys.readouterr().out


def test_clean_logs_report_no_errors(monkeypatch, capsys, with_creds):
    ssh = _fake_ssh("GET / 200 OK\nGET /health 200 OK\n")
    _install_ssh(monkeypatch, ssh)

    check_logs.check_logs("web_container", 50)

    out = capsys.readouterr().out
    assert "No errors detected" in out
    assert "Errors detected" not in out


def test_error_logs_are_flagged(monkeypatch, capsys, with_creds):
    logs = (
        "GET / 200 OK\n"
        "Traceback (most recent call last):\n"
        "  File 'app.py', line 42, in handler\n"
        "AttributeError: 'NoneType' object has no attribute 'id'\n"
    )
    ssh = _fake_ssh(logs)
    _install_ssh(monkeypatch, ssh)

    check_logs.check_logs("web_container", 50)

    out = capsys.readouterr().out
    assert "Errors detected" in out
    # the offending lines are surfaced for the operator
    assert "AttributeError" in out
    assert "Traceback" in out


def test_stderr_errors_are_flagged(monkeypatch, capsys, with_creds):
    ssh = _fake_ssh(stdout_text="", stderr_text="CRITICAL: database connection refused")
    _install_ssh(monkeypatch, ssh)

    check_logs.check_logs("db_container", 20)

    out = capsys.readouterr().out
    assert "Errors detected" in out


def test_builds_correct_docker_command(monkeypatch, with_creds):
    ssh = _fake_ssh("ok")
    _install_ssh(monkeypatch, ssh)

    check_logs.check_logs("mycontainer", 20)

    cmd = ssh.exec_command.call_args[0][0]
    assert cmd == "docker logs mycontainer --tail 20"


def test_defaults_to_configured_container(monkeypatch, with_creds):
    monkeypatch.setattr(check_logs, "CONTAINER_NAME", "default_box")
    ssh = _fake_ssh("ok")
    _install_ssh(monkeypatch, ssh)

    check_logs.check_logs(None, 50)

    cmd = ssh.exec_command.call_args[0][0]
    assert cmd == "docker logs default_box --tail 50"
