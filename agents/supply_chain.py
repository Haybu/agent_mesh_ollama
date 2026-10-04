"""Supply Chain agent. Task: check product availability."""
from mesh.agent import BaseAgent

INVENTORY = {"TUMBLER-40OZ-SAGE": 12_000}   # units on hand (illustrative)
EXPEDITE = {"lead_time_weeks": 4, "unit_premium": 2.10}


class SupplyChainAgent(BaseAgent):
    name, task = "supply_chain", "check_availability"

    async def perform(self, request: dict) -> dict:
        sku, qty = request["sku"], request["quantity"]
        on_hand = INVENTORY.get(sku, 0)
        shortfall = max(qty - on_hand, 0)
        result = {
            "sku": sku,
            "available_now": min(qty, on_hand),
            "expedite_units": shortfall,
            "expedite_weeks": EXPEDITE["lead_time_weeks"] if shortfall else 0,
            "expedite_unit_premium": EXPEDITE["unit_premium"] if shortfall else 0.0,
        }
        result["rationale"] = await self.reasoner.explain("Supply chain", self.task, result)
        self.log.info(result["rationale"])
        return result
