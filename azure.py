"""
Azure OpenAI support for golem.
"""

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-locals

from util import http_request, fatal, lookup_variable

# See
# https://learn.microsoft.com/en-us/azure/ai-services/openai/reference


# For API_VERSION, see
# https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#api-specs

API_VERSION = "2024-06-01"  # GA


def ask_azure(
    model,
    url,
    api_key,
    messages,
    temperature,
    seed,
    top_p,
    max_tokens,
    logprobs,
    top_logprobs,
):
    """
    Make a request to the Azure OpenAI API.
    """

    if api_key is None:
        api_key = lookup_variable("AZURE_OPENAI_API_KEY")

    if url is None:
        url = lookup_variable("AZURE_OPENAI_ENDPOINT")

    # Model availability depends on what you have deployed via the
    # Azure OpenAI portal. The model name must match your deployment
    # name.

    if model is None:
        model = "gpt-4o-2024-05-13"  # Default

    model = model.replace(".", "")  # N.B. Microsoft uses gpt-35-turbo not gpt-3.5-turbo

    url = f"{url}openai/deployments/{model}/chat/completions?api-version={API_VERSION}"

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    json_data = {"model": model, "messages": messages}

    if temperature is not None:
        json_data["temperature"] = temperature

    if seed is not None:
        json_data["seed"] = seed

    if top_p is not None:
        json_data["top_p"] = top_p

    if max_tokens is not None:
        json_data["max_tokens"] = max_tokens

    if logprobs is not None:
        json_data["logprobs"] = bool(logprobs)

    if top_logprobs is not None:
        json_data["top_logprobs"] = top_logprobs

    request = None
    response = None
    try:
        request, response = http_request(url, headers, json_data)
        response = response.json()
        answer = response["choices"][0]["message"]["content"]
        provider = "azure"
        model = response["model"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
