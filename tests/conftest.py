import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

NS = 'xmlns:android="http://schemas.android.com/apk/res/android" xmlns:app="http://schemas.android.com/apk/res-auto"'


@pytest.fixture
def ns():
    return NS


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: needs a decoded upstream APK under work/ (skipped otherwise)")


def decoded_base():
    """The newest decoded upstream res dir, or None."""
    bases = sorted((ROOT / "work").glob("*/base/res")) if (ROOT / "work").exists() else []
    return bases[-1] if bases else None
