from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from inspect_ai import Task, eval, task
from inspect_ai.dataset import Sample
from inspect_ai.model._model_info import _custom_models, ModelInfo
from inspect_ai.scorer import exact
from inspect_ai.solver import generate


@task
def hello_world():
    return Task(
        dataset=[
            Sample(
                input="Just reply with Hello World",
                target="Hello World",
            )
        ],
        solver=[generate()],
        scorer=exact(),
    )


def _make_mock_client(response):
    """Create a mock AsyncClient that returns the given response from get()."""
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _make_success_response(json_data):
    """Create a mock response with a 200 status and given JSON body."""
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    return response


def _run_eval_with_mock_client(mock_client):
    with patch(
        "inspect_costs_plugin.inspect_costs_plugin.httpx.AsyncClient",
        return_value=mock_client,
    ):
        return eval(
            hello_world(), model="mockllm/model", log_dir="/tmp/inspect-costs-test"
        )


def test_eval_has_cost_data():
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    response = _make_success_response(
        {
            "mockllm/model": {
                "input": 1.0,
                "output": 2.0,
                "input_cache_write": 0.5,
                "input_cache_read": 0.1,
            }
        }
    )
    mock_client = _make_mock_client(response)
    logs = _run_eval_with_mock_client(mock_client)

    assert len(logs) == 1
    log = logs[0]
    assert log.status == "success"

    assert log.stats.model_usage
    for _, usage in log.stats.model_usage.items():
        assert usage.total_cost is not None
        assert usage.total_cost > 0

    assert log.samples
    for sample in log.samples:
        assert sample.model_usage
        for _, usage in sample.model_usage.items():
            assert usage.total_cost is not None
            assert usage.total_cost > 0


def test_eval_succeeds_on_http_error():
    """Eval should still succeed when the cost API returns an HTTP error."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    response = MagicMock()
    response.status_code = 500
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Internal Server Error",
        request=MagicMock(),
        response=response,
    )
    mock_client = _make_mock_client(response)
    logs = _run_eval_with_mock_client(mock_client)

    assert len(logs) == 1
    assert logs[0].status == "success"
    # Costs should be None since the API call failed
    for _, usage in logs[0].stats.model_usage.items():
        assert usage.total_cost is None


def test_eval_succeeds_on_connection_error():
    """Eval should still succeed when the cost API is unreachable."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    logs = _run_eval_with_mock_client(mock_client)

    assert len(logs) == 1
    assert logs[0].status == "success"
    for _, usage in logs[0].stats.model_usage.items():
        assert usage.total_cost is None


def test_eval_succeeds_on_invalid_json_response():
    """Eval should still succeed when the cost API returns unparseable data."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    response = _make_success_response({"mockllm/model": "not a valid cost object"})
    mock_client = _make_mock_client(response)
    logs = _run_eval_with_mock_client(mock_client)

    assert len(logs) == 1
    assert logs[0].status == "success"
    for _, usage in logs[0].stats.model_usage.items():
        assert usage.total_cost is None


def test_eval_succeeds_on_timeout():
    """Eval should still succeed when the cost API times out."""
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ReadTimeout("Read timed out")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    logs = _run_eval_with_mock_client(mock_client)

    assert len(logs) == 1
    assert logs[0].status == "success"
    for _, usage in logs[0].stats.model_usage.items():
        assert usage.total_cost is None
