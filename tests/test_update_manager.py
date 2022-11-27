import logging
from typing import Any, Dict
from unittest.mock import patch

from smartbox.update_manager import (
    DevDataSubscription,
    UpdateManager,
    UpdateSubscription,
)

from const import MOCK_DEV_ID


def test_dev_data_subscription():
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


def test_update_subscription():
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


async def _socket_dev_data(update_manager: UpdateManager, data: Dict[str, Any]) -> None:
    await update_manager.socket_session.namespace.on_dev_data(data)


async def _socket_update(update_manager: UpdateManager, data: Dict[str, Any]) -> None:
    await update_manager.socket_session.namespace.on_update(data)


async def test_integration(mocker, mock_session, caplog):
    caplog.set_level(logging.DEBUG)
    with patch("smartbox.update_manager.SocketSession.run") as mock_socket_run:
        update_manager = UpdateManager(mock_session, MOCK_DEV_ID)

        dev_data = {
            "away_status": {"away": True},
            "htr_system": {"setup": {"power_limit": 0}},
        }
        updates = [
            {"path": "/htr/1/status", "body": {"active": True, "mtemp": 22.5}},
            {"path": "/mgr/away_status", "body": {"away": True}},
            {"path": "/htr_system/setup", "body": {"power_limit": 1000}},
            {"path": "/htr_system/unknown_thing", "body": {"blah": "foo"}},
        ]

        async def run_first_updates() -> None:
            await _socket_dev_data(update_manager, dev_data)
            for update in updates:
                await _socket_update(update_manager, update)

        mock_socket_run.side_effect = run_first_updates

        # dev data
        dev_data_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(".", dev_data_sub)
        away_status_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(".away_status", away_status_sub)
        power_limit_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(
            ".htr_system.setup.power_limit", power_limit_sub
        )
        unmatched_sub = mocker.MagicMock()
        update_manager.subscribe_to_dev_data(
            ".htr_system.setup.unmatched", unmatched_sub
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

        await update_manager.run()
        mock_socket_run.assert_awaited()

        # dev data
        dev_data_sub.assert_called_with(dev_data)
        away_status_sub.assert_called_with({"away": True})
        power_limit_sub.assert_called_with(0)
        unmatched_sub.assert_not_called()

        # updates
        node_status_update_sub.assert_called_with(
            updates[0]["body"], node_type="htr", addr="1"
        )
        away_status_update_sub.assert_called_with(True)
        power_limit_update_sub.assert_called_with(1000)

        # specific functions
        away_status_specific_sub.assert_called_with({"away": True})
        power_limit_specific_sub.assert_called_with(1000)
        node_status_specific_sub.assert_called_with("htr", 1, updates[0]["body"])

        # Make sure we logged about the unknown update
        assert (
            "smartbox.update_manager",
            logging.DEBUG,
            "No matches for update {'path': '/htr_system/unknown_thing', 'body': {'blah': 'foo'}}",
        ) in caplog.record_tuples

        async def run_second_update() -> None:
            await _socket_update(
                update_manager,
                {"path": "/htr_system/power_limit", "body": {"power_limit": 500}},
            )

        mock_socket_run.side_effect = run_second_update
        await update_manager.run()
        mock_socket_run.assert_awaited()
        power_limit_update_sub.assert_called_with(500)
        power_limit_specific_sub.assert_called_with(500)
