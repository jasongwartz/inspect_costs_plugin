import logging

from inspect_ai.hooks import Hooks, TaskStart, hooks
from inspect_ai.model import set_model_cost, ModelCost
import httpx
from pydantic import TypeAdapter, ValidationError

logger = logging.getLogger(__name__)

adapter = TypeAdapter(dict[str, ModelCost])


@hooks(
    name="model_cost_hooks", description="Automatically retrieve and set model costs"
)
class ModelCostHooks(Hooks):
    async def on_task_start(self, data: TaskStart) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://llm-prices.llm-prices.workers.dev/api/inspect-costs",
                    params={"model": data.spec.model, "format": "json"},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Failed to fetch model costs (HTTP {e.response.status_code}): {e}"
            )
            return
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch model costs: {e}")
            return

        try:
            prices = adapter.validate_python(response.json())
        except ValidationError as e:
            logger.warning(f"Failed to parse model cost response: {e}")
            return

        for model_name, cost in prices.items():
            set_model_cost(model_name, cost)
