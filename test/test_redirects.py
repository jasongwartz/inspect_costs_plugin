import asyncio
from functools import partial
from unittest.mock import MagicMock, patch

import httpx
import pytest
from inspect_ai.model import ModelCost

from inspect_costs_plugin.inspect_costs_plugin import ModelCostHooks


@pytest.mark.parametrize("status_code", [301, 302, 307, 308])
def test_loads_prices_after_redirect(monkeypatch, status_code):
    monkeypatch.setenv(
        "INSPECT_COSTS_API_URL", "https://old.example.com/api/inspect-costs"
    )
    model = "mockllm/model"
    prices = {
        "input": 1.0,
        "output": 2.0,
        "input_cache_write": 0.5,
        "input_cache_read": 0.1,
    }
    requests = []

    def handle_request(request):
        requests.append(request)
        if request.url.host == "old.example.com":
            return httpx.Response(
                status_code,
                headers={
                    "Location": str(request.url.copy_with(host="new.example.com"))
                },
            )
        return httpx.Response(200, json={model: prices})

    client_factory = partial(
        httpx.AsyncClient, transport=httpx.MockTransport(handle_request)
    )
    hooks = ModelCostHooks()
    task_start = MagicMock()
    task_start.spec.model = model

    with (
        patch(
            "inspect_costs_plugin.inspect_costs_plugin.httpx.AsyncClient",
            side_effect=client_factory,
        ),
        patch(
            "inspect_costs_plugin.inspect_costs_plugin.set_model_cost"
        ) as set_model_cost,
    ):
        asyncio.run(hooks.on_task_start(task_start))

    assert [request.url.host for request in requests] == [
        "old.example.com",
        "new.example.com",
    ]
    assert dict(requests[-1].url.params) == {"model": model, "format": "json"}
    set_model_cost.assert_called_once_with(model, ModelCost(**prices))
    assert model in hooks.models_already_loaded
