import pytest

from const import MOCK_ACCESS_TOKEN


@pytest.fixture
def mock_session(mocker):
    session = mocker.MagicMock()
    session._access_token = MOCK_ACCESS_TOKEN
    return session
