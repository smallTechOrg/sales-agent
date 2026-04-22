# Phase-0 gate test — per spec/engineering/phases.md
from __future__ import annotations

import zer0


def test_version_is_importable() -> None:
    assert isinstance(zer0.__version__, str)
    assert len(zer0.__version__) > 0
