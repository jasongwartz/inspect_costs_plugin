from unittest.mock import AsyncMock, MagicMock, patch

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


def test_eval_has_cost_data():
    # Register mockllm/model in the model info database so set_model_cost can find it
    _custom_models["mockllm/model"] = ModelInfo(organization="Mock", model="model")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "mockllm/model": {
            "input": 1.0,
            "output": 2.0,
            "input_cache_write": 0.5,
            "input_cache_read": 0.1,
        }
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "inspect_costs_plugin.inspect_costs_plugin.httpx.AsyncClient",
        return_value=mock_client,
    ):
        logs = eval(
            hello_world(), model="mockllm/model", log_dir="/tmp/inspect-costs-test"
        )

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
