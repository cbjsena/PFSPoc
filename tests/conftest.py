import pytest
from pathlib import Path


@pytest.fixture
def base_data_dir(tmp_path, settings):
    """Fixture that sets BASE_DIR to a temporary path and returns it."""
    settings.BASE_DIR = tmp_path
    return tmp_path
