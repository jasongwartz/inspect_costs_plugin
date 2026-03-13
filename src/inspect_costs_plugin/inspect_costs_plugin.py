from inspect_ai.hooks import Hooks, TaskStart, hooks

from inspect_ai.model import set_model_cost, ModelCost
import httpx
from pydantic import TypeAdapter

adapter = TypeAdapter(dict[str, ModelCost])


@hooks(
    name="model_cost_hooks", description="Automatically retrieve and set model costs"
)
class ModelCostHooks(Hooks):
    async def on_task_start(self, data: TaskStart) -> None:
        costs = httpx.get(
            "https://llm-prices.llm-prices.workers.dev/api/inspect-costs",
            params={"model": data.spec.model, "format": "json"},
        ).json()
        prices = adapter.validate_python(costs)
        for model_name, cost in prices.items():
            set_model_cost(model_name, cost)
