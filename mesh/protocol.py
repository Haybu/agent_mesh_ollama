"""Wire protocol shared by the broker and all agents.

Routing convention:  "<agent>.<task>"   e.g. "finance.approve_order"
Payload data:        UTF-8 JSON object
Payload metadata:    RSocket composite metadata carrying the route
"""
import json
from typing import Any

from rsocket.extensions.composite_metadata import CompositeMetadata
from rsocket.extensions.helpers import composite, require_route, route
from rsocket.extensions.mimetypes import WellKnownMimeTypes
from rsocket.payload import Payload

BROKER_HOST = "localhost"
BROKER_PORT = 7878
METADATA_ENCODING = WellKnownMimeTypes.MESSAGE_RSOCKET_COMPOSITE_METADATA


def make_route(agent: str, task: str) -> str:
    return f"{agent}.{task}"


def target_agent(route_name: str) -> str:
    """Return the agent name that owns a route."""
    return route_name.split(".", 1)[0]


def encode(route_name: str, body: dict[str, Any]) -> Payload:
    return Payload(json.dumps(body).encode(), composite(route(route_name)))


def decode(payload: Payload) -> dict[str, Any]:
    return json.loads(payload.data.decode()) if payload.data else {}


def read_route(payload: Payload) -> str:
    return require_route(CompositeMetadata().parse(payload.metadata))


def setup_payload(agent: str) -> Payload:
    """Sent once on connect so the broker knows who this connection is."""
    return Payload(json.dumps({"agent": agent}).encode())
