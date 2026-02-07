"""
Ollama support
"""

# pylint: disable=too-many-arguments, broad-exception-caught

import json
from util import fatal, http_request

# Ollama support requires a running Ollama server on port 11434, See
# https://github.com/ollama/ollama/blob/main/README.md


def ask_ollama(
    model, url, messages, temperature, seed, top_p, max_tokens, response_format
):
    """
    Make a request to a locally running Ollama server.
    """

    if model is None:
        model = "llama3"  # Default

    if url is None:
        url = "http://localhost:11434/api/chat"

    json_data = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {},
    }

    if temperature is not None:
        json_data["options"]["temperature"] = temperature

    if seed is not None:
        json_data["options"]["seed"] = seed

    if top_p is not None:
        json_data["options"]["top_p"] = top_p

    if response_format is not None:
        json_data["format"] = json.loads(response_format)

    # max_tokens is num_predict in Ollama
    if max_tokens is not None:
        json_data["options"]["num_predict"] = max_tokens

    request = None
    response = None
    try:
        request, response = http_request(url, {}, json_data)
        response = response.json()
        answer = response["message"]["content"]
        provider = "ollama"
        model = response["model"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
