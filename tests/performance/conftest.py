"""
Performance tests are opt-in.

These tests may be slow, require extra tooling (e.g. Locust/gevent),
and can be unstable on some platforms/pythons during collection.

Run explicitly:
  RUN_PERFORMANCE_TESTS=1 python -m pytest -m performance
"""

import os

import pytest


_FLAG = (os.getenv("RUN_PERFORMANCE_TESTS") or "").strip().lower()
if _FLAG not in {"1", "true", "yes", "on"}:
    pytest.skip(
        "Performance tests are opt-in. Set RUN_PERFORMANCE_TESTS=1 to enable.",
        allow_module_level=True,
    )
