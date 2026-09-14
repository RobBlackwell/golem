# Golem Agents

Golem supports multiple Large Language Model (LLM) providers through agent modules. Each agent provides a standardized interface to different LLM APIs.

## Supported Providers

### Ollama

**Module:** `ollama.py`

Local inference engine for running LLMs on your machine.

**Configuration:**
- Default URL: `http://localhost:11434`
- Default model: `llama3`
- Environment variable: `--url` to override endpoint

**Example:**
```bash
golem --provider ollama --model mistral "Why is the sky blue?"
```

**Setup:** [Download and run Ollama](https://ollama.com)

---

### OpenAI

**Module:** `openai.py`

Access to OpenAI's GPT models via the OpenAI API.

**Configuration:**
- API Key: Use `--key` or set `OPENAI_API_KEY` environment variable
- Default model: `gpt-3.5-turbo`
- Endpoint: OpenAI's official API

**Example:**
```bash
export OPENAI_API_KEY="your-key-here"
golem --provider openai --model gpt-4 "Why is the sky blue?"
```

**Setup:** [Register with OpenAI](https://platform.openai.com) and create an API key

---

### Anthropic

**Module:** `anthropic.py`

Access to Anthropic's Claude models.

**Configuration:**
- API Key: Use `--key` or set `ANTHROPIC_API_KEY` environment variable
- Default model: `claude-3-sonnet-20240229`
- Endpoint: Anthropic's official API

**Example:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
golem --provider anthropic --model claude-3-opus "Why is the sky blue?"
```

**Setup:** [Register with Anthropic](https://console.anthropic.com) and create an API key

---

### Azure OpenAI

**Module:** `azure.py`

Access to OpenAI models hosted on Microsoft Azure.

**Configuration:**
- Endpoint URL: Use `--url` or set `AZURE_OPENAI_ENDPOINT` environment variable
- API Key: Use `--key` or set `AZURE_OPENAI_API_KEY` environment variable
- Default model: `gpt-35-turbo`

**Example:**
```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-key-here"
golem --provider azure --model gpt-4 "Why is the sky blue?"
```

**Setup:** [Deploy Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource)

---

### Azure AI

**Module:** `azureai.py`

Access to various models hosted on Microsoft Azure AI.

**Configuration:**
- Endpoint URL: Use `--url` or set `AZUREAI_ENDPOINT_URL` environment variable
- API Key: Use `--key` or set `AZUREAI_ENDPOINT_KEY` environment variable

**Example:**
```bash
export AZUREAI_ENDPOINT_URL="your-endpoint-url"
export AZUREAI_ENDPOINT_KEY="your-key-here"
golem --provider azureai "Why is the sky blue?"
```

**Setup:** [Deploy Azure AI model](https://learn.microsoft.com/en-us/azure/ai-services/)

---

### Google Vertex AI

**Module:** `vertex.py`

Access to Google's models including Gemini through Vertex AI.

**Configuration:**
- Requires `gcloud` CLI: [Install gcloud](https://cloud.google.com/sdk/docs/install)
- Environment variables:
  - `CLOUDSDK_COMPUTE_REGION`: Your Google Cloud region (e.g., `europe-west2`)
  - `CLOUDSDK_CORE_PROJECT`: Your Google Cloud project ID
- Default model: `gemini-1.5-pro`

**Example:**
```bash
export CLOUDSDK_COMPUTE_REGION="europe-west2"
export CLOUDSDK_CORE_PROJECT="my-project"
golem --provider vertex --model gemini-1.5-flash "Why is the sky blue?"
```

**Setup:** 
1. [Set up Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
2. [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. [Enable Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)

---

### Google Gemini

**Module:** `gemini.py`

Direct access to Google's Gemini models via Google AI Studio API.

**Configuration:**
- API Key: Use `--key` or set `GOOGLE_API_KEY` environment variable
- Default model: `gemini-1.5-pro`
- Endpoint: Google AI Studio API

**Example:**
```bash
export GOOGLE_API_KEY="your-key-here"
golem --provider gemini --model gemini-1.5-flash "Why is the sky blue?"
```

**Setup:** [Get API key from Google AI Studio](https://aistudio.google.com/app/apikey)

---

### Claude Code

**Module:** `claudecode.py`

Anthropic's coding agent, benchmarked as a whole agent rather than as a
bare model. Unlike every other provider, this one does not call an HTTP
API: it runs the `claude` CLI as a subprocess in non-interactive
(`--print`) mode, so the recorded response includes the agent's tool
calls and multiple turns.

**Configuration:**
- Requires the `claude` CLI on `PATH`, see [Claude Code](https://claude.com/claude-code)
- Authentication is whatever the CLI already uses; `--key` and `--url`
  are passed to it as `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`
- Default model: whatever the CLI is configured to use, `--model`
  accepts an alias (`opus`, `sonnet`, `haiku`) or a full model name

| Variable | Default | Meaning |
|---|---|---|
| `CLAUDE_CODE_PATH` | `claude` | Path to the CLI binary |
| `CLAUDE_CODE_TOOLS` | `Bash,WebFetch,WebSearch` | Built in tools offered to the agent, `""` for none, `default` for all |
| `CLAUDE_CODE_PERMISSION_MODE` | `bypassPermissions` | Permission mode, unattended runs need permission prompts off |
| `CLAUDE_CODE_TIMEOUT` | `3600` | Seconds before the subprocess is killed |
| `CLAUDE_CODE_SYSTEM_PROMPT_MODE` | append | Set to `replace` to replace the agent's system prompt rather than append to it |
| `CLAUDE_CODE_ARGS` | unset | Extra CLI flags, appended last |

**Example:**
```bash
golem --provider claude-code --model haiku "What is 7 + 2? Only give the final answer"
```

**Mapped arguments:** `--reasoning_effort` becomes `--effort`,
`--response-format` becomes `--json-schema`. `--temperature`,
`--top_p`, `--seed`, `--max_tokens`, `--n` and `--logprobs` have no CLI
equivalent and are ignored with a warning.

**No ambient CLAUDE.md:** golem always passes `--setting-sources=`,
which loads no settings sources, so the agent never sees a `CLAUDE.md`
from the working directory, from any parent of it, or from the user's
`~/.claude`. Left alone, the CLI reads all of those, which silently
contaminates results and makes them irreproducible on another machine.
This is deliberately not configurable, and `make claudecode-isolation`
guards it. Note that loading no settings sources also means no
settings file MCP servers, skills, hooks or custom agents. Anything
passed in `CLAUDE_CODE_ARGS` is appended after this flag and can
therefore override it, so don't put `--setting-sources` there unless
you mean to give up the guarantee.

**Caveats:**
- `bypassPermissions` lets the agent run tools, including `Bash`, with
  no prompting, against the directory golem was started in. Run
  benchmarks somewhere you don't mind being written to.
- Don't reach for `--bare` for isolation. It restricts authentication
  to `ANTHROPIC_API_KEY`, and never reads OAuth credentials or the
  keychain, so a CLI that is logged in interactively will fail with
  "Not logged in".
- Failures are not retried, because an agent run has side effects and
  replaying a half finished one is not safe. Restart with `--skip`.
- A multi turn `messages` list is flattened into a single labelled
  prompt, since the CLI takes one prompt on stdin.

---

## Adding New Agents

To add a new LLM provider agent:

1. Create a new module file (e.g., `newprovider.py`)
2. Implement an `ask_newprovider()` function that:
   - Takes standardized parameters (prompt, model, temperature, etc.)
   - Returns a dictionary with standardized response format including:
     - `response`: The raw API response
     - `answer`: The text answer extracted from the response
     - Other model-specific metadata
3. Import the function in `golem.py`
4. Add provider case handling in `golem.py`'s main function
5. Document the new provider in this file

---

## Common Parameters

All agents support the following standardized parameters:

- `--model`: Specify the model to use (defaults vary by provider)
- `--temperature`: Control randomness (0.0-2.0, default varies)
- `--top_p`: Nucleus sampling parameter (0.0-1.0)
- `--max_tokens`: Maximum tokens in response
- `--system-prompt`: System message to guide behavior
- `--seed`: Random seed for reproducibility (where supported)

Refer to `golem -h` for the complete list of options.
