"""Tests for the command-safety gate (scripts/safety.py).

These pin the LLM/deterministic boundary: which commands may run unattended,
which need explicit human confirmation, and which are refused outright.
"""
import pytest

from safety import (
    Risk,
    UnsafeCommandError,
    assert_safe,
    classify_command,
    is_destructive,
)

# --- commands that must run unattended (the tool's own happy path) ---
ALLOWED = [
    "docker cp /tmp/app.py web_container:/app/app.py",
    "docker compose restart web_container",
    "docker logs web_container --tail 50",
    "docker ps -a",
    "ALTER TABLE projects ADD COLUMN max_age INT NULL",
    "DELETE FROM sessions WHERE expired_at < NOW()",  # scoped by WHERE
    "ls -la /app",
    "git status",
]

# --- destructive but recoverable: need explicit confirmation ---
CONFIRM = [
    ("rm -rf /app/cache", "recursive delete"),
    ("DROP TABLE projects", "drop table"),
    ("TRUNCATE TABLE logs", "truncate"),
    ("DELETE FROM users", "unfiltered DELETE"),
    ("ALTER TABLE projects DROP COLUMN max_age", "drop column"),
    ("git push --force origin main", "force push"),
    ("git push -f", "force push short flag"),
    ("git reset --hard HEAD~3", "hard reset"),
    ("docker rm -f web_container", "force remove container"),
    ("docker volume rm pgdata", "remove volume"),
    ("docker system prune -a", "system prune"),
    ("shutdown -h now", "shutdown"),
    ("reboot", "reboot"),
    ("killall -9 python", "sigkill"),
    ("chmod -R 777 /app", "world-writable chmod"),
]

# --- catastrophic / irreversible: refused even with confirmation ---
BLOCKED = [
    ("rm -rf /", "root wipe"),
    ("rm -rf /*", "root glob wipe"),
    ("rm -rf ~", "home wipe"),
    ("sudo rm -rf /", "root wipe with sudo"),
    ("mkfs.ext4 /dev/sda1", "format"),
    ("dd if=/dev/zero of=/dev/sda", "raw disk write"),
    ("DROP DATABASE production", "drop database"),
    ("", "empty command"),
    ("   ", "whitespace-only command"),
]


@pytest.mark.parametrize("cmd", ALLOWED)
def test_allowed_commands_pass(cmd):
    assert classify_command(cmd).risk is Risk.ALLOW
    assert is_destructive(cmd) is False
    # assert_safe returns a verdict (does not raise) for allowed commands
    assert assert_safe(cmd).risk is Risk.ALLOW


@pytest.mark.parametrize("cmd,label", CONFIRM)
def test_destructive_commands_need_confirmation(cmd, label):
    assert classify_command(cmd).risk is Risk.CONFIRM, label
    assert is_destructive(cmd) is True
    # without confirmation -> refused
    with pytest.raises(UnsafeCommandError):
        assert_safe(cmd)
    # with explicit confirmation -> allowed through
    assert assert_safe(cmd, confirmed=True).risk is Risk.CONFIRM


@pytest.mark.parametrize("cmd,label", BLOCKED)
def test_catastrophic_commands_are_blocked(cmd, label):
    assert classify_command(cmd).risk is Risk.BLOCK, label
    assert is_destructive(cmd) is True
    # blocked even when a human tries to confirm
    with pytest.raises(UnsafeCommandError):
        assert_safe(cmd)
    with pytest.raises(UnsafeCommandError):
        assert_safe(cmd, confirmed=True)


def test_multiline_command_cannot_dodge_a_rule():
    # whitespace/newlines are collapsed before matching
    sneaky = "docker cp x web:/app/x\nDROP   DATABASE   prod"
    assert classify_command(sneaky).risk is Risk.BLOCK


def test_verdict_reports_reason_and_match():
    verdict = classify_command("git push --force origin main")
    assert verdict.risk is Risk.CONFIRM
    assert "force" in verdict.reason.lower()
    assert verdict.matched  # non-empty match fragment


def test_rm_of_subdirectory_is_confirm_not_block():
    # deleting an app subdir is recoverable-ish; only root/home wipes are blocked
    assert classify_command("rm -rf /app/tmp").risk is Risk.CONFIRM


def test_case_insensitive_sql():
    assert classify_command("drop table foo").risk is Risk.CONFIRM
    assert classify_command("Drop Database foo").risk is Risk.BLOCK
