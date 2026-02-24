#!/usr/bin/env python3

# Read one or more answers.jsonl files, compute inter-record timestamp
# intervals per model (ignoring non-positive deltas), and output the
# sample count and median latency (seconds) per model as JSONL.

import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime


def parse_timestamp(ts: str) -> datetime:
    ts = ts.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def compute_intervals_for_file(path: str):
    model_name = None
    previous_timestamp = None
    intervals = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            if model_name is None:
                model_name = record.get("model")

            timestamp_str = record.get("timestamp")
            if not timestamp_str:
                continue

            current_timestamp = parse_timestamp(timestamp_str)

            if previous_timestamp is not None:
                delta_seconds = (current_timestamp - previous_timestamp).total_seconds()
                if delta_seconds > 0:  # ignore out-of-order or identical timestamps
                    intervals.append(delta_seconds)

            previous_timestamp = current_timestamp

    return model_name, intervals


def main(paths):
    model_to_intervals = defaultdict(list)

    for path in paths:
        model_name, intervals = compute_intervals_for_file(path)
        if model_name:
            model_to_intervals[model_name].extend(intervals)

    for model_name in sorted(model_to_intervals):
        intervals = model_to_intervals[model_name]

        output = {
            "model": model_name,
            "samples": len(intervals),
            "median": statistics.median(intervals) if intervals else None,
        }
        print(json.dumps(output))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            f"usage: {sys.argv[0]} answers1.jsonl [answers2.jsonl ...]", file=sys.stderr
        )
        raise SystemExit(2)
    main(sys.argv[1:])
