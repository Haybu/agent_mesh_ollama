"""Finance agent. Task: approve an order against a margin policy."""
from mesh.agent import BaseAgent

UNIT_COST = {"TUMBLER-40OZ-SAGE": 17.00}   # illustrative
MIN_MARGIN = 0.30                           # policy: 30% gross margin floor


class FinanceAgent(BaseAgent):
    name, task = "finance", "approve_order"

    async def perform(self, request: dict) -> dict:
        qty, price = request["quantity"], request["unit_price"]
        cost = UNIT_COST[request["sku"]] * qty + request.get("expedite_cost", 0.0)
        revenue = price * qty
        margin = (revenue - cost) / revenue
        result = {
            "approved": margin >= MIN_MARGIN,
            "gross_margin_pct": round(margin * 100, 1),
            "gross_profit": round(revenue - cost, 2),
            "policy_floor_pct": MIN_MARGIN * 100,
        }
        result["rationale"] = await self.reasoner.explain("Finance", self.task, result)
        self.log.info(result["rationale"])
        return result
