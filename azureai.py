"""
Azure AI support for golem
"""

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-locals

from util import http_request, fatal, lookup_variable


def ask_azureai(
    url, api_key, messages, temperature, seed, top_p, max_tokens, logprobs, top_logprobs
):
    """
    Make a request to the Azure AI Inference API.
    """

    # Use the Azure AI Model Inference API. For
    # Meta-Llama-3-70B-Instruct and other Marketplace models N.B. This
    # is different to the Azure OpenAI API.
    # https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api

    if url is None:
        url = lookup_variable("AZUREAI_ENDPOINT_URL")

    if api_key is None:
        api_key = lookup_variable("AZUREAI_ENDPOINT_KEY")

    url = f"{url}chat/completions"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    json_data = {"messages": messages}

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
        provider = "azureai"
        model = response["model"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
