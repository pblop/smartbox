import logging
import re
from typing import Any, Dict, List
from unittest.mock import patch

from smartbox.update_manager import (
    DevDataSubscription,
    OptimisedJQMatcher,
    UpdateManager,
    UpdateSubscription,
)

from const import MOCK_DEV_ID


def test_optimised_jq_matcher():
    matcher = OptimisedJQMatcher(".foo")
    assert repr(matcher) == "OptimisedJQMatcher('.foo', fast_path=True)"
    assert str(matcher) == "OptimisedJQMatcher('.foo', fast_path=True)"

    matcher = OptimisedJQMatcher(".foo[1]")
    assert repr(matcher) == "jq.compile('.foo[1]')"
    assert str(matcher) == "jq.compile('.foo[1]')"


def test_dev_data_subscription(caplog):
    result = []

    def callback(data):
        result.append(data)

    sub = DevDataSubscription(".foo", callback)
    sub.match({"foo": "bar"})
    assert result == ["bar"]

    result = []
    sub.match({"fooboo": "bar"})
    assert result == []

    # multiple
    sub2 = DevDataSubscription(".foo[1]", callback)
    result = []
    sub2.match({"foo": ["bar", "baz"]})
    assert result == ["baz"]

    # invalid
    sub3 = DevDataSubscription(".foo[]", callback)
    result = []
    sub3.match({"bar": []})

    _assert_log_message(
        "smartbox.update_manager",
        logging.ERROR,
        "Error evaluating jq on dev data",
        caplog.record_tuples,
    )


def _assert_log_message(name: str, level: int, msg_regex: str, record_tuples: List):
    assert any(
        (name == record_name and level == record_level and re.search(msg_regex, msg))
        for record_name, record_level, msg in record_tuples
    )


def test_update_subscription(caplog):
    result = []

    def callback(data):
        result.append(data)

    sub = UpdateSubscription("^/foo", ".body.foo", callback)
    sub.match({"path": "/foo", "body": {"foo": "bar"}})
    assert result == ["bar"]

    # jq mismatch
    result = []
    sub.match({"path": "/foo", "body": {"fooboo": "bar"}})
    assert result == []

    # path mismatch
    result = []
    sub.match({"path": "/bar", "body": {"foo": "bar"}})
    assert result == []

    # multiple
    sub2 = UpdateSubscription("^/foo", ".body.foo[1]", callback)
    result = []
    sub2.match({"path": "/foo", "body": {"foo": ["bar", "baz"]}})
    assert result == ["baz"]

    # invalid
    sub3 = UpdateSubscription("^/foo", ".body.foo[]", callback)
    result = []
    sub3.match({"path": "/foo", "body": {"bar": []}})

    _assert_log_message(
        "smartbox.update_manager",
        logging.ERROR,
        "Error evaluating jq on update",
        caplog.record_tuples,
    )


async def _socket_dev_data(update_manager: UpdateManager, data: Dict[str, Any]) -> None:
    await update_manager.socket_session.namespace.on_dev_data(data)


async def _socket_update(update_manager: UpdateManager, data: Dict[str, Any]) -> None:
    await update_manager.socket_session.namespace.on_update(data)


