"""RSocket broker: accepts agent connections and routes requests between them.

RSocket is bidirectional, so the broker can send requests *to* an agent over
the same connection that agent opened. Agents never connect to each other.
"""
import asyncio
import json
import logging

from rsocket.helpers import create_future
from rsocket.payload import Payload
from rsocket.request_handler import BaseRequestHandler
from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP

from mesh.protocol import BROKER_HOST, BROKER_PORT, read_route, target_agent

log = logging.getLogger("broker")


class Registry:
    """Agent name -> live RSocket connection."""

    def __init__(self):
        self._agents: dict[str, RSocketServer] = {}

    def add(self, name: str, socket: RSocketServer) -> None:
        self._agents[name] = socket
        log.info("registered '%s'  online=%s", name, sorted(self._agents))

    def remove(self, socket: RSocketServer) -> None:
        for name, s in list(self._agents.items()):
            if s is socket:
                del self._agents[name]
                log.info("'%s' disconnected", name)

    def get(self, name: str) -> RSocketServer:
        if name not in self._agents:
            raise LookupError(f"agent '{name}' is not connected")
        return self._agents[name]


class BrokerHandler(BaseRequestHandler):
    """One handler per agent connection."""

    def __init__(self, registry: Registry, socket_ref):
        super().__init__()
        self._registry, self._socket_ref = registry, socket_ref

    async def on_setup(self, data_encoding, metadata_encoding, payload: Payload):
        agent = json.loads(payload.data.decode())["agent"]
        self._registry.add(agent, self._socket_ref())

    async def request_response(self, payload: Payload):
        route_name = read_route(payload)
        target = self._registry.get(target_agent(route_name))
        log.info("route %s", route_name)
        response = await target.request_response(payload)  # forward unchanged
        return create_future(response)

    async def on_close(self, rsocket, exception=None):
        self._registry.remove(self._socket_ref())


async def run_broker(host: str = BROKER_HOST, port: int = BROKER_PORT) -> None:
    registry = Registry()

    def on_connection(reader, writer):
        holder: dict[str, RSocketServer] = {}
        holder["socket"] = RSocketServer(
            TransportTCP(reader, writer),
            handler_factory=lambda: BrokerHandler(registry, lambda: holder["socket"]),
        )

    server = await asyncio.start_server(on_connection, host, port)
    log.info("listening on %s:%s", host, port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)-20s %(message)s")
    asyncio.run(run_broker())
