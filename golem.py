#!/usr/bin/env python3
# Time-stamp: <2025-01-10 13:46:35 rblackwell>

"""Golem

Copyright (C) 2024 Robert E. Blackwell <rblackwell@turing.ac.uk>.

Use Large Language Model APIs from the command line.

https://github.com/RobBlackwell/golem

This program comes with ABSOLUTELY NO WARRANTY; for details see
LICENSE. This is free software, and you are welcome to redistribute it
under certain conditions; see LICENSE for details.

Examples
./golem.py --provider ollama --model mistral "Why is the sky blue?"
./golem.py --provider ollama --model mistral -f prompts.jsonl

"""

# pylint: disable=too-many-arguments, broad-exception-caught, too-many-locals, too-many-branches, too-many-return-statements, global-statement, too-many-statements, too-many-positional-arguments


import argparse
import json
import logging
import time

from util import (
    timestamp,
    fatal,
    ensure_json_serializable,
    parse_list,
    add_system_message,
)

from ollama import ask_ollama
from openai import ask_openai
from azure import ask_azure
from azureai import ask_azureai
from vertex import ask_google
from anthropic import ask_anthropic

__version__ = "0.0.1"

DESCRIPTION = (
    "Golem Copyright (C) 2024 Robert E. Blackwell.\n\n"
    "Use Large Language Model APIs from the command line.\n\n"
    "https://github.com/RobBlackwell/golem\n\n"
    "This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.\n"
    "This is free software, and you are welcome to redistribute it "
    "under certain conditions; see LICENSE for details.\n"
)

EXAMPLES = (
    "examples:\n\n"
    'golem --provider ollama --model mistral "Why is the sky blue?"\n'
    'golem --provider openai --model gpt-4o "Tell me a rhyming poem about a tortoise '
    'and a friendly dinosaur" | jq -r  .answer\n'
)


def ask(
    args,
    messages,
    temperature,
    top_p,
):
    """
    Direct a request to an LLM API.
    """

    provider = args.provider.lower()
    model = args.model
    max_tokens = args.max_tokens
    logprobs = args.logprobs
    top_logprobs = args.top_logprobs
    seed = args.seed
    url = args.url
    key = args.key

    if provider == "azure":
        return ask_azure(
            model,
            url,
            key,
            messages,
            temperature,
            seed,
            top_p,
            max_tokens,
            logprobs,
            top_logprobs,
        )

    if provider == "azureai":
        if model is not None:
            logging.warning("Ignoring model")
        return ask_azureai(
            url,
            key,
            messages,
            temperature,
            seed,
            top_p,
            max_tokens,
            logprobs,
            top_logprobs,
        )

    if provider == "openai":
        return ask_openai(
            model,
            url,
            key,
            messages,
            temperature,
            seed,
            top_p,
            max_tokens,
            logprobs,
            top_logprobs,
        )

    if top_logprobs is not None:
        logging.warning("Ignoring top_logprobs")

    if logprobs is not None:
        logging.warning("Ignoring logprobs")

    if provider == "anthropic":
        if seed is not None:
            logging.warning("Ignoring seed")
        return ask_anthropic(model, url, key, messages, temperature, top_p, max_tokens)

    if provider == "ollama":
        if key is not None:
            logging.warning("Ignoring key")
        return ask_ollama(model, url, messages, temperature, seed, top_p, max_tokens)

    if url is not None:
        logging.warning("Ignoring url %s", url)

    if key is not None:
        logging.warning("Ignoring key")

    if provider == "google":
        return ask_google(model, messages, temperature, seed, top_p, max_tokens)

    fatal(f"Unknown API provider {provider}.")
    return None


def run(identifier, args, repeat, temperature, top_p, messages):
    """
    Make an LLM request and display results.
    """

    # Any of these numeric variables could be a Decimal
    temperature = ensure_json_serializable(temperature)
    top_p = ensure_json_serializable(top_p)
    repeat = ensure_json_serializable(repeat)

    request, response, answer, provider, model = ask(args, messages, temperature, top_p)
    result = {
        "id": identifier,
        "provider": provider,
        "model": model,
        "timestamp": timestamp(),
        "request": request,
        "response": response,
        "answer": answer,
    }
    if repeat is not None:
        result["repeat"] = repeat
    if temperature is not None:
        result["temperature"] = temperature
    if top_p is not None:
        result["top_p"] = top_p

    print(json.dumps(result))


