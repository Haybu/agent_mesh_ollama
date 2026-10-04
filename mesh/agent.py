"""BaseAgent: connects to the broker, serves ONE task, and can ask other agents."""
import asyncio
import json
import logging
from abc import ABC, abstractmethod

from rsocket.helpers import create_future, single_transport_provider
from rsocket.payload import Payload
from rsocket.routing.request_router import RequestRouter
from rsocket.routing.routing_request_handler import RoutingRequestHandler
from rsocket.rsocket_client import RSocketClient
from rsocket.transports.tcp import TransportTCP

from mesh.protocol import (BROKER_HOST, BROKER_PORT, METADATA_ENCODING,
                           decode, encode, make_route, setup_payload)
from mesh.reasoner import Reasoner, default_reasoner


class BaseAgent(ABC):
    name: str   # role, e.g. "finance"
    task: str   # the one task it performs, e.g. "approve_order"

    def __init__(self, reasoner: Reasoner | None = None):
        self.reasoner = reasoner or default_reasoner()
        self.log = logging.getLogger(f"agent.{self.name}")
        self._client: RSocketClient | None = None
        self._stop = asyncio.Event()

    @property
    def route(self) -> str:
        return make_route(self.name, self.task)

    @abstractmethod
    async def perform(self, request: dict) -> dict:
        """The agent's single responsibility."""

    async def ask(self, agent: str, task: str, body: dict) -> dict:
        """Request work from another agent through the broker."""
        self.log.info("-> %s.%s", agent, task)
        response = await self._client.request_response(encode(make_route(agent, task), body))
        return decode(response)

    def _router(self) -> RequestRouter:
        router = RequestRouter()

        @router.response(self.route)
        async def handle(payload: Payload):
            result = await self.perform(decode(payload))
            return create_future(Payload(json.dumps(result).encode()))

        return router

    async def run(self, ready: asyncio.Event | None = None,
                  host: str = BROKER_HOST, port: int = BROKER_PORT) -> None:
        reader, writer = await asyncio.open_connection(host, port)
        async with RSocketClient(
            single_transport_provider(TransportTCP(reader, writer)),
            handler_factory=lambda: RoutingRequestHandler(self._router()),
            metadata_encoding=METADATA_ENCODING,
            setup_payload=setup_payload(self.name),
        ) as client:
            self._client = client
            self.log.info("online, serving '%s'", self.route)
            if ready:
                ready.set()
            await self._stop.wait()  # serve until stopped

    def stop(self) -> None:
        self._stop.set()
