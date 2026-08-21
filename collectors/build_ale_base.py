#!/usr/bin/env python3
"""Compatibility wrapper.

The canonical Last Exam generator is collectors/build_last_exam_from_rules.py.
data/base remains a previous generated tree and is no longer the source of truth.
"""

from __future__ import annotations

from build_last_exam_from_rules import main


if __name__ == "__main__":
    main()
