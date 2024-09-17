#!/usr/bin/env python3
# Time-stamp: <2024-09-13 11:59:10 rblackwell>

"""
Process the LLM outputs to extract the answers. Clean up the
answers. Join the answers back to the original questions and save
the resulting table in summary.psv.
"""

import argparse
import json
import re

import pandas as pd


def load_jsonl(filename):
    """
    Load a JSON Lines file.
    """
    data = []
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            data.append(json.loads(line))
    return data


def load_questions(filename):
    """
    Load the questions as a Pandas data frame.
    """
    data = load_jsonl(filename)
    df = pd.DataFrame(data)
    df["id"] = df["id"].astype(str)
    return df


def load_answers(filename):
    """
    Load answers as a Pandas data frame.
    """
    data = load_jsonl(filename)
    ids = [x["id"] for x in data]
    answers = [x["answer"] for x in data]
    temperatures = [x["temperature"] for x in data]
    repeats = [x["repeat"] for x in data]
    top_ps = [x["top_p"] if "top_p" in x else None for x in data]

    df = pd.DataFrame(
        {
            "id": ids,
            "answer": answers,
            "repeat": repeats,
            "temperature": temperatures,
            "top_p": top_ps,
        }
    )
    return df


def extract_answer(text):
    """
    Extract the final answer.
    """
    pattern = r"### Answer:\s*(.*)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def str_to_set(s):
    """
    Convert a string of elements to a set.
    """
    if s is None:
        return set()

    # Insert custom clean ups here.
    s = s.upper()  # We want case insensitive
    s = re.sub(r"[\*\]\\\[\]\.]", "", s)  # spurious chars
    s = re.split(r"\s*,\s*", s.strip())
    return set(s)


def jaccard_index(x, y):
    """
    Compute the Jaccard Index (intersection over union for two sets.
    """
    print(f"x {x}, y {y}")
    i = x.intersection(y)
    u = x.union(y)
    return len(i) / len(u)


def run(question_file, answer_file, summary_file):
    """
    Combine question and answer files into a summary with marked answers.
    """

    questions = load_questions(question_file)

    if "answer" in questions.columns:
        questions = questions.rename(columns={"answer": "correctAnswer"})

    answers = load_answers(answer_file)
    df = pd.merge(questions, answers, on="id", how="inner")

    df["cleanAnswer"] = df["answer"].apply(extract_answer)

    # Remove all carriage returns (\n) and pipe symbols (|) from the 'answer' column
    df["answer"] = (
        df["answer"]
        .str.replace("\n", "", regex=False)
        .str.replace("|", "", regex=False)
    )

    df["x"] = df["cleanAnswer"].apply(str_to_set)
    df["y"] = df["correctAnswer"].apply(str_to_set)

    df["score"] = df.apply(lambda row: jaccard_index(row["x"], row["y"]), axis=1)

    print(df[["cleanAnswer", "x", "y", "score"]])

    del df["x"]
    del df["y"]

    # Use PSV because commas are common in LLM output.
    df.to_csv(summary_file, sep="|", index=False)


def main():
    """
    Entry point.
    """

    parser = argparse.ArgumentParser(description="Summarise LLM results.")
    parser.add_argument("question_file", help="The path to the question jsonl file.")
    parser.add_argument(
        "answer_file", help="The path to the answers (llm output) jsonl file."
    )

    parser.add_argument("summary_file", help="The path to save the summary PSV file.")
    args = parser.parse_args()
    run(args.question_file, args.answer_file, args.summary_file)


if __name__ == "__main__":
    main()
