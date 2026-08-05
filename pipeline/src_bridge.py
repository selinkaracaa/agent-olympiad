from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"


def ensure_src_imports() -> None:
    """Expose the repository's legacy flat `src/` modules to the package."""
    source = str(SRC_ROOT)
    if source not in sys.path:
        sys.path.insert(0, source)
