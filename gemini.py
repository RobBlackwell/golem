"""
Google Gemini support for Golem
"""

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-locals, global-statement

from util import http_request, fatal, lookup_variable


def to_parts(content):
    """
    Convert OpenAI style message content into Gemini parts.

    Content is either a plain string, or a list of parts of the kind
    the OpenAI chat completions API takes, which is what prompt files
    are written in. Images arrive as data URLs and Gemini wants them
    as inline data, so they are decoded here rather than re-encoded.
    """

    if isinstance(content, str):
        return [{"text": content}]

    parts = []
    for part in content:
        kind = part.get("type")
        if kind == "text":
            parts.append({"text": part["text"]})
        elif kind == "image_url":
            url = part["image_url"]["url"]
            if not url.startswith("data:"):
                fatal(f"Gemini needs an inline data URL, not {url}")
            header, _, data = url.partition(",")
            mime_type = header[len("data:") :].split(";")[0]
            parts.append({"inline_data": {"mime_type": mime_type, "data": data}})
        else:
            fatal(f"Unsupported content part {kind} for Gemini")

    return parts


def to_text(content):
    """
    Flatten OpenAI style message content down to its text, for the
    system instruction, which takes no images.
    """

    return " ".join(part["text"] for part in to_parts(content) if "text" in part)


def ask_gemini(
    provider,
    model,
    url,
    api_key,
    messages,
    temperature,
    seed,
    top_p,
    max_tokens,
    reasoning_effort,
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
        to_text(entry["content"]) for entry in messages if entry["role"] == "system"
    ]
    system = " ".join(system_contents)

    messages2 = [entry for entry in messages if entry["role"] != "system"]

    # And messages consist of parts, with "model" where Open AI says
    # "assistant"

    messages2 = [
        {
            "role": "model" if entry["role"] == "assistant" else entry["role"],
            "parts": to_parts(entry["content"]),
        }
        for entry in messages2
    ]

    json_data = {}

    if system:
        json_data["systemInstruction"] = {"parts": [{"text": system}]}

    json_data["contents"] = messages2

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

    if reasoning_effort is not None:
        json_data.setdefault("generationConfig", {})
        json_data["generationConfig"]["thinkingConfig"] = {"thinkingLevel": reasoning_effort}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {"X-goog-api-key": f"{api_key}", "Content-Type": "application/json"}

    request = None
    response = None
    try:
        request, response = http_request(url, headers, json_data, timeout=1200)
        response = response.json()
        # Thinking models put their reasoning in parts of their own,
        # marked as thoughts, which are not part of the answer.
        parts = response["candidates"][0]["content"]["parts"]
        answer = "".join(
            part["text"]
            for part in parts
            if "text" in part and not part.get("thought")
        )
        model = response["modelVersion"]
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
