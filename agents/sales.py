"""Sales agent. Task: process a B2B order by collaborating with peers."""
from mesh.agent import BaseAgent


class SalesAgent(BaseAgent):
    name, task = "sales", "process_order"

    async def perform(self, order: dict) -> dict:
        supply = await self.ask("supply_chain", "check_availability",
                                {"sku": order["sku"], "quantity": order["quantity"]})

        expedite_cost = supply["expedite_units"] * supply["expedite_unit_premium"]
        finance = await self.ask("finance", "approve_order",
                                 {**order, "expedite_cost": expedite_cost})

        status = "CONFIRMED" if finance["approved"] else "ESCALATED"
        plan = (f"{supply['available_now']} units now"
                + (f", {supply['expedite_units']} in {supply['expedite_weeks']} weeks"
                   if supply["expedite_units"] else ""))
        decision = {"order_id": order["order_id"], "status": status,
                    "fulfillment": plan, "gross_margin_pct": finance["gross_margin_pct"]}
        decision["rationale"] = await self.reasoner.explain("Sales", self.task, decision)
        self.log.info(decision["rationale"])
        return decision
