import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture
def read_file():
    def _read_file(path):
        with open(path, "rb") as f:
            return f.read()
    return _read_file
