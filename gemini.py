"""
Google Gemini support for Golem
"""

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-locals, global-statement

from util import http_request, fatal, lookup_variable


def ask_gemini(
    provider, model, url, api_key, messages, temperature, seed, top_p, max_tokens
):
    """
    Make a request to the Google Gemini API.
    """

    if model is None:
        model = "gemini-2.0-flash"  # Default

    if api_key is None:
        api_key = lookup_variable("GEMINI_API_KEY")

    # System messages are a separate field, unlike Open AI

    system_contents = [
        entry["content"] for entry in messages if entry["role"] == "system"
    ]
    system = " ".join(system_contents)

    messages2 = [entry for entry in messages if entry["role"] != "system"]

    # And messages consist of parts

    messages2 = [
        {"role": entry["role"], "parts": [{"text": entry["content"]}]}
        for entry in messages2
    ]

    json_data = {
        "contents": messages2,
    }

    if system:
        json_data["systemInstruction"] = {"parts": [{"text": system}]}

    if max_tokens is not None:
        json_data.setdefault("generationConfig", {})
        json_data["generationConfig"]["maxOutputTokens"] = max_tokens

    if seed is not None:
        json_data.setdefault("generationConfig", {})
        json_data["generationConfig"]["seed"] = seed

    if top_p is not None:
        json_data.setdefault("generationConfig", {})
        json_data["generationConfig"]["topP"] = top_p

    if temperature is not None:
        json_data.setdefault("generationConfig", {})
        json_data["generationConfig"]["temperature"] = temperature

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {"X-goog-api-key": f"{api_key}", "Content-Type": "application/json"}

    request = None
    response = None
    try:
        request, response = http_request(url, headers, json_data, timeout=1200)
        response = response.json()
        answer = response["candidates"][0]["content"]["parts"][0]["text"]
        model = response["modelVersion"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
