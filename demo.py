"""Runs the broker, three agents, and one incoming order in a single process."""
import asyncio
import json
import logging

from agents import FinanceAgent, SalesAgent, SupplyChainAgent
from mesh.broker import run_broker
from mesh.protocol import BROKER_PORT

ORDER = {"order_id": "B2B-1042", "customer": "Peak Outfitters",
         "sku": "TUMBLER-40OZ-SAGE", "quantity": 20_000, "unit_price": 27.50}


async def main() -> None:
    broker = asyncio.create_task(run_broker())
    await asyncio.sleep(0.3)

    agents = [SupplyChainAgent(), FinanceAgent(), SalesAgent()]
    ready = [asyncio.Event() for _ in agents]
    tasks = [asyncio.create_task(a.run(r)) for a, r in zip(agents, ready)]
    await asyncio.gather(*(r.wait() for r in ready))

    # An order arrives (e.g., from the B2B portal) and is routed to Sales.
    sales = agents[-1]
    decision = await sales.perform(ORDER)
    print("\nDECISION\n" + json.dumps(decision, indent=2))

    for agent in agents:
        agent.stop()
    await asyncio.gather(*tasks)
    broker.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)-20s %(message)s")
    logging.getLogger("pyrsocket").setLevel(logging.CRITICAL)
    asyncio.run(main())
