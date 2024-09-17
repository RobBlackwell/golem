#!/usr/bin/env python3
"""
Apply an f-string style template to every line in a JSONL file.
"""

import argparse
import json

# pylint: disable=eval-used


def main():
    """
    Entry point.
    """
    parser = argparse.ArgumentParser(
        description="Process a template file and a JSONL file to produce formatted strings."
    )
    parser.add_argument("template_file", type=str, help="Path to the template file.")
    parser.add_argument("jsonl_file", type=str, help="Path to the JSONL file.")
    parser.add_argument(
        "--remove-line-endings",
        action="store_true",
        help="Remove line endings from the template (useful for JSONL).",
    )

    args = parser.parse_args()

    # Read the template string from the template file
    with open(args.template_file, "r", encoding="utf-8") as file:
        template_string = file.read()

        if args.remove_line_endings:
            template_string = template_string.replace("\n", "")

    # Process each line in the JSONL file
    with open(args.jsonl_file, "r", encoding="utf-8") as file:
        for line in file:
            # Convert JSON line to dictionary
            data = json.loads(line.strip())

            # Create a safe environment containing the data and datetime module
            safe_env = {"line": data}

            # Use eval to interpret the string as an f-string dynamically
            formatted_string = eval(
                f"f'''{template_string}'''", {"__builtins__": {}}, safe_env
            )

            print(formatted_string)


if __name__ == "__main__":
    main()
