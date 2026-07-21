"""Shared pytest fixtures / path setup.

The ``scripts/`` directory holds standalone modules (they import each other by
top-level name, e.g. ``from safety import assert_safe``, the same way they
resolve when run as ``python scripts/deploy.py``). Put it on ``sys.path`` so the
tests can import them without a package install.
"""
import os
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
