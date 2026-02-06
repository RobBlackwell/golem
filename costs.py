#!/usr/bin/env python3

# Reads an answers.jsonl file and extracts information about the
# number of tokens used (where possible) and calculates the cost of
# the experiment (based on data in /etc/models.yaml

import sys
import json
from statistics import median
from pathlib import Path
import yaml


def load_pricing():
    """Load pricing data from etc/models.yaml and build lookup dictionary."""
    pricing_lookup = {}

    models_yaml = Path(__file__).parent / "etc" / "models.yaml"
    try:
        with open(models_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "models" in data:
                for model_entry in data["models"]:
                    pricing = model_entry.get("pricing", {})

                    if pricing:
                        # Add entries for all keys in "keys" field
                        for key in model_entry.get("keys", []):
                            pricing_lookup[key] = pricing
    except FileNotFoundError:
        print(
            f"Warning: {models_yaml} not found, costs will not be calculated",
            file=sys.stderr,
        )
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing {models_yaml}: {e}", file=sys.stderr)

    return pricing_lookup


def process_file(filename, pricing_lookup):
    prompt_tokens = []
    completion_tokens = []
    total_tokens = []
    input_tokens = []
    output_tokens = []
    repeats = []

    model = ""

    total_lines = 0
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                total_lines += 1
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(
                        f"Warning: Skipping malformed JSON in {filename}, line {total_lines}: {e}",
                        file=sys.stderr,
                    )
                    continue

                if "model" in data:
                    model = data["model"]

                usage = data.get("response", {}).get("usage")

                if not usage:
                    usage = data.get("response", {}).get(
                        "usageMetadata"
                    )  # Google just have to be different!

                if not usage:
                    continue  # skip this line if usage data is missing

                if "repeat" in data:
                    repeats.append(data["repeat"])

                ## OpenAI style JSON
                if "prompt_tokens" in usage:
                    prompt_tokens.append(usage["prompt_tokens"])
                if "completion_tokens" in usage:
                    completion_tokens.append(usage["completion_tokens"])
                if "total_tokens" in usage:
                    total_tokens.append(usage["total_tokens"])
                ## Anthropic style JSON
                if "input_tokens" in usage:
                    input_tokens.append(usage["input_tokens"])
                if "output_tokens" in usage:
                    output_tokens.append(usage["output_tokens"])
                ## Gemini style JSON
                if "promptTokenCount" in usage:
                    input_tokens.append(usage["promptTokenCount"])
                if "candidatesTokenCount" in usage:
                    output_tokens.append(usage["candidatesTokenCount"])

    except FileNotFoundError:
        print(f"Error: file not found: {filename}", file=sys.stderr)
        return

    p = Path(filename)

    # Calculate costs if pricing is available
    input_cost = 0.0
    output_cost = 0.0
    total_cost = 0.0

    if model in pricing_lookup:
        pricing = pricing_lookup[model]
        input_price = pricing.get("input_price", 0.0)
        output_price = pricing.get("output_price", 0.0)

        # Use input_tokens if available, otherwise use prompt_tokens
        tokens_in = sum(input_tokens) if input_tokens else sum(prompt_tokens)
        # Use output_tokens if available, otherwise use completion_tokens
        tokens_out = sum(output_tokens) if output_tokens else sum(completion_tokens)

        input_cost = (
            tokens_in * input_price / 1_000_000
        )  # Pricing is per million tokens
        output_cost = tokens_out * output_price / 1_000_000
        total_cost = input_cost + output_cost
    elif model:
        print(f"Warning: model '{model}' not found in models.yaml", file=sys.stderr)

    entry = {
        "file": str(filename),
        "label": p.parent.name,
        "experiment": p.parent.parent.name,
        "model": model,
        "prompt_tokens": sum(prompt_tokens),
        "completion_tokens": sum(completion_tokens),
        "input_tokens": sum(input_tokens),
        "total_tokens": sum(total_tokens),
        "output_tokens": sum(output_tokens),
        "repeats": len(set(repeats)),
        "lines": total_lines,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
    }

    json_line = json.dumps(entry)
    print(json_line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: costs.py answers1.jsonl [answers2.jsonl ...]", file=sys.stderr)
        sys.exit(1)

    pricing_lookup = load_pricing()

    for file in sys.argv[1:]:
        process_file(file, pricing_lookup)
