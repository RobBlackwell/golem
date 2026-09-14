"""
Claude Code support for golem.

Unlike the other providers, this one does not call an HTTP API. It runs
the `claude` command line tool as a subprocess in non-interactive
(--print) mode, so that what gets benchmarked is the whole agent,
including tool use and multiple turns, rather than a bare model.

Equivalent to:

  claude --print --model MODEL --verbose --output-format stream-json \\
      --tools "Bash,WebFetch,WebSearch" --permission-mode bypassPermissions \\
      < prompt.txt

Requires the claude CLI on PATH, see https://claude.com/claude-code
"""

# pylint: disable=too-many-arguments, too-many-locals, too-many-branches, broad-exception-caught

import json
import logging
import os
import shlex
import subprocess

from util import fatal

# Built in tools made available to the agent. Comma separated, "" for
# no tools at all, or "default" for all of them.
DEFAULT_TOOLS = "Bash,WebFetch,WebSearch"

# Benchmark runs are unattended, so permission prompts have to go. This
# lets the agent run tools without asking; run it somewhere you don't
# mind it writing to.
DEFAULT_PERMISSION_MODE = "bypassPermissions"

# Agent runs make many API calls, so they take far longer than a single
# completion.
DEFAULT_TIMEOUT = 3600


def build_prompt(messages):
    """
    Flatten golem messages into a system prompt and a user prompt.

    The claude CLI takes a single prompt on stdin, so a multi turn
    conversation is flattened into labelled blocks.
    """

    system_parts = []
    turns = []

    for message in messages:
        content = message.get("content")
        if not isinstance(content, str):
            # e.g., multimodal content, keep it rather than lose it
            content = json.dumps(content)

        if message.get("role") == "system":
            system_parts.append(content)
        else:
            turns.append((message.get("role", "user"), content))

    if len(turns) == 1:
        prompt = turns[0][1]
    else:
        prompt = "\n\n".join(f"{role}: {content}" for role, content in turns)

    return "\n\n".join(system_parts), prompt


def parse_events(stdout):
    """
    Parse the stream-json output, one JSON event per line.
    """

    events = []

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # The CLI occasionally writes non JSON chatter to stdout
            logging.warning("Ignoring non JSON output: %s", line)

    return events


def find_result(events):
    """
    Return the final result event, which carries the answer, the token
    usage and the cost.
    """

    for event in reversed(events):
        if event.get("type") == "result":
            return event

    return None


def find_model(events, model):
    """
    Report the model the CLI actually resolved, e.g., "opus" becomes
    "claude-opus-4-5-20251101".
    """

    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            if event.get("model"):
                return event["model"]

    result = find_result(events)
    if result:
        model_usage = result.get("modelUsage")
        if isinstance(model_usage, dict) and model_usage:
            return next(iter(model_usage))

    return model


def ask_claudecode(
    provider,
    model,
    url,
    key,
    messages,
    reasoning_effort,
    response_format,
):
    """
    Run a prompt through the claude command line tool.
    """

    command = [
        os.getenv("CLAUDE_CODE_PATH", "claude"),
        "--print",
        "--verbose",  # required by --output-format stream-json
        "--output-format",
        "stream-json",
        # Load no settings sources at all. Benchmark runs must not pick
        # up an ambient CLAUDE.md, from the working directory, from any
        # parent of it, or from the user's ~/.claude, because that
        # silently contaminates results and makes them irreproducible
        # on another machine. Not configurable, on purpose.
        "--setting-sources=",
        "--tools",
        os.getenv("CLAUDE_CODE_TOOLS", DEFAULT_TOOLS),
        "--permission-mode",
        os.getenv("CLAUDE_CODE_PERMISSION_MODE", DEFAULT_PERMISSION_MODE),
    ]

    if model is not None:
        command += ["--model", model]

    if reasoning_effort is not None:
        command += ["--effort", reasoning_effort]

    if response_format is not None:
        command += ["--json-schema", response_format]

    system_prompt, prompt = build_prompt(messages)

    if system_prompt:
        # Append by default, because replacing the Claude Code system
        # prompt outright tends to break the agent's tool use. Set
        # CLAUDE_CODE_SYSTEM_PROMPT_MODE=replace to override it instead.
        if os.getenv("CLAUDE_CODE_SYSTEM_PROMPT_MODE") == "replace":
            command += ["--system-prompt", system_prompt]
        else:
            command += ["--append-system-prompt", system_prompt]

    extra_args = os.getenv("CLAUDE_CODE_ARGS")
    if extra_args:
        command += shlex.split(extra_args)

    # Credentials go in the environment, never on the command line,
    # because the command line is written to the log.
    env = os.environ.copy()
    if key is not None:
        env["ANTHROPIC_API_KEY"] = key
    if url is not None:
        env["ANTHROPIC_BASE_URL"] = url

    timeout = int(os.getenv("CLAUDE_CODE_TIMEOUT", str(DEFAULT_TIMEOUT)))

    # The working directory is part of the experiment, since the agent
    # can read and write files there.
    request = {"command": command, "cwd": os.getcwd(), "stdin": prompt}

    logging.debug("subprocess: %s", request)

    completed = None
    try:
        completed = subprocess.run(
            command,
            input=prompt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        fatal(f"{command[0]} not found, is the claude CLI installed and on PATH?")
    except subprocess.TimeoutExpired:
        fatal(f"Timed out after {timeout} s, see CLAUDE_CODE_TIMEOUT. REQUEST: {request}")
    except Exception as e:
        fatal(f"EXCEPTION: {e} REQUEST: {request}")

    if completed.stderr:
        logging.debug("stderr: %s", completed.stderr)

    events = parse_events(completed.stdout)
    result = find_result(events)

    if completed.returncode != 0 or result is None:
        # Deliberately not retried. An agent run has side effects, so
        # replaying a half finished one is not safe. Restart the batch
        # with --skip instead.
        fatal(
            f"claude exited {completed.returncode} REQUEST: {request} "
            f"STDERR: {completed.stderr} STDOUT: {completed.stdout}"
        )

    if result.get("is_error"):
        fatal(f"{result.get('subtype')} REQUEST: {request} RESULT: {result}")

    answer = result.get("result")
    model = find_model(events, model)

    # The result event holds the usage and cost, the full event stream
    # is kept alongside it so the agent's tool calls stay traceable.
    response = dict(result)
    response["events"] = events

    return request, response, answer, provider, model
