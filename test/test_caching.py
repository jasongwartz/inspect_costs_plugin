import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from inspect_ai.model._model_info import _custom_models, ModelInfo

from inspect_costs_plugin.inspect_costs_plugin import ModelCostHooks


def _make_success_response(json_data):
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    return response


def _make_mock_client(response):
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _make_task_start(model_name: str):
    data = MagicMock()
    data.spec.model = model_name
    return data


def test_caching_skips_duplicate_fetches():
    """Second call for the same model should not make another HTTP request."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    response = _make_success_response({
        "mockllm/model": {
            "input": 1.0,
            "output": 2.0,
            "input_cache_write": 0.5,
            "input_cache_read": 0.1,
        }
    })
    mock_client = _make_mock_client(response)

    hooks = ModelCostHooks()
    task_start = _make_task_start("mockllm/model")

    with patch(
        "inspect_costs_plugin.inspect_costs_plugin.httpx.AsyncClient",
        return_value=mock_client,
    ):
        asyncio.run(hooks.on_task_start(task_start))
        asyncio.run(hooks.on_task_start(task_start))

    assert mock_client.get.await_count == 1


def test_caching_fetches_different_models_separately():
    """Different models should each trigger their own HTTP request."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")
    _custom_models["mockllm/other"] = ModelInfo(organization="Mock", model="other")

    response = _make_success_response({
        "mockllm/model": {
            "input": 1.0,
            "output": 2.0,
            "input_cache_write": 0.5,
            "input_cache_read": 0.1,
        }
    })
    mock_client = _make_mock_client(response)

    hooks = ModelCostHooks()

    with patch(
        "inspect_costs_plugin.inspect_costs_plugin.httpx.AsyncClient",
        return_value=mock_client,
    ):
        asyncio.run(hooks.on_task_start(_make_task_start("mockllm/model")))
        asyncio.run(hooks.on_task_start(_make_task_start("mockllm/other")))

    assert mock_client.get.await_count == 2
