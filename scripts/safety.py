#!/usr/bin/env python3
"""Command-safety validation for the AI DevOps automation layer.

The automation is driven by an LLM operator (Claude Code) that decides which
shell / SQL commands to run against a production server over SSH. The operating
policy (see ``CLAUDE_CODE_PROMPT*.md``) forbids destructive actions without an
explicit human confirmation. This module turns that prose policy into an
enforceable gate, so the LLM/deterministic boundary does not rely on prompt
compliance alone.

Design choices:

* The gate never *rewrites* a command. It only classifies it and either lets it
  through, demands an explicit human acknowledgement, or refuses outright. A
  rewrite would silently change the operator's intent, which is worse than a
  hard stop.
* Classification is conservative and pattern-based (deny-by-signature, not
  allow-by-signature): an unknown command is treated as ``ALLOW`` because the
  scripts here run over an already-authenticated SSH session, and the goal is to
  catch the small set of irreversible foot-guns, not to sandbox every command.
* Three levels instead of a boolean, because "delete a container" (recoverable)
  and "drop the database" (irreversible) deserve different handling.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# START_BLOCK_SAFETY_MODEL


class Risk(str, Enum):
    """Risk level of a command."""

    ALLOW = "allow"      # safe to run unattended
    CONFIRM = "confirm"  # destructive but recoverable: needs explicit human ack
    BLOCK = "block"      # catastrophic / irreversible: never run automatically


@dataclass(frozen=True)
class Verdict:
    """Result of classifying a single command."""

    risk: Risk
    reason: str
    matched: str  # the substring that triggered the verdict ("" for ALLOW)


class UnsafeCommandError(RuntimeError):
    """Raised when a command is not permitted to run in the current mode."""


# END_BLOCK_SAFETY_MODEL

# START_BLOCK_SAFETY_RULES
# Irreversible / catastrophic: refused even with confirmation. Checked first.
_BLOCK_RULES: list[tuple[str, str]] = [
    (r"\brm\s+-[a-z]*r[a-z]*\s+(/\*|/|~|\$HOME)(\s|$)", "recursive delete of a root/home path"),
    (r"\bmkfs(\.\w+)?\b", "filesystem format"),
    (r"\bdd\b[^\n]*\bof=/dev/", "raw write to a block device"),
    (r">\s*/dev/(sd|nvme|hd|xvd)", "overwrite of a raw disk device"),
    (r":\(\)\s*\{[^}]*\|[^}]*&\s*\}", "fork bomb"),
    (r"\bDROP\s+DATABASE\b", "drop database (irreversible data loss)"),
]

# Destructive but recoverable: allowed only with an explicit human confirmation.
_CONFIRM_RULES: list[tuple[str, str]] = [
    (r"\brm\s+-[a-z]*r", "recursive delete"),
    (r"\bDROP\s+TABLE\b", "drop table"),
    (r"\bTRUNCATE\b", "truncate table"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "unfiltered DELETE (no WHERE clause)"),
    (r"\bALTER\s+TABLE\b[^;]*\bDROP\b", "drop column"),
    (r"\bgit\s+push\b[^\n]*(--force\b|--force-with-lease\b|\s-f\b)", "git force push"),
    (r"\bgit\s+reset\s+--hard\b", "git hard reset"),
    (r"\bdocker\s+(rm|rmi)\b[^\n]*\s-f\b", "force remove docker resource"),
    (r"\bdocker\s+volume\s+rm\b", "remove docker volume"),
    (r"\bdocker\s+system\s+prune\b", "docker system prune"),
    (r"\b(shutdown|reboot|halt|poweroff)\b", "host power-state change"),
    (r"\bkill(all)?\s+-9\b", "SIGKILL"),
    (r"\bchmod\s+-R\s+777\b", "recursive world-writable chmod"),
    (r">\s*/etc/", "overwrite of a system config file"),
]
# END_BLOCK_SAFETY_RULES

# START_BLOCK_SAFETY_API


def classify_command(command: str) -> Verdict:
    """Classify a command into ALLOW / CONFIRM / BLOCK.

    Whitespace (including embedded newlines) is collapsed before matching so a
    command cannot dodge a rule by wrapping across lines.
    """
    if not command or not command.strip():
        return Verdict(Risk.BLOCK, "empty command", "")

    norm = " ".join(command.split())

    for pattern, reason in _BLOCK_RULES:
        m = re.search(pattern, norm, re.IGNORECASE)
        if m:
            return Verdict(Risk.BLOCK, reason, m.group(0).strip())

    for pattern, reason in _CONFIRM_RULES:
        m = re.search(pattern, norm, re.IGNORECASE)
        if m:
            return Verdict(Risk.CONFIRM, reason, m.group(0).strip())

    return Verdict(Risk.ALLOW, "no destructive pattern matched", "")


def is_destructive(command: str) -> bool:
    """True if the command needs confirmation or is blocked outright."""
    return classify_command(command).risk is not Risk.ALLOW


def assert_safe(command: str, *, confirmed: bool = False) -> Verdict:
    """Raise ``UnsafeCommandError`` unless the command may run now.

    * BLOCK  -> always raises.
    * CONFIRM -> raises unless ``confirmed=True`` (a human has reviewed it).
    * ALLOW  -> returns the verdict.
    """
    verdict = classify_command(command)
    if verdict.risk is Risk.BLOCK:
        raise UnsafeCommandError(
            f"Refusing to run blocked command [{verdict.reason}]: {command!r}"
        )
    if verdict.risk is Risk.CONFIRM and not confirmed:
        raise UnsafeCommandError(
            f"Command requires explicit confirmation [{verdict.reason}]: {command!r}. "
            "Re-run with confirmed=True after a human review."
        )
    return verdict


# END_BLOCK_SAFETY_API
