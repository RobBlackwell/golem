# Golem

<rblackwell@turing.ac.uk>

![Golem](images/golem-small.png)

![Alpha](https://img.shields.io/badge/status-alpha-red)

## Introduction

Evaluating the capabilities of large language models (LLMs) typically
requires testing a variety of models from different vendors with
different APIs. Golem provides a simple, consistent, command line
interface to models from OpenAI, Anthropic, Google, Microsoft Azure
and Ollama.

A key problem in LLM benchmarking is that "instance by instance [LLM]
results .. are rarely made available" (Burnell et al. 2023). Golem can
be used interactively, but is primarily designed for batch mode
operation. Golem grew out of the work by Cohn and Blackwell (2024)
where we had a large number of questions that we wanted to test on
multiple LLMs. We wanted to log all LLM requests and responses in
JSONL format ensuring full traceability of prompts, models, timestamps
and results.

Golem is alpha quality software and a work in progress; I support it
on a reasonable endeavours basis. Pull requests and user feedback are
welcome.

## Installation

Golem is written in Python and designed to work best in a Unix command
line environment, for example Linux, Mac OS, or [Windows Subsystem for
Linux](https://techcommunity.microsoft.com/t5/windows-11/how-to-install-the-linux-windows-subsystem-in-windows-11/m-p/2701207). You
can probably use it from within a Windows Command prompt, but Windows
command prompts are rarely a happy experience. These instructions
assume that you already have a working system with
[Python](https://www.python.org/about/gettingstarted/) (version 3.8
or better) and [Git](https://git-scm.com) installed. You may also
wish to install [./jq](https://jqlang.github.io/jq/), a lightweight
and flexible command-line JSON processor.

1. **Clone the repository**

First, clone the repository to your local machine using git:

``` bash
git clone https://github.com/RobBlackwell/golem.git
cd golem
```

2. **Install dependencies and the package**

Golem uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management:

``` bash
uv pip install -e .
```

Alternatively, you can use the traditional pip:

``` bash
pip install -e .
```

5. **Run the golem tool**

Now that the software is installed, you can test the command line tool by running:

``` bash
golem -h
```

## Configuration

Golem supports a range of APIs and models, but you typically need to
register with an API provider to obtain access credentials.

### OpenAI

Having registered with OpenAI you can either specify your key as part
of the command line, e.g.:

``` bash
golem --provider openai --key "YOUR-KEY-HERE" "Why is the sky blue?"
```

If no key is provided, Golem will look for a shell variable called
OPENAI_API_KEY. In bash you can set this as follows:

``` bash
export OPENAI_API_KEY="YOUR-KEY-HERE"
golem --provider openai "Why is the sky blue?"
```

### Azure OpenAI

Having registered with Azure and deployed a model as part of the Azure
OpenAI API service, you should have an endpoint and a key. These can
be specified with the `--url` and `--key` command line arguments
respectively, or you can set the corresponding shell variables
AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.

### Azure AI

Having deployed an Azure AI model, you should have an endpoint and a
key.  These can be specified with the `--url` and `--key` command line
arguments respectively, or you can set the corresponding shell
variables AZUREAI_ENDPOINT_URL and AZUREAI_ENDPOINT_KEY.

### OpenRouter

Having registered with OpenRouter, you can either specify your key as part of the command line, e.g.:

``` bash
golem --provider openrouter --key "YOUR-KEY-HERE" "Why is the sky blue?"
```

The default model for OpenRouter is set to `meta-llama/llama-3.3-8b-instruct:free` because it's free!

If no key is provided, Golem will look for a shell variable called
OPENROUTER_API_KEY. In bash you can set this as follows:
``` bash
export OPENROUTER_API_KEY="YOUR-KEY-HERE"
golem --provider openrouter "Why is the sky blue?"
```

### Google Vertex

For Google Vertex you need install the `gcloud` client because Golem
uses `gcloud auth print-access-token` to obtain credentials.

You must also set CLOUDSDK_COMPUTE_REGION to the cloud region you are
using (perhaps "europe-west2" for London) and CLOUDSDK_CORE_PROJECT to
the name of your gcloud project.

### ollama

Assuming you have a running Ollama instance on your local machine
(instructions [here](https://github.com/ollama/ollama)) on port 11434
(the default), then ollama should just work with golem, e.g.:

``` bash
golem --provider ollama --model llama3 "Why is the sky blue?"
```

However, you can override the endpoint by setting `--url` explicitly if your ollama is running on a different port or URL.

## Examples

Here is a simple example:

``` bash
% golem "What is one plus plus?"
{"id": 1, "provider": "ollama", "model": "llama3", "timestamp": "2024-09-16T12:49:45.171742+00:00", "request": {"url": "http://localhost:11434/api/chat", "headers": {}, "json": {"model": "llama3", "messages": [{"role": "user", "content": "What is one plus plus?"}], "stream": false, "options": {}}}, "response": {"model": "llama3", "created_at": "2024-09-16T12:49:45.170587Z", "message": {"role": "assistant", "content": "A clever question!\n\nIn mathematics, \"one plus\" can be written as 1+. This is often used as a shorthand to represent the expression \"one plus some quantity\", where the quantity is implied but not explicitly stated.\n\nSo, in this case, \"one plus plus\" would mean... (drumroll please)... 2!"}, "done_reason": "stop", "done": true, "total_duration": 2436901916, "load_duration": 19158375, "prompt_eval_count": 16, "prompt_eval_duration": 353868000, "eval_count": 69, "eval_duration": 2063010000}, "answer": "A clever question!\n\nIn mathematics, \"one plus\" can be written as 1+. This is often used as a shorthand to represent the expression \"one plus some quantity\", where the quantity is implied but not explicitly stated.\n\nSo, in this case, \"one plus plus\" would mean... (drumroll please)... 2!", "repeat": 0}
```

Note that no provider or model was specified and so Golem has selected
ollama and llama3 respectively as defaults.

There is quite a lot of information here, including timestamp and
model specific outputs. Because each model has its own formats, Golem
always includes a copy of the answer under the "answer:" key, so that
the output is compatible whatever the model. If you just want the
answer then you can `jq` to query the output like this:

``` bash
% golem "What is one plus two?" | jq -r .answer
One plus two is... 3!
```

It's useful to pipe the output to a JSONL file

``` bash
% golem "What is one plus three?" > answers.jsonl
```

You can then query the results.jsonl using jq, for example, to find timestamps.

``` bash
jq .timestamp answerss.jsonl
"2024-09-16T13:02:28.968544+00:00"
```
### Reading prompts from a file

So far, we have included the LLM prompt on the command line, but a
more typical use case is to take a list of prompts from a jsonl file
and record the results in another jsonl:

```
golem --provider openai -f prompts.jsonl > answers.jsonl
```

The prompts.jsonl file is expected to have id and messages fields, e.g.:

``` bash
{"id": "1", "messages": [{"role": "user", "content": "If a storm is moving from north to south and you are facing the storm, which directions are you facing?"}]}
{"id": "2", "messages": [{"role": "user", "content": "If you are watching the sun rise, which direction are you facing?"}]}
```

A more comprehensive example based on these kinds of questions is included in the example directory.

### Repeats

Suppose you want to repeat an experiment ten times to assess variability:

```
~/git/golem/golem.py --provider azure --model gpt-35-turbo-0125 --repeat "0:10"  -f prompts.jsonl > answers.jsonl
```

### Varying temperature

Suppose you want to vary `temperature` from 0.0 to 1.0 in steps of 0.2.

```
~/git/golem/golem.py --provider azure --model gpt-35-turbo-0125 --temperature "0.0:1.1:0.2" > answers.jsonl
```

You can also vary `top_p` similarly and combine these options with
`repeat`.

### Getting help

Additional help and documentation can be found by typing:

``` bash
golem -h
```

### Bugs

If you encounter a bug, please report it as a GitHub issue. It can be useful to include detailed
debugging information by using the verbose flag, e.g.:

``` bash
golem -v "Why is the sky blue"
```

## FAQ

### Why Golem ?

[A Golem](https://en.wikipedia.org/wiki/Golem) is an artificial human
being described in Hebrew folklore and endowed with life. The word is
often used to mean an automaton.

### Why JSONL?

The JSON Lines format is convenient to work with in data science
languages such as R, Python and Julia.

[./jq](https://jqlang.github.io/jq/) is a lightweight and flexible
command-line JSON processor. `jq` makes it easy to inspect and query
files at the command line.

JSONL files are easily editable using text editors.

### How can I keep my credentials private?

You can keep all your credentials in a `token.sh` file in a private
directory and just consult it before using golem by typing `source
~/tokens.sh`.

Note that any and all credentials are marked as REDACTED in the log,
making it safe to share outputs.

## Related work

You might also consider using
[prompto](https://github.com/alan-turing-institute/prompto) which has
asynchronous querying and is supported by the Alan Turing Institute
Research Engineering team. Prompto's design philosophy is more
Pythonic and pipeline oriented, whilst Golem is designed to play well
with the Unix shell and the [jq](https://jqlang.github.io/jq/) JSON
processor. Golem uses HTTP REST APIs directly rather than Python
libraries. Golem is easier to hack on and trace for one-off
experiments.

## Referencing this work

Blackwell, R.E. and Cohn, A.G., 2024. Golem - a command line interface
for benchmarking Large Language Models. Zenodo,
https://doi.org/10.5281/zenodo.14035711 .

## References

Burnell, R., et al., 2023. Rethink reporting of evaluation results in
AI. Science, 380(6641),
pp.136-138.(https://doi.org/10.1126/science.adf6369)

Blackwell, R.E., Barry, J. and Cohn, A.G., 2024. Towards Reproducible
LLM Evaluation: Quantifying Uncertainty in LLM Benchmark Scores. arXiv
preprint https://arxiv.org/abs/2410.03492

Cohn, A.G. and Blackwell, R.E., 2024. Evaluating the Ability of Large
Language Models to Reason About Cardinal Directions (Short Paper). In
16th International Conference on Spatial Information Theory (COSIT
2024). Schloss Dagstuhl–Leibniz-Zentrum für
Informatik. (https://doi.org/10.4230/LIPIcs.COSIT.2024.28).
