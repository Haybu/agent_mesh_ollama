"""Run one agent as its own process:  python run_agent.py finance"""
import asyncio
import logging
import sys

from agents import FinanceAgent, SalesAgent, SupplyChainAgent

AGENTS = {a.name: a for a in (SalesAgent, SupplyChainAgent, FinanceAgent)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)-20s %(message)s")
    asyncio.run(AGENTS[sys.argv[1]]().run())
