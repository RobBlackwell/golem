"""
OpenAI support for golem.
"""

from util import lookup_variable, http_request, fatal

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-positional-arguments, too-many-locals


def ask_openai(
    provider,
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
    reasoning_effort,
):
    """
    Make a request to the OpenAI API.
    """

    # See https://platform.openai.com/docs/api-reference/chat/create

    if model is None:
        model = "gpt-4o"  # Default

    if url is None:
        url = "https://api.openai.com/v1/chat/completions"

    if api_key is None:
        api_key = lookup_variable("OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
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
        json_data["logprobs"] = logprobs

    if top_logprobs is not None:
        json_data["top_logprobs"] = top_logprobs

    if reasoning_effort is not None:
        json_data["reasoning_effort"] = reasoning_effort

    request = None
    response = None
    try:
        request, response = http_request(url, headers, json_data)
        response = response.json()
        answer = response["choices"][0]["message"]["content"]
        model = response["model"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
