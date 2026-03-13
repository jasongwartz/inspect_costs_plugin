# Inspect Costs Plugin

This package implements [an Inspect AI "hook"](https://inspect.aisi.org.uk/extensions.html#hooks) to auto-gather LLM cost data from https://llm-prices.llm-prices.workers.dev/ for models being used in an [Inspect eval](https://inspect.aisi.org.uk/).

## Usage

Just install the package in your Python virtual environment, for example [with uv](https://docs.astral.sh/uv/concepts/projects/dependencies/#git):

```bash
uv add git+https://github.com/jasongwartz/inspect-costs-plugin
```

Inspect will then auto-detect the package and collect cost data for models you use in evals.

## Roadmap

- Cache cost data for models that have already been loaded
- Load data for other models like scorer models

## Credit

Thanks to Matt Fisher [for the server implementation](https://github.com/MattFisher/llm-prices) that provides the LLM pricing data in an easy-to-consume format.
