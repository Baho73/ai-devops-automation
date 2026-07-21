"""Tests for the deploy flow (scripts/deploy.py).

SSH / SFTP / Docker are mocked. We assert the exact commands the deployer
builds, that it skips container steps when no container path is given, and that
the wired safety gate refuses a command poisoned by an injected container path.
"""
from unittest.mock import MagicMock

import pytest

import deploy


def _fake_ssh():
    ssh = MagicMock()
    ssh.open_sftp.return_value = MagicMock()
    ssh.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
    return ssh


@pytest.fixture
def with_creds(monkeypatch):
    monkeypatch.setattr(deploy, "SERVER_HOST", "10.0.0.1")
    monkeypatch.setattr(deploy, "SERVER_PASSWORD", "secret")
    monkeypatch.setattr(deploy, "SERVER_USER", "root")
    monkeypatch.setattr(deploy, "SERVER_PORT", 22)
    monkeypatch.setattr(deploy, "CONTAINER_NAME", "web_container")


def _install_ssh(monkeypatch, ssh):
    monkeypatch.setattr(deploy.paramiko, "SSHClient", lambda: ssh)


def test_missing_credentials_exits(monkeypatch, capsys):
    monkeypatch.setattr(deploy, "SERVER_HOST", None)
    monkeypatch.setattr(deploy, "SERVER_PASSWORD", None)
    with pytest.raises(SystemExit) as exc:
        deploy.deploy_file("app.py", "/tmp/app.py", "/app/app.py")
    assert exc.value.code == 1
    assert "must be set" in capsys.readouterr().out


def test_happy_path_uploads_and_restarts(monkeypatch, with_creds):
    ssh = _fake_ssh()
    _install_ssh(monkeypatch, ssh)

    deploy.deploy_file("app.py", "/tmp/app.py", "/app/app.py")

    # file uploaded via SFTP
    ssh.open_sftp.return_value.put.assert_called_once_with("app.py", "/tmp/app.py")

    # exactly two remote commands: docker cp then compose restart
    commands = [call.args[0] for call in ssh.exec_command.call_args_list]
    assert commands == [
        "docker cp /tmp/app.py web_container:/app/app.py",
        "docker compose restart web_container",
    ]


def test_no_container_path_skips_docker(monkeypatch, with_creds):
    ssh = _fake_ssh()
    _install_ssh(monkeypatch, ssh)

    deploy.deploy_file("app.py", "/tmp/app.py", container_path=None)

    ssh.open_sftp.return_value.put.assert_called_once_with("app.py", "/tmp/app.py")
    # no docker commands executed
    ssh.exec_command.assert_not_called()


def test_injected_container_path_is_blocked(monkeypatch, with_creds, capsys):
    ssh = _fake_ssh()
    _install_ssh(monkeypatch, ssh)

    # attacker-controlled container path smuggles a root wipe
    with pytest.raises(SystemExit):
        deploy.deploy_file("app.py", "/tmp/app.py", "/app/app.py; rm -rf /")

    # the destructive command never reached the server
    ssh.exec_command.assert_not_called()
    assert "Refusing to run blocked command" in capsys.readouterr().out