def make_parser():
    """
    Construct and configure the golem command line argument parser.
    """

    parser = argparse.ArgumentParser(
        prog="golem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        epilog=EXAMPLES,
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed  DEBUG info."
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="Ollama",
        help=(
            "API provider, e.g., OpenAI, Google, Anthropic, Azure, "
            "AzureAI or Ollama. Default Ollama."
        ),
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            'Name of the model to use (e.g. "gpt-4o", optional). If not specified, '
            "models may use a sensible default."
        ),
    )

    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help=(
            "URL of the API endpoint (optional). If not specified, models will "
            "check appropriate shell variables."
        ),
    )

    parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="API Key (optional). If not specified, models will check appropriate shell variables.",
    )

    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Skip n records in the JSONL. Useful for restarting after a crash.",
    )

    parser.add_argument(
        "--repeat",
        type=str,
        default=None,
        help=(
            "Repeat the run multiple times. "
            'Can be a label (e.g. 0), a list of labels (e.g., "0,1,2,3") or a range (e.g. "0:10").'
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay in seconds between requests (e.g. 0.2).",
    )

    parser.add_argument(
        "-t",
        "--temperature",
        type=str,
        default=None,
        help=(
            "Temperature is used to control the randomness of the output and "
            'can be a single value (e.g. "0.0"), a list (.e.g., "0.0,1.0") '
            'or a range (e.g. "0.0:1.1:0.1").'
        ),
    )
    parser.add_argument(
        "--top_p",
        type=str,
        default=None,
        help=(
            "Use top_p (nucleus sampling) 0 < top_p <= 1.0. Can be a single value (.e.g. 0.1), "
            'a list e.g., "0.1,0.9" or a range (e.g, "0.1:1.0:0.2").'
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Setting the random seed makes some models more deterministic.",
    )

    parser.add_argument(
        "--max_tokens", type=int, default=None, help="Maximum number of tokens."
    )

    parser.add_argument(
        "--logprobs",
        default=None,
        help="Whether to return log probabilities of the output tokens or not.",
    )

    parser.add_argument(
        "--top_logprobs",
        type=int,
        default=None,
        help="The number of most likely tokens to return at each token position.",
    )

    parser.add_argument(
        "--system-prompt",
        type=str,
        default=None,
        help="Path to text file containing system prompt text.",
    )

    parser.add_argument(
        "-f", "--messages", help="Path to a JSONL file containing messages."
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help='A simple user prompt, e.g. "Why is the sky blue?" (optional)',
    )

    return parser


def main():
    """
    Entry point.
    """

    args = make_parser().parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logging.info(DESCRIPTION)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    if args.temperature is None:
        args.temperature = [None]
    else:
        args.temperature = parse_list(args.temperature)

    if args.repeat is None:
        args.repeat = [0]
    else:
        args.repeat = parse_list(args.repeat)

    if args.top_p is None:
        args.top_p = [None]
    else:
        args.top_p = parse_list(args.top_p)

    if args.system_prompt:
        with open(args.system_prompt, "r", encoding="utf-8") as file:
            args.system_prompt = file.read()

    for repeat in args.repeat:

        logging.debug(
            "repeat: %s (type: %s)",
            repeat,
            type(repeat).__name__,
        )

        for top_p in args.top_p:

            logging.debug(
                "top_p: %s (type: %s)",
                top_p,
                type(top_p).__name__,
            )

            for temperature in args.temperature:

                logging.debug(
                    "temperature: %s (type: %s)",
                    temperature,
                    type(temperature).__name__,
                )

                if args.prompt:
                    # Immediate mode, useful for testing
                    messages = [{"role": "user", "content": args.prompt}]
                    if args.system_prompt:
                        messages = add_system_message(messages, args.system_prompt)
                    run(1, args, repeat, temperature, top_p, messages)
                else:
                    # Batch mode for bulk requests
                    if args.messages:
                        logging.debug("messages: %s", args.messages)
                        with open(args.messages, "r", encoding="utf-8") as file:
                            nline = 0
                            for line in file:
                                data = json.loads(line)
                                nline += 1
                                if nline <= args.skip:
                                    logging.debug("Skipping %s", nline)
                                    continue

                                logging.debug("data: %s", data)
                                identifier = data["id"]
                                messages = data["messages"]
                                if args.system_prompt:
                                    messages = add_system_message(
                                        messages, args.system_prompt
                                    )
                                run(
                                    identifier,
                                    args,
                                    repeat,
                                    temperature,
                                    top_p,
                                    messages,
                                )
                                if args.delay is not None:
                                    logging.debug("Sleeping %s ..", args.delay)
                                    time.sleep(args.delay)

                        # Skip is primarily for restarts,
                        # so only skip on the first iteration
                        args.skip = 0

                    else:
                        fatal("You must specify a prompt message.")


if __name__ == "__main__":
    main()