async def test_integration(mocker, mock_session, caplog):
    caplog.set_level(logging.DEBUG)
    with patch("smartbox.update_manager.SocketSession.run") as mock_socket_run:
        update_manager = UpdateManager(mock_session, MOCK_DEV_ID)

        dev_data = {
            "away_status": {"away": False},
            "htr_system": {"setup": {"power_limit": "0"}},
            "nodes": [
                {
                    "addr": 1,
                    "type": "htr",
                    "status": {"active": True, "mtemp": 22.0},
                    "setup": {"window_mode_enabled": False},
                }
            ],
        }
        updates = [
            {"path": "/htr/1/status", "body": {"active": True, "mtemp": 22.5}},
            {"path": "/mgr/away_status", "body": {"away": True}},
            {"path": "/htr_system/power_limit", "body": {"power_limit": "1000"}},
            {"path": "/htr_system/unknown_thing", "body": {"blah": "foo"}},
            {"path": "/htr/1/setup", "body": {"window_mode_enabled": True}},
        ]

        # dev data
        dev_data_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(".", dev_data_sub)
        away_status_dev_data_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(".away_status", away_status_dev_data_sub)
        power_limit_dev_data_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(
            ".htr_system.setup.power_limit", power_limit_dev_data_sub
        )
        unmatched_dev_data_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(
            ".htr_system.setup.unmatched", unmatched_dev_data_sub
        )

        # updates
        node_status_update_sub = mocker.MagicMock()
        update_manager.subscribe_to_updates(
            r"^/(?P<node_type>[^/]+)/(?P<addr>\d+)/status",
            ".body",
            node_status_update_sub,
        )
        away_status_update_sub = mocker.MagicMock()
        update_manager.subscribe_to_updates(
            r"^/mgr/away_status", ".body.away", away_status_update_sub
        )
        power_limit_update_sub = mocker.MagicMock()
        update_manager.subscribe_to_updates(
            r"^/htr_system/(setup|power_limit)",
            ".body.power_limit",
            power_limit_update_sub,
        )

        # specific functions
        away_status_specific_sub = mocker.MagicMock()
        update_manager.subscribe_to_device_away_status(away_status_specific_sub)
        power_limit_specific_sub = mocker.MagicMock()
        update_manager.subscribe_to_device_power_limit(power_limit_specific_sub)
        node_status_specific_sub = mocker.MagicMock()
        update_manager.subscribe_to_node_status(node_status_specific_sub)
        node_setup_specific_sub = mocker.MagicMock()
        update_manager.subscribe_to_node_setup(node_setup_specific_sub)

        # dev data
        async def send_dev_data() -> None:
            await _socket_dev_data(update_manager, dev_data)

        mock_socket_run.side_effect = send_dev_data
        await update_manager.run()
        mock_socket_run.assert_awaited()

        dev_data_sub.assert_called_with(dev_data)
        away_status_dev_data_sub.assert_called_with({"away": False})
        power_limit_dev_data_sub.assert_called_with("0")
        unmatched_dev_data_sub.assert_not_called()
        away_status_specific_sub.assert_called_with({"away": False})
        node_status_specific_sub.assert_called_with(
            "htr", 1, dev_data["nodes"][0]["status"]
        )
        power_limit_specific_sub.assert_called_with(0)
        node_setup_specific_sub.assert_called_with(
            "htr", 1, {"window_mode_enabled": False}
        )

        async def run_first_updates() -> None:
            for update in updates:
                await _socket_update(update_manager, update)

        mock_socket_run.side_effect = run_first_updates
        await update_manager.run()
        mock_socket_run.assert_awaited()

        node_status_update_sub.assert_called_with(
            updates[0]["body"], node_type="htr", addr="1"
        )
        away_status_update_sub.assert_called_with(True)
        power_limit_update_sub.assert_called_with("1000")
        node_setup_specific_sub.assert_called_with(
            "htr", 1, {"window_mode_enabled": True}
        )

        away_status_specific_sub.assert_called_with({"away": True})
        assert isinstance(away_status_specific_sub.call_args[0][0]["away"], bool)
        node_status_specific_sub.assert_called_with("htr", 1, updates[0]["body"])
        power_limit_specific_sub.assert_called_with(1000)
        assert isinstance(power_limit_specific_sub.call_args[0][0], int)

        # Make sure we logged about the unknown update
        assert (
            "smartbox.update_manager",
            logging.DEBUG,
            "No matches for update {'path': '/htr_system/unknown_thing',"
            " 'body': {'blah': 'foo'}}",
        ) in caplog.record_tuples

        async def run_second_update() -> None:
            await _socket_update(
                update_manager,
                {"path": "/htr_system/power_limit", "body": {"power_limit": "500"}},
            )

        mock_socket_run.side_effect = run_second_update
        await update_manager.run()
        mock_socket_run.assert_awaited()
        power_limit_update_sub.assert_called_with("500")
        power_limit_specific_sub.assert_called_with(500)
        assert isinstance(power_limit_specific_sub.call_args[0][0], int)
