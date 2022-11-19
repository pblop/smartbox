"""Smartbox socket update manager."""

from dataclasses import dataclass
import jq
import logging
import re
from typing import Any, Callable, Dict, List

from .session import Session
from .socket import SocketSession

_LOGGER = logging.getLogger(__name__)


@dataclass
class DevDataSubscription:
    """Subscription for dev data callbacks."""

    compiled_jq: Any
    callback: Callable


@dataclass
class UpdateSubscription:
    """Subscription for updates."""

    path_regex: Any
    compiled_jq: Any
    callback: Callable


class UpdateManager(object):
    """Manages subscription callbacks to receive updates from a Smartbox socket."""

    def __init__(self, session: Session, device_id: str, **kwargs):
        """Create an UpdateManager for a smartbox socket."""
        self._socket_session = SocketSession(
            session, device_id, self._dev_data_cb, self._update_cb, **kwargs
        )
        self._dev_data_subscriptions: List[DevDataSubscription] = []
        self._update_subscriptions: List[UpdateSubscription] = []

    @property
    def socket_session(self) -> SocketSession:
        """Get the underlying socket session."""
        return self._socket_session

    async def run(self) -> None:
        """Run the socket session asynchronously, waiting for updates."""
        await self._socket_session.run()

    def subscribe_to_dev_data(self, jq_expr: str, callback: Callable) -> None:
        """Subscribe to receive device data."""
        sub = DevDataSubscription(compiled_jq=jq.compile(jq_expr), callback=callback)
        self._dev_data_subscriptions.append(sub)

    def subscribe_to_updates(
        self, path_regex: str, jq_expr: str, callback: Callable[..., None]
    ) -> None:
        """Subscribe to receive device and node data updates.

        Named groups in path_regex are passed as kwargs to callback.
        """
        sub = UpdateSubscription(
            path_regex=re.compile(path_regex),
            compiled_jq=jq.compile(jq_expr),
            callback=callback,
        )
        self._update_subscriptions.append(sub)

    def subscribe_to_device_away_status(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Subscribe to device away status updates."""
        self.subscribe_to_dev_data(".away_status", callback)
        self.subscribe_to_updates(r"^/mgr/away_status", ".body", callback)

    def subscribe_to_device_power_limit(self, callback: Callable[[int], None]) -> None:
        """Subscribe to device power limit updates."""
        self.subscribe_to_updates(
            r"^/htr_system/(setup|power_limit)",
            ".body.power_limit",
            lambda power_limit: callback(int(power_limit)),
        )

    def subscribe_to_node_status(
        self, callback: Callable[[str, int, Dict[str, Any]], None]
    ) -> None:
        """Subscribe to node status updates."""

        def wrapper(data: Dict[str, Any], node_type: str, addr: str) -> None:
            callback(node_type, int(addr), data),

        self.subscribe_to_updates(
            r"^/(?P<node_type>[^/]+)/(?P<addr>\d+)/status", ".body", wrapper
        )

    def _dev_data_cb(self, data: Dict[str, Any]) -> None:
        for sub in self._dev_data_subscriptions:
            for match in sub.compiled_jq.input(data):
                if match is not None:
                    sub.callback(match)

    def _update_cb(self, data: Dict[str, Any]) -> None:
        matched = False
        for sub in self._update_subscriptions:
            if "path" not in data:
                _LOGGER.error("Path not found in update data: %s", data)
                continue
            path_match = sub.path_regex.search(data["path"])
            if not path_match:
                continue
            path_match_kwargs = path_match.groupdict()
            for data_match in sub.compiled_jq.input(data):
                if data_match is not None:
                    matched = True
                    sub.callback(data_match, **path_match_kwargs)
        if not matched:
            _LOGGER.debug("No matches for update %s", data)
