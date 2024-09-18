"""
Google Vertex support for Golem
"""

# pylint: disable=broad-exception-caught, too-many-arguments, too-many-locals, global-statement

import subprocess

from util import http_request, fatal, lookup_variable, UnauthorizedException

API_KEY_CACHE = None  # API key cache


def get_google_token():
    """
    Use Google Cloud to get an access token.
    """
    command = ["gcloud", "auth", "print-access-token"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        token = result.stdout.strip()  # Removes any trailing newline
        return token
    except subprocess.CalledProcessError as e:
        fatal(f"Can't get Google token: {e}")
        return None


def ask_google(model, messages, temperature, seed, top_p, max_tokens):
    """
    Make a request to the Google Vertex API.
    """
    # We use the  Google Vertex API, see
    # https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal#set-up-your-environment
    #
    # gcloud auth application-default login
    #
    # https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.publishers.models/generateContent
    #
    # https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference
    #
    # https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations#europe
    #
    # https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
    #
    # Example models:
    # gemini-1.5-pro-001
    #

    location = lookup_variable(
        "CLOUDSDK_COMPUTE_REGION"
    )  # e.g. "europe-west2" is London
    project_id = lookup_variable("CLOUDSDK_CORE_PROJECT")

    if model is None:
        model = "gemini-1.5-flash-001"  # Default

    global API_KEY_CACHE
    if API_KEY_CACHE is None:
        API_KEY_CACHE = get_google_token()

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
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {},
    }

    if max_tokens is not None:
        json_data["generationConfig"]["maxOutputTokens"] = max_tokens

    if seed is not None:
        json_data["generationConfig"]["seed"] = seed

    if top_p is not None:
        json_data["generationConfig"]["topP"] = top_p

    if temperature is not None:
        json_data["generationConfig"]["temperature"] = temperature

    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/"
        f"{project_id}/locations/{location}/publishers/google/models/"
        f"{model}:generateContent"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY_CACHE}",
        "Content-Type": "application/json",
    }

    try:
        try:
            request, response = http_request(url, headers, json_data)
        except UnauthorizedException:
            # Re-authenticate and try again
            API_KEY_CACHE = get_google_token()
            headers["Authorization"] = f"Bearer {API_KEY_CACHE}"
            request, response = http_request(url, headers, json_data)

        response = response.json()
        answer = response["candidates"][0]["content"]["parts"][0]["text"]
        provider = "google"
        # The Google Vertex API does not respond with the model name, so
        # we just have to trust that it used the model that we asked for.
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request} RESPONSE: {response}")

    return request, response, answer, provider, model
