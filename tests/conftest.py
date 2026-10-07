import pytest

from quillframe import utils


@pytest.fixture(autouse=True)
def _fast_and_offline(monkeypatch):
    """No real sleeping between retries, and always reset the mocked transport."""
    monkeypatch.setattr(utils, "RETRY_BASE_DELAY", 0)
    yield
    utils.set_transport(None)
