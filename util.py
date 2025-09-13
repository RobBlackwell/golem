"""
Golem utilities
"""

# pylint: disable=too-many-branches

from datetime import datetime, timezone
from decimal import Decimal
from http import HTTPStatus
import logging
import os
import random
import sys
import time

import requests
from requests.exceptions import RequestException

session = requests.Session()  # Use session for keep-alive and connection pooling

MAX_RETRIES = 20  # Number of HTTP retries before giving up

REDACTED = "REDACTED"  # Replacement text for credentials in output


class UnauthorizedException(Exception):
    """
    Allow an API call to throw an unauthorised exception so that
    it can be caught and re-authorised if possible. E.g. Google.
    """


def ensure_json_serializable(n):
    """
    Unfortunately decimals are not JSON serializable and so we
    have to convert them to floats.
    """
    if isinstance(n, Decimal):
        return float(n)
    return n


def add_system_message(data, text):
    """
    Insert system message text.
    """
    system_message = {"role": "system", "content": text}
    data.insert(0, system_message)
    return data


def decimal_range(start, stop, step):
    """
    Like range but not restricted to integers.
    """
    current = start
    while current < stop:
        yield current
        current += step


def parse_elements(string, sep=","):
    """
    Parse a list consisting of comma separated values.
    """
    elements = string.split(sep)
    converted_elements = []

    for element in elements:
        element = element.strip()  # Remove any surrounding whitespace
        try:
            if "." in element:
                converted_elements.append(Decimal(element))
            else:
                converted_elements.append(int(element))
        except ValueError:
            converted_elements.append(
                element
            )  # If it can't be converted to a number, keep it as a string

    return converted_elements


def parse_range(string):
    """
    Parse colon separated ranges e.g. 1:10 or 1:10:2 where 2 is a step.
    """
    elements = parse_elements(string, ":")
    if len(elements) < 2 or len(elements) > 3:
        fatal(f"{string} is not a valid range start:stop:step")

    start = elements[0]
    stop = elements[1]
    step = 1

    if len(elements) == 3:
        step = elements[2]

    return list(decimal_range(start, stop, step))


def parse_list(string):
    """
    Lists can either be specified as comma separated values or
    colon separated ranges.

    """
    if ":" in string:
        return parse_range(string)
    return parse_elements(string, ",")


def timestamp():
    """
    Return a timestamp, the current date and time in ISO format.
    """
    return datetime.now(timezone.utc).isoformat()


def exponential_backoff(retry_count, initial_delay=5, max_delay=300, factor=2):
    """
    Calculate an exponential back off delay with jitter for
    retries.
    """
    delay = min(initial_delay * (factor**retry_count), max_delay)

    # Add random jitter of up to 10% to avoid synchronized patterns
    jitter_value = random.uniform(0, 0.1 * delay)
    delay += jitter_value

    return delay


def lookup_variable(name):
    """
    We store API credentials as shell variables and use this
    function to lookup a named variable's value.
    """
    v = os.getenv(name)
    if v is None:
        fatal(f"{name} is not set in your shell environment")
        return None
    return v


def fatal(text):
    """
    Fatal error handler. Log the error and bail.
    """
    logging.critical(text)
    sys.exit(1)


def is_rate_limited(response):
    """
    Return True if response implies rate limiting.
    """
    # TOO_MANY_REQUESTS implies that we are being rate
    # limited. Unfortunately, OpenAI use it for insufficient
    # quota.
    return response.status_code == HTTPStatus.TOO_MANY_REQUESTS


def is_server_error(response):
    """
    Return True if response implies a server error
    """
    # INTERNAL_SERVER_ERROR could mean the service is temporarily
    # down, or could be the model randomly barfing as seen when
    # running with high temperature.
    return response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def is_gateway_error(response):
    """
    Return True if response implies bad or overloaded gateway.
    """
    # 502 BAD_GATEWAY.
    # 503 Service Unavailable e.g., seen on Google Vertex
    # 524 e.g.,Cloudflare timeout
    # 529 e.g,Anthropic overloaded
    return response.status_code in (HTTPStatus.BAD_GATEWAY, 503, 524, 529)


def is_continuable_error(response):
    """
    Return True if response indicates an error that is
    continuable, in that the request could be retried.

    """
    return (
        response is None  # e.g., HTTP disconnect
        or is_rate_limited(response)
        or is_server_error(response)
        or is_gateway_error(response)
    )


def reset_session():
    """Reset the global session by closing the existing one and creating a new one."""
    global session
    session.close()
    session = requests.Session()


def http_request(url, headers, json_data, retry=0):
    """
    Make an HTTP request to an LLM API
    """

    logging.debug(
        "http_request: {{url: %s, headers: %s, json: %s, retry: %s}}",
        url,
        headers,
        json_data,
        retry,
    )

    try:
        response = session.post(url, headers=headers, json=json_data, timeout=600)
        logging.debug(
            "http_response: {{status_code: %s, headers: %s, text: %s}}",
            response.status_code,
            response.headers,
            response.text,
        )
        if response.text.strip() == "":
            # Seen with DeepSeek behind Cloudflare
            logging.warning("Empty response.text, ignoring.")
            response = None

    except Exception as e:
        logging.warning("Exception: %s", e)
        response = None

    if response is None:
        reset_session()

    if is_continuable_error(response):

        # Retry ..

        if retry > MAX_RETRIES:
            fatal(f"Too many retries (MAX_RETRIES={MAX_RETRIES})")
        else:
            retry += 1
            d = exponential_backoff(retry)
            if response is None:
                logging.info("Sleeping %s s, before retry %s", int(d), retry)
            else:
                logging.info(
                    "%s:%s Sleeping %s s, before retry %s",
                    response.status_code,
                    response.text,
                    int(d),
                    retry,
                )
            time.sleep(d)
            _, response = http_request(url, headers, json_data, retry)
    elif response.status_code == HTTPStatus.OK:
        pass
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        # This gives the caller an opportunity to trap the error and re-authenticate
        raise UnauthorizedException("HTTP 401")
    else:
        fatal(f"{response.status_code}:{response.text}")

    # Redact credentials in the log
    if "x-api-key" in headers:
        headers["x-api-key"] = REDACTED

    if "Authorization" in headers:
        headers["Authorization"] = REDACTED

    if "api-key" in headers:
        headers["api-key"] = REDACTED

    if "X-goog-api-key" in headers:
        headers["X-goog-api-key"] = REDACTED

    request = {"url": url, "headers": headers, "json": json_data}
    return request, response
