# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install (editable):**
```bash
uv pip install -e .     # preferred, see README
pip install -e .        # equivalent
```
Note: `make install` runs `bin/install.sh`, which references a `requirements.txt` that no longer exists — that step errors (the script has no `set -e`, so `pip install .` still runs). Prefer installing directly.

**Lint:**
```bash
make pylint
# equivalent to:
pylint -d duplicate-code $(git ls-files '*.py')
```

**Tests** — every target makes live API calls to real providers, so they cost money and need credentials for *all* providers to be exported (see `tokens.sh`). Run one target rather than the whole suite while iterating:
```bash
make math          # each provider answers a trivial sum correctly
make models        # returned .model matches the requested deployment
make logprobs
make temperature   # sweep parsing: single value, list, range
make top_p         # not included in `make test`
make repeat
make system        # batch mode + --skip + --system-prompt, asserts line count
make claudecode    # answer, resolved model, and that the agent actually used Bash
make claudecode-isolation   # ambient CLAUDE.md does not reach the agent

make test          # math models logprobs temperature repeat system claudecode claudecode-isolation
```
Tests are shell one-liners in the `Makefile` that pipe golem's JSONL through `jq` and `grep -q`. They pin specific model names and Azure deployment endpoints (`AZURE_OPENAI_ENDPOINT_1..3`), so they go stale as models are retired.

**Run without installing:**
```bash
./golem.py --provider ollama "Why is the sky blue?"
```

## Architecture

Golem is a CLI for batch LLM benchmarking. It sends prompts to many providers and logs every request/response as JSONL for full traceability.

### Core flow

`golem.py` is entry point and orchestrator:
1. `make_parser()` parses CLI args.
2. `--temperature`, `--top_p` and `--repeat` each accept a single value, a comma-separated list, or a `start:stop:step` range; `util.parse_list` expands them (numbers become `int`/`Decimal`, anything else stays a string).
3. `main()` loops repeat × top_p × temperature, in either *immediate mode* (positional `prompt` arg) or *batch mode* (`-f prompts.jsonl`, one `{"id", "messages"}` record per line).
4. `run()` calls `ask()`, which dispatches on `args.provider`, and prints one JSON object per request to stdout.

### Provider modules

Each module exports `ask_<provider>()` which builds the HTTP request, calls `util.http_request()`, and returns the 5-tuple `(request, response, answer, provider, model)`. `answer` is a normalized plain-text extraction so downstream consumers never need provider-specific parsing; `model` is read back from the *response* where possible, so it reflects what actually served the request.

Provider names do not map 1:1 onto module names:

| `--provider` | module | function |
|---|---|---|
| `openai` | `openai.py` | `ask_openai` |
| `anthropic` | `anthropic.py` | `ask_anthropic` |
| `azure` | `azure.py` | `ask_azure` |
| `azureai` | `azureai.py` | `ask_azureai` |
| `gemini` (AI Studio) | `gemini.py` | `ask_gemini` |
| `google` (Vertex AI) | `vertex.py` | `ask_google` |
| `ollama` | `ollama.py` | `ask_ollama` |
| `claude-code` / `claudecode` | `claudecode.py` | `ask_claudecode` |
| `deepseek`, `xai`, `openrouter`, `vllm` | `openai.py` | `ask_openai` with a different default model/URL/key |

`claude-code` is the one provider that is not an HTTP call: it runs the `claude` CLI as a subprocess with `--print --output-format stream-json`, so it benchmarks the agent rather than a bare model. `response` is the CLI's final `result` event, with the whole event stream (tool calls included) kept under `response.events`; `request` records the argv, cwd and stdin instead of a URL and headers. Credentials go into the subprocess environment, never onto the command line, since the command line is logged. It does not retry, because agent runs have side effects. See `AGENTS.md` for its environment variables.

It always passes `--setting-sources=` so that no ambient `CLAUDE.md` (cwd, any parent directory, or `~/.claude`) reaches the agent — that would contaminate results and make them irreproducible elsewhere. Treat this as load-bearing, not incidental: `make claudecode-isolation` fails if it regresses. Do not "fix" isolation with `--bare`, which restricts auth to `ANTHROPIC_API_KEY` and breaks an interactively logged-in CLI.

