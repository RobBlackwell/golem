#!/usr/bin/env python3

"""
Reads one or more answers.jsonl files, and extracts reasoning trace
information.
"""

from pathlib import Path
import json
import sys


def find_trace(response):
    """
    Extract a reasoning trace from a provider response, probing each
    known shape (OpenRouter/DeepSeek, legacy DeepSeek, OpenAI) in turn.
    """
    # pylint: disable=too-many-return-statements
    if not isinstance(response, dict):
        return None

    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    choice0 = choices[0] if isinstance(choices[0], dict) else None
    message = choice0.get("message") if isinstance(choice0, dict) else None
    if not isinstance(message, dict):
        return None

    # OpenRouter / DeepSeek-style (your example)
    if isinstance(message.get("reasoning"), str) and message["reasoning"].strip():
        return message["reasoning"]

    # DeepSeek legacy style
    if (
        isinstance(message.get("reasoning_content"), str)
        and message["reasoning_content"].strip()
    ):
        return message["reasoning_content"]

    # OpenAI / other style
    details = message.get("reasoning_details") or []
    if isinstance(details, list):
        for item in details:
            if not isinstance(item, dict):
                continue
            t = item.get("type")
            if t == "reasoning.summary":
                s = item.get("summary")
                if isinstance(s, str) and s.strip():
                    return s
            if t == "reasoning.text":
                txt = item.get("text")
                if isinstance(txt, str) and txt.strip():
                    return txt

    return None


def process_file(filename):
    """Read filename's answers.jsonl records and print one JSON line per reasoning trace found."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Skipping malformed JSON in {filename}: {e}",
                        file=sys.stderr,
                    )
                    continue

                record_id = None
                if "id" in data:
                    record_id = data["id"]

                model = None
                if "model" in data:
                    model = data["model"]

                answer = None
                if "answer" in data:
                    answer = data["answer"]

                repeat = None
                if "repeat" in data:
                    repeat = data["repeat"]

                response = None
                if "response" in data:
                    response = data["response"]

                trace = find_trace(response)
                if trace is not None:
                    p = Path(filename)

                    entry = {
                        "id": record_id,
                        "answer": answer,
                        "file": str(filename),
                        "label": p.parent.name,
                        "experiment": p.parent.parent.name,
                        "trace": trace,
                        "model": model,
                        "repeat": repeat,
                    }

                    json_line = json.dumps(entry)
                    print(json_line)

    except FileNotFoundError:
        print(f"Error: file not found: {filename}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: traces.py answers1.jsonl [answers2.jsonl ...]", file=sys.stderr)
        sys.exit(1)

    for file in sys.argv[1:]:
        process_file(file)
