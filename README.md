# Inspect Costs Plugin

An [Inspect AI hook](https://inspect.aisi.org.uk/extensions.html#hooks) that automatically retrieves and sets LLM cost data for models used in [Inspect evals](https://inspect.aisi.org.uk/). Pricing data is fetched from https://llm-prices.llm-prices.workers.dev/ by [Matt Fisher](https://github.com/MattFisher/llm-prices).

## Installation

Install the package in your Python virtual environment:

```bash
# with uv
uv add git+https://github.com/jasongwartz/inspect-costs-plugin

# with pip
pip install git+https://github.com/jasongwartz/inspect-costs-plugin
```

That's it — Inspect will auto-detect the plugin and populate cost data for your eval runs. No code changes required.

## Configuration

| Environment variable    | Description                                               | Default                                                       |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------------------------- |
| `INSPECT_COSTS_API_URL` | Override the pricing API endpoint (e.g. for self-hosting) | `https://llm-prices.llm-prices.workers.dev/api/inspect-costs` |

## Limitations

- Only the main task model gets cost data. Other models used during an eval (e.g. scorer models) are not currently covered.

## Credit

Thanks to Matt Fisher for the [llm-prices](https://github.com/MattFisher/llm-prices) server that provides the pricing data.

## License

[MIT](LICENSE)
