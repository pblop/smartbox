from click.testing import CliRunner
import itertools
import json
import pytest
from unittest.mock import patch

import smartbox.cmd


_TEST_API_NAME = "api-foo"
_TEST_BASIC_AUTH = "dsfoijf093"
_TEST_USERNAME = "sldkfj"
_TEST_PASSWORD = "ji2jfl83f"

_TEST_DEV_1 = "a0a0a0a0a0a0a0a0a0"
_TEST_DEV_2 = "b1b1b1b1b1b1b1b1b1"
_TEST_DEVICES = [
    {
        "dev_id": _TEST_DEV_1,
        "name": "FOO",
    },
    {
        "dev_id": _TEST_DEV_2,
        "name": "BAR",
    },
]

_TEST_NODES = {
    _TEST_DEV_1: [
        {
            "addr": 1,
            "name": "test dev 1 node 1",
            "type": "htr",
        }
    ],
    _TEST_DEV_2: [
        {
            "addr": 1,
            "name": "test dev 2 node 1",
            "type": "htr",
        },
        {
            "addr": 2,
            "name": "test dev 2 node 2",
            "type": "acm",
        },
    ],
}

_TEST_NODE_STATUS = {
    _TEST_DEV_1: [
        {
            "active": True,
            "mtemp": "20.0",
            "power": "844.2",
        }
    ],
    _TEST_DEV_2: [
        {
            "active": True,
            "mtemp": "19.7",
            "power": "843.4",
        },
        {
            "active": False,
            "mtemp": "21.2",
            "power": "848.9",
        },
    ],
}

_TEST_NODE_SETUP = {
    _TEST_DEV_1: [
        {
            "sync_status": "ok",
            "units": "C",
        }
    ],
    _TEST_DEV_2: [
        {
            "sync_status": "ok",
            "units": "F",
        },
        {
            "sync_status": "ok",
            "units": "F",
        },
    ],
}

_TEST_AWAY_STATUS = {
    _TEST_DEV_1: {
        "away": False,
        "enabled": True,
        "forced": False,
    },
    _TEST_DEV_2: {
        "away": True,
        "enabled": True,
        "forced": False,
    },
}

_AUTH_ARGS = [
    "-a",
    _TEST_API_NAME,
    "-b",
    _TEST_BASIC_AUTH,
    "-u",
    _TEST_USERNAME,
    "-p",
    _TEST_PASSWORD,
]

runner = CliRunner()


@pytest.fixture
def mock_session(mocker):
    session = mocker.MagicMock()
    session.get_devices = mocker.MagicMock(return_value=_TEST_DEVICES)
    session.get_nodes = lambda dev_id: _TEST_NODES[dev_id]
    session.get_status = lambda dev_id, node: _TEST_NODE_STATUS[dev_id][
        node["addr"] - 1
    ]
    session.get_setup = lambda dev_id, node: _TEST_NODE_SETUP[dev_id][node["addr"] - 1]
    session.get_device_away_status = lambda dev_id: _TEST_AWAY_STATUS[dev_id]
    with patch("smartbox.cmd.Session", autospec=True, return_value=session):
        yield session


@pytest.fixture
def mock_socket_session(mocker):
    socket_session = mocker.MagicMock()
    socket_session.run = mocker.AsyncMock()
    with patch(
        "smartbox.cmd.SocketSession", autospec=True, return_value=socket_session
    ):
        yield socket_session


def test_devices(mock_session):
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["devices"],
    )
    assert response.exit_code == 0
    assert json.loads(response.output) == _TEST_DEVICES


def test_nodes(mock_session):
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["nodes"],
    )
    assert response.exit_code == 0
    for dev in _TEST_DEVICES:
        assert f"{dev['name']} (dev_id: {dev['dev_id']})" in response.output
    assert "test dev 1 node 1" in response.output
    assert "test dev 2 node 1" in response.output
    assert "test dev 2 node 2" in response.output


def test_status(mock_session):
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["status"],
    )
    assert response.exit_code == 0
    for dev in _TEST_DEVICES:
        assert f"{dev['name']} (dev_id: {dev['dev_id']})" in response.output
        for node in _TEST_NODES[dev["dev_id"]]:
            assert f"{node['name']} (addr: {node['addr']})" in response.output
            data = json.dumps(
                _TEST_NODE_STATUS[dev["dev_id"]][node["addr"] - 1],
                indent=4,
                sort_keys=True,
            )
            assert data in response.output


def test_set_status(mock_session):
    test_data = {"locked": True, "mode": "auto", "stemp": "22.5", "units": "C"}
    test_args = list(
        itertools.chain(
            *{f"--{k.replace('_', '-')}": v for k, v in test_data.items()}.items()
        )
    )
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["set-status", "-d", _TEST_DEV_1, "-n", 1] + test_args,
    )
    assert response.exit_code == 0
    mock_session.set_status.assert_called_with(
        _TEST_DEV_1, _TEST_NODES[_TEST_DEV_1][0], test_data
    )


def test_setup(mock_session):
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["setup"],
    )
    assert response.exit_code == 0
    for dev in _TEST_DEVICES:
        assert f"{dev['name']} (dev_id: {dev['dev_id']})" in response.output
        for node in _TEST_NODES[dev["dev_id"]]:
            assert f"{node['name']} (addr: {node['addr']})" in response.output
            data = json.dumps(
                _TEST_NODE_SETUP[dev["dev_id"]][node["addr"] - 1],
                indent=4,
                sort_keys=True,
            )
            assert data in response.output


def test_set_setup(mock_session):
    test_data = {"true_radiant_enabled": True}
    test_args = list(
        itertools.chain(
            *{f"--{k.replace('_', '-')}": v for k, v in test_data.items()}.items()
        )
    )
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["set-setup", "-d", _TEST_DEV_2, "-n", 2] + test_args,
    )
    assert response.exit_code == 0
    mock_session.set_setup.assert_called_with(
        _TEST_DEV_2, _TEST_NODES[_TEST_DEV_2][1], test_data
    )


def test_device_away_status(mock_session):
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["device-away-status"],
    )
    assert response.exit_code == 0
    for dev in _TEST_DEVICES:
        assert f"{dev['name']} (dev_id: {dev['dev_id']})" in response.output
        data = json.dumps(
            _TEST_AWAY_STATUS[dev["dev_id"]],
            indent=4,
            sort_keys=True,
        )
        assert data in response.output


def test_set_device_away_status(mock_session):
    test_data = {"away": True, "enabled": True, "forced": False}
    test_args = list(
        itertools.chain(
            *{f"--{k.replace('_', '-')}": v for k, v in test_data.items()}.items()
        )
    )
    response = runner.invoke(
        smartbox.cmd.smartbox,
        _AUTH_ARGS + ["set-device-away-status", "-d", _TEST_DEV_2] + test_args,
    )
    assert response.exit_code == 0
    mock_session.set_device_away_status.assert_called_with(_TEST_DEV_2, test_data)


def test_socket(mock_session, mock_socket_session):
    for dev in _TEST_DEVICES:
        response = runner.invoke(
            smartbox.cmd.smartbox,
            _AUTH_ARGS + ["socket", "-d", dev["dev_id"]],
        )
        assert response.exit_code == 0
        mock_socket_session.run.assert_called()
