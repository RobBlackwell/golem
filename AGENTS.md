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
