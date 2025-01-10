"""
Anthropic support for golem
"""

from util import http_request, fatal, lookup_variable

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-positional-arguments


def ask_anthropic(model, url, api_key, messages, temperature, top_p, max_tokens):
    """
    Make a request to the Anthropic API.
    """

    # See https://docs.anthropic.com/en/api/messages
    # No support for seed or logprobs as at July 204.

    if model is None:
        model = "claude-3-5-sonnet-20240620"

    if url is None:
        url = "https://api.anthropic.com/v1/messages"

    if api_key is None:
        api_key = lookup_variable("ANTHROPIC_API_KEY")

    # The Messages API accepts a top-level `system` parameter, not
    # "system" as an input message role.  This is different from
    # OpenAI API messages, so we fix that up here:

    system = " ".join(
        [entry["content"] for entry in messages if entry["role"] == "system"]
    )

    messages = [entry for entry in messages if entry["role"] != "system"]

    json_data = {"model": model, "messages": messages, "system": system}

    # Temperature 0.0 to 1.0 only.

    if temperature is not None:
        json_data["temperature"] = temperature

    if top_p is not None:
        json_data["top_p"] = top_p

    if max_tokens is not None:
        json_data["max_tokens"] = max_tokens

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    request = None
    response = None
    try:
        request, response = http_request(url, headers, json_data)
        response = response.json()
        answer = response["content"][0]["text"]
        provider = "anthropic"
        model = response["model"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