Arguments are passed **positionally** into `ask_<provider>()`, so adding a parameter means updating the call site in `ask()` and every module that receives it (see the recent `reasoning_effort` addition to `ask_gemini`). Parameters a provider cannot support are dropped in `ask()` with a `logging.warning("Ignoring ...")` rather than an error.

### Error handling

`util.fatal()` logs, appends to `error.log`, and calls `sys.exit(1)` — provider modules wrap their parsing in a broad `except` and call `fatal()` with the request and response attached. There is no partial-failure recovery inside a run; recovery is by restarting with `--skip N`.

`util.http_request()` retries up to `MAX_RETRIES` (20) with exponential backoff plus jitter on 429, 500, 502, 503, 524, 529, connection exceptions, and empty response bodies (seen from DeepSeek behind Cloudflare); it resets the shared `requests.Session` on a dead connection. HTTP 401 raises `UnauthorizedException` instead, so callers can re-authenticate (Vertex refreshes its `gcloud` token this way).

### Output format

```json
{"id": ..., "provider": ..., "model": ..., "timestamp": ..., "request": {...}, "response": {...}, "answer": "...", "repeat": ..., "temperature": ..., "top_p": ...}
```
`repeat`/`temperature`/`top_p` are only present when set. Credential headers (`Authorization`, `api-key`, `x-api-key`, `X-goog-api-key`) are replaced with `"REDACTED"` in `request.headers` before output, which is what makes answer files safe to publish.

### Experiment layout

The analysis scripts infer metadata from the *directory path*, so results are expected to live at `<experiment>/<label>/answers.jsonl` — `costs.py` and `traces.py` both emit `"label": parent.name` and `"experiment": parent.parent.name`. See `example/standard/gpt-35-turbo-0125/` for the pattern: one directory per model, each with a small `Makefile` that runs golem into a timestamped temp file and only `mv`s it into place on success.

The example pipeline is `questions.jsonl` → `jsont.py` (f-string templating over JSONL) → `prompts.jsonl` → golem → `answers.jsonl` → `summarise.py` → `summary.psv`.

### Analysis scripts

All take one or more `answers.jsonl` paths as argv and emit JSONL on stdout:

- `costs.py` — sums token usage (handling OpenAI, Anthropic and Gemini `usage`/`usageMetadata` shapes) and prices it from `etc/models.yaml`. Lookup is by the model string in the record against a model entry's `keys:` list, so a new model needs an entry there or costs come out as 0 with a warning. If a record carries `response.total_cost_usd` (Claude Code reports its own), that is used in preference, because the token-count model ignores cache reads and writes, which dominate the bill for agent runs — in that case `input_cost`/`output_cost` stay 0 and only `total_cost` is meaningful.
- `latencies.py` — median/quartiles/IQR of *inter-record* timestamp deltas per model. This measures wall-clock spacing of a sequential batch run, not true request latency.
- `traces.py` — extracts reasoning traces, probing `message.reasoning`, `message.reasoning_content`, and `message.reasoning_details[]` in turn.

### Adding a new provider

1. Create `<provider>.py` with `ask_<provider>(...)` returning `(request, response, answer, provider, model)`, using `util.http_request()` and `util.lookup_variable()` for credentials.
2. Import and dispatch it in `golem.py`'s `ask()`. If the API is OpenAI-compatible, just set defaults and call `ask_openai()`.
3. Add the module to `py-modules` in `pyproject.toml`, or it won't be installed.
4. Add test cases to the `Makefile`.
5. Document it in `AGENTS.md` and the README's Configuration section.

## Key details

- Uses `requests` directly, never provider SDKs — all traffic goes through `util.http_request()`.
- Credentials come from environment variables looked up by `util.lookup_variable()`; `tokens.sh` (gitignored) is where they're kept locally, sourced before use.
- `--skip N` restarts a batch after a crash by skipping the first N lines of the input JSONL; it applies only to the first repeat iteration.
- `--delay` throttles batch mode between requests.
- `Decimal` values from range parsing are converted to `float` by `util.ensure_json_serializable()` before output.
- Python files carry an Emacs `Time-stamp:` header in the first two lines; leave it alone unless updating it deliberately.
